from flask import Flask, render_template, request, jsonify
import dspy
import os
from dotenv import load_dotenv
from litellm import RateLimitError
import difflib
import traceback
import json

load_dotenv()

app = Flask(__name__)

# Initialize DSPy with OpenAI
try:
    lm = dspy.LM('openai/gpt-3.5-turbo', api_key=os.getenv('OPENAI_API_KEY'))
    dspy.configure(lm=lm)
except Exception as e:
    print(f"Error initializing language model: {str(e)}")
    raise

class CodeChange:
    def __init__(self, start_line, end_line, new_content):
        self.start_line = start_line  # 1-based line number
        self.end_line = end_line      # 1-based line number
        self.new_content = new_content

class CodeModifier(dspy.Signature):
    """Signature for identifying and describing specific code changes."""
    instruction = dspy.InputField(desc="The instruction for modifying the code")
    code = dspy.InputField(desc="The original code content")
    changes = dspy.OutputField(desc="A list of changes in the format: [{'start_line': int, 'end_line': int, 'new_content': str}, ...]")
    explanation = dspy.OutputField(desc="Brief explanation of the changes made")

def apply_changes(original_code: str, changes: list) -> str:
    """Apply a list of changes to the original code intelligently."""
    try:
        # Convert code to lines for easier manipulation
        lines = original_code.splitlines()
        
        # Sort changes by start line in reverse order (to apply from bottom to top)
        sorted_changes = sorted(changes, key=lambda x: x['start_line'], reverse=True)
        
        for change in sorted_changes:
            start = change['start_line'] - 1  # Convert to 0-based index
            end = change['end_line'] - 1      # Convert to 0-based index
            new_content = change['new_content'].splitlines()
            
            # Validate indices
            if start < 0 or end >= len(lines):
                raise ValueError(f"Invalid line numbers: start={start+1}, end={end+1}, total_lines={len(lines)}")
            
            # Replace the specified lines with new content
            lines[start:end + 1] = new_content
        
        return '\n'.join(lines)
    except Exception as e:
        print(f"Error in apply_changes: {str(e)}")
        print(f"Changes object: {changes}")
        raise

# Create a more specific ChainOfThought module with temperature control
code_modifier = dspy.ChainOfThought(CodeModifier)
dspy.settings.configure(temperature=0.3)  # Lower temperature for more consistent outputs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/modify-code', methods=['POST'])
def modify_code():
    data = request.json
    instruction = data.get('instruction')
    code = data.get('code_content')
    
    if not instruction or not code:
        return jsonify({'error': 'Missing instruction or code'}), 400
    
    try:
        # Use DSPy to get the changes
        print(f"\nProcessing instruction: {instruction}")
        print(f"Input code:\n{code}\n")
        
        result = code_modifier(instruction=instruction, code=code)
        print(f"\nRaw DSPy result: {result}")
        print(f"Result dict: {result.__dict__}")
        print(f"Changes type: {type(result.changes)}")
        print(f"Changes content: {result.changes}")
        
        # Handle changes that might come as a string
        changes = result.changes
        if isinstance(changes, str):
            try:
                changes = eval(changes)  # Safe here since we control the input from DSPy
            except Exception as e:
                return jsonify({
                    'error': 'Could not parse changes',
                    'details': f'Error parsing changes: {str(e)}'
                }), 500
        
        if changes is None:
            return jsonify({
                'error': 'No changes returned',
                'details': 'DSPy model did not return any changes'
            }), 500
            
        if not isinstance(changes, list):
            return jsonify({
                'error': 'Invalid response format',
                'details': f'Expected list of changes, got {type(changes)}'
            }), 500
            
        # Validate change format
        for i, change in enumerate(changes):
            print(f"\nValidating change {i}:")
            print(f"Change content: {change}")
            if not isinstance(change, dict):
                return jsonify({
                    'error': 'Invalid change format',
                    'details': f'Change {i} is not a dictionary: {change}'
                }), 500
            if not all(k in change for k in ['start_line', 'end_line', 'new_content']):
                return jsonify({
                    'error': 'Invalid change format',
                    'details': f'Change {i} missing required fields: {change}'
                }), 500
        
        # Apply the changes to the original code
        modified_code = apply_changes(code, changes)
        
        # Generate a diff for visualization
        diff = list(difflib.unified_diff(
            code.splitlines(keepends=True),
            modified_code.splitlines(keepends=True),
            fromfile='Original',
            tofile='Modified'
        ))
        
        return jsonify({
            'modified_code': modified_code,
            'changes': changes,
            'explanation': result.explanation,
            'diff': ''.join(diff)
        })
    except RateLimitError as e:
        print(f"Rate limit error: {str(e)}")
        return jsonify({
            'error': 'OpenAI API rate limit exceeded. Please check your API key quota and billing status.',
            'details': str(e)
        }), 429
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'An error occurred while processing your request',
            'details': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080) 