import streamlit as st
from openai import OpenAI
import openai
import json
import os
import base64
import tiktoken
import PyPDF2
import docx
import io
import pygments
from pygments import lexers
from pygments.util import ClassNotFound

DB_FILE = 'db.json'
models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

# Define token limits for different models
MODEL_LIMITS = {
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 4096
}

# Define supported file extensions and their descriptions
SUPPORTED_FILES = {
    'txt': 'Text files',
    'pdf': 'PDF documents',
    'docx': 'Word documents',
    'py': 'Python source code',
    'java': 'Java source code',
    'cpp': 'C++ source code',
    'c': 'C source code',
    'js': 'JavaScript source code',
    'ts': 'TypeScript source code',
    'html': 'HTML files',
    'css': 'CSS files',
    'json': 'JSON files',
    'xml': 'XML files',
    'yaml': 'YAML files',
    'sql': 'SQL files',
    'r': 'R source code',
    'swift': 'Swift source code',
    'kt': 'Kotlin source code',
    'go': 'Go source code',
    'rs': 'Rust source code'
}

def validate_api_key(api_key, model):
    openai.api_key = api_key
    try:
        openai_models = openai.models.list()
        openai_model_ids = [m.id for m in openai_models.data]
        if model in openai_model_ids:
            return True, f"The API key is valid for the model: {model}."
        else:
            return False, f"The API key is valid, but the model '{model}' is not available."
    except Exception as e:
        return False, e.body['message']


def detect_programming_language(file_name, content):
    """Detect programming language from file extension and content."""
    try:
        # Try to guess lexer from content
        lexer = lexers.guess_lexer(content)
        return lexer.name
    except ClassNotFound:
        # Fall back to file extension
        try:
            extension = file_name.split('.')[-1].lower()
            lexer = lexers.get_lexer_for_filename(file_name)
            return lexer.name
        except ClassNotFound:
            return "Plain Text"

def process_code_file(content, file_name):
    """Process code file with syntax detection and formatting."""
    try:
        # Detect programming language
        language = detect_programming_language(file_name, content)
        
        # Format the code content with metadata
        formatted_content = f"""
Language: {language}
File: {file_name}

Source Code:
{content}
"""
        return formatted_content, language
    except Exception as e:
        raise Exception(f"Error processing code file: {str(e)}")

def convert_pdf_to_text(file_content):
    """Convert PDF content to text."""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error converting PDF: {str(e)}")

def convert_docx_to_text(file_content):
    """Convert DOCX content to text."""
    try:
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error converting DOCX: {str(e)}")

def count_tokens(text, model="gpt-3.5-turbo"):
    """Count the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def validate_file_size(file_content, model):
    """Validate if the file content meets the token limit requirements."""
    try:
        token_count = count_tokens(file_content, model)
        max_tokens = MODEL_LIMITS.get(model, 4096)
        reserved_tokens = 1000
        available_tokens = max_tokens - reserved_tokens
        
        if token_count > available_tokens:
            return False, f"File is too large: {token_count} tokens (limit: {available_tokens} tokens)", token_count
        
        return True, f"File size OK: {token_count} tokens", token_count
    except Exception as e:
        return False, f"Error counting tokens: {str(e)}", 0

def process_uploaded_file(uploaded_file, model):
    """Process uploaded file with support for multiple file types."""
    if uploaded_file is not None:
        try:
            # Read file content
            file_content = uploaded_file.read()
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Process different file types
            if file_extension in ['py', 'java', 'cpp', 'c', 'js', 'ts', 'html', 'css', 'json', 
                                'xml', 'yaml', 'sql', 'r', 'swift', 'kt', 'go', 'rs']:
                text_content, language = process_code_file(file_content.decode('utf-8'), uploaded_file.name)
            elif file_extension == 'pdf':
                text_content = convert_pdf_to_text(file_content)
                language = 'PDF'
            elif file_extension == 'docx':
                text_content = convert_docx_to_text(file_content)
                language = 'DOCX'
            elif file_extension == 'txt':
                text_content = file_content.decode('utf-8')
                language = 'Plain Text'
            else:
                return None, f"Unsupported file type: {file_extension}"
            
            # Validate file size
            is_valid, message, token_count = validate_file_size(text_content, model)
            if not is_valid:
                return None, message
            
            return {
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "content": text_content,
                "language": language,
                "size": uploaded_file.size,
                "tokens": token_count
            }, "File processed successfully"
        except Exception as e:
            return None, f"Error processing file: {str(e)}"
    return None, "No file uploaded"

def main():
    client = OpenAI(api_key=st.session_state.openai_api_key)

    # Create a select box for the models
    st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)

    # Show token limit for selected model
    selected_model_limit = MODEL_LIMITS.get(st.session_state["openai_model"], 4096)
    st.sidebar.info(f"Selected model token limit: {selected_model_limit}")

    # Add file upload widget in sidebar with expanded file type support
    uploaded_file = st.sidebar.file_uploader(
        "Upload a file", 
        type=list(SUPPORTED_FILES.keys()),
        help="Supported formats: " + ", ".join(f"{ext} ({desc})" for ext, desc in SUPPORTED_FILES.items())
    )
    
    # Process uploaded file
    file_info = None
    if uploaded_file:
        with st.spinner("Processing file..."):
            file_info = {}
            with open(DB_FILE, 'r') as file:
                db = json.load(file)
                if f"{st.session_state.openai_api_key}_files" in db.get('openai_api_keys'):
                    if uploaded_file.name in db.get('openai_api_keys')[f"{st.session_state.openai_api_key}_files"]:
                        file_info = db.get('openai_api_keys')[f"{st.session_state.openai_api_key}_files"][uploaded_file.name]
                    else:
                        file_info, message = process_uploaded_file(uploaded_file, st.session_state["openai_model"])
                        if file_info:
                            db.get('openai_api_keys')[f"{st.session_state.openai_api_key}_files"][uploaded_file.name] = file_info
                else:
                    file_info, message = process_uploaded_file(uploaded_file, st.session_state["openai_model"])
                    if file_info:
                        db.get('openai_api_keys')[f"{st.session_state.openai_api_key}_files"] = {uploaded_file.name: file_info}
                    
                if file_info:
                    st.sidebar.success(f"""
                        File uploaded: {uploaded_file.name}
                        Tokens: {file_info['tokens']}
                        Type: {uploaded_file.type}
                    """)
                    with open(DB_FILE, 'w') as file:
                        json.dump(db, file)
                    uploaded_file = None
                else:
                    st.sidebar.error(message)

    # Load chat history from db.json
    with open(DB_FILE, 'r') as file:
        db = json.load(file)
    st.session_state.messages = db.get('openai_api_keys')[st.session_state.openai_api_key]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Check prompt token count
        prompt_tokens = count_tokens(prompt, st.session_state["openai_model"])
        
        # Prepare the message with file content if available
        user_message = prompt
        if file_info:
            user_message = f"""
Question: {prompt}

Attached file information:
Filename: {file_info['name']}
Content:
{file_info['content']}
"""
        
        # Check total tokens
        total_tokens = count_tokens(user_message, st.session_state["openai_model"])
        max_tokens = MODEL_LIMITS.get(st.session_state["openai_model"], 4096)
        
        if total_tokens > max_tokens - 1000:  # Reserve 1000 tokens for response
            st.error(f"Total input too large: {total_tokens} tokens (limit: {max_tokens - 1000} tokens)")
            return

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_message})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)  # Show original prompt without file content for cleaner UI

        # Display assistant response in chat message container
        try:
            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)            
            st.session_state.messages.append({"role": "assistant", "content": response})
            db.get('openai_api_keys')[st.session_state.openai_api_key] = st.session_state.messages
            with open(DB_FILE, 'w') as file:
                json.dump(db, file)
        except Exception as e:
            error_message = getattr(e, 'body', {}).get('message', str(e))
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            db.get('openai_api_keys')[st.session_state.openai_api_key] = st.session_state.messages
            with open(DB_FILE, 'w') as file:
                json.dump(db, file)
            st.error(f"An error occurred: {error_message}")

    # Add a "Clear Chat" button to the sidebar
    if st.sidebar.button('Clear Chat'):
        # Clear chat history in db.json
        db.get('openai_api_keys')[st.session_state.openai_api_key] = []
        db.get('openai_api_keys')[f"{st.session_state.openai_api_key}_files"] = {}
        with open(DB_FILE, 'w') as file:
            json.dump(db, file)
        # Clear chat messages in session state
        st.session_state.messages = []
        st.rerun()

if __name__ == '__main__':
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        main()
    else:
        # if the DB_FILE not exists, create it
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w') as file:
                db = {
                    'openai_api_keys': {},
                }
                json.dump(db, file)
        # load the database
        else:
            with open(DB_FILE, 'r') as file:
                db = json.load(file)

        # a text input box for entering a new key
        new_key = st.text_input(
            label="Your OpenAI API Key", 
            type="password"
        )

        login = st.button("Login")

        if login:
            if new_key:
                st.session_state["openai_model"] = st.sidebar.selectbox("Select OpenAI model", models, index=0)      
                valid, message = validate_api_key(new_key, st.session_state["openai_model"])          
                if valid:
                    db = None
                    with open(DB_FILE, 'r') as file:
                        db = json.load(file)
                    if 'openai_api_keys' not in db:
                        db['openai_api_keys'] = {}
                    else:
                        if new_key in db['openai_api_keys']:
                            st.session_state.messages = db['openai_api_keys'][new_key]
                        else:
                            db['openai_api_keys'][new_key] = []

                    with open(DB_FILE, 'w') as file:
                        json.dump(db, file)
                    st.success("Key saved successfully.")
                    st.session_state['openai_api_key'] = new_key
                    st.rerun()
                else:
                    st.error(message)
