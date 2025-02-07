# DSPy Code Modifier

A web application that uses DSPy and OpenAI to modify code based on natural language instructions.

## Features

- Web interface for code modification
- Powered by DSPy and OpenAI's GPT-3.5
- Real-time code modifications
- Error handling for API limits

## Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/dspy-code-modifier.git
cd dspy-code-modifier
```

2. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install
```

4. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

5. Run the application:
```bash
poetry run python app.py
```

6. Open your browser and navigate to `http://localhost:8080`

## Usage

1. Enter your modification instructions in the top text area
2. Paste your code in the middle text area
3. Click "Modify Code" to get the modified version
4. The modified code will appear in the bottom text area

## Requirements

- Python 3.12+
- Poetry for dependency management
- OpenAI API key

## License

MIT License 