import streamlit as st
from openai import OpenAI
import os
import tiktoken
import json

# Set page config
st.set_page_config(page_title="OpenAI Chat Interface", page_icon="🤖", layout="wide")

# Title of the application
st.title("🤖 OpenAI Chat Interface")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "model_name" not in st.session_state:
    st.session_state.model_name = "gpt-4o"

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

# Sidebar for API key and model selection
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key input
    api_key = st.text_input("Enter your OpenAI API Key", 
                           value=st.session_state.api_key, 
                           type="password")
    
    # Model selection dropdown
    model_options = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo"
    ]
    
    model_name = st.selectbox("Select Model", 
                             options=model_options, 
                             index=model_options.index(st.session_state.model_name))
    
    # Update session state
    st.session_state.api_key = api_key
    st.session_state.model_name = model_name
    
    # Clear messages button
    if st.button("🗑️ Clear Messages"):
        st.session_state.messages = []
        st.session_state.total_cost = 0.0
        st.rerun()
    
    # Show total cost
    st.markdown("---")
    st.metric("**💰 Total Session Cost**", f"${st.session_state.total_cost:.6f}")

# Function to check if OpenAI is properly configured
def is_configured():
    return bool(st.session_state.api_key)

# Function to format the message content
def format_message_content(content):
    if "```" in content:
        # Split by code blocks and render differently
        parts = content.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 0:  # This is regular text
                if part.strip():
                    st.markdown(part)
            else:  # This is code
                if '\n' in part:
                    lang_and_code = part.split('\n', 1)
                    if len(lang_and_code) == 2:
                        lang, code = lang_and_code
                        st.code(code, language=lang)
                    else:
                        st.code(part)
                else:
                    st.code(part)
    else:
        st.markdown(content)

# Function to count tokens using tiktoken
def count_tokens(messages, model="gpt-4o"):
    try:
        if model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]:
            encoding = tiktoken.encoding_for_model("gpt-4")
        else:
            encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3
    tokens_per_name = 1
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    
    num_tokens += 3  # Every reply is primed with assistant
    return num_tokens

# Main chat interface
if not is_configured():
    st.warning("⚠️ Please enter your OpenAI API key in the sidebar to start chatting.")
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            format_message_content(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to ask?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # Create OpenAI client with minimal parameters
                # Ensure no proxy parameters are passed
                os.environ.pop('HTTP_PROXY', None)
                os.environ.pop('HTTPS_PROXY', None)
                os.environ.pop('http_proxy', None)
                os.environ.pop('https_proxy', None)
                
                client = OpenAI(api_key=st.session_state.api_key, base_url=None)
                
                # Count prompt tokens
                prompt_tokens = count_tokens(st.session_state.messages, st.session_state.model_name)
                
                # Send message to OpenAI
                stream = client.chat.completions.create(
                    model=st.session_state.model_name,
                    messages=st.session_state.messages,
                    stream=True
                )
                
                # Stream the response
                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Count completion tokens
                completion_tokens = count_tokens([{"role": "assistant", "content": full_response}], st.session_state.model_name)
                total_tokens = prompt_tokens + completion_tokens
                
                # Cost calculation based on model (prices as of 2024)
                cost_per_1k_tokens = {
                    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
                    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
                    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
                    "gpt-4": {"prompt": 0.03, "completion": 0.06},
                    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015}
                }
                
                model_prices = cost_per_1k_tokens.get(st.session_state.model_name, {"prompt": 0.01, "completion": 0.03})
                prompt_cost = (prompt_tokens / 1000) * model_prices["prompt"]
                completion_cost = (completion_tokens / 1000) * model_prices["completion"]
                total_cost = prompt_cost + completion_cost
                
                # Update total session cost
                st.session_state.total_cost += total_cost
                
                # Display token usage and cost
                st.markdown("---")
                st.markdown("### 📊 Token Usage & Cost")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Prompt Tokens", prompt_tokens)
                with col2:
                    st.metric("Completion Tokens", completion_tokens)
                with col3:
                    st.metric("Total Tokens", total_tokens)
                st.metric("**💰 This Query Cost**", f"${total_cost:.6f}")
            
            except Exception as e:
                error_message = f"❌ Error: {str(e)}"
                message_placeholder.error(error_message)
                # Show diagnostic information
                st.error("If you see a proxy error, please ensure you're using the latest OpenAI library version.")
                st.code(f"Error type: {type(e).__name__}\nError message: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*Powered by OpenAI and Streamlit*")
