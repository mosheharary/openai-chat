# OpenAI Chat Interface

A Streamlit application that provides a chat interface for interacting with OpenAI chat models.

## Features

- 🔑 Secure API key input
- 🤖 Support for multiple OpenAI models (GPT-4, GPT-3.5, etc.)
- 💬 Full conversation history
- 🗑️ Clear messages button
- 📝 Markdown formatting for regular text
- 💻 Code formatting for code blocks
- 📊 Token usage tracking and cost calculation
- 💰 Running total of session costs

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

3. Open your browser and navigate to the provided URL (usually http://localhost:8501)

4. Enter your OpenAI API key in the sidebar

5. Select your preferred model from the dropdown

6. Start chatting!

## Usage

1. **API Key**: Securely enter your OpenAI API key in the sidebar. This is required to use the application.

2. **Model Selection**: Choose from a list of available OpenAI models (GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-4, GPT-3.5-turbo).

3. **Chat Interface**: Type your messages in the input box at the bottom of the chat interface. The assistant will respond with properly formatted text and code.

4. **Clear Messages**: Use the "Clear Messages" button in the sidebar to reset the conversation history.

## Notes

- The application sends the entire conversation history with each request to maintain context.
- Code blocks are automatically detected and formatted with syntax highlighting.
- Markdown formatting is supported for regular text responses.
- Token usage is calculated using tiktoken for accurate counts.
- Cost calculations are based on OpenAI's current pricing (as of 2024).
- The total session cost is displayed in the sidebar and updated with each query.
