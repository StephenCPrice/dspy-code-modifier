from flask import Flask, render_template, request, jsonify
import dspy
import os
from dotenv import load_dotenv
from litellm import RateLimitError

load_dotenv()

app = Flask(__name__)

# Initialize DSPy with OpenAI
try:
    lm = dspy.LM('openai/gpt-3.5-turbo', api_key=os.getenv('OPENAI_API_KEY'))
    dspy.configure(lm=lm)
except Exception as e:
    print(f"Error initializing language model: {str(e)}")
    raise

# Define the signature for code modification
class CodeModifier(dspy.Signature):
    """Signature for modifying code based on instructions."""
    instruction = dspy.InputField(desc="The instruction for modifying the code")
    code = dspy.InputField(desc="The original code content")
    modified_code = dspy.OutputField(desc="The modified code based on the instruction")

# Create a ChainOfThought module
code_modifier = dspy.ChainOfThought(CodeModifier)

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
        # Use DSPy to modify the code
        result = code_modifier(instruction=instruction, code=code)
        return jsonify({'modified_code': result.modified_code})
    except RateLimitError as e:
        return jsonify({
            'error': 'OpenAI API rate limit exceeded. Please check your API key quota and billing status.',
            'details': str(e)
        }), 429
    except Exception as e:
        return jsonify({
            'error': 'An error occurred while processing your request',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080) 