import logging
from io import BytesIO
from pypdf import PdfReader
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import base64

# Load environment variables from .env
load_dotenv()

# Retrieve the API key from the environment
api_key = os.getenv('GOOGLE_API_KEY')

# Check if the API key is loaded correctly
if not api_key:
    raise ValueError("API Key not found. Please set it in the .env file.")
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()
# Configure the Generative AI client with the API key
genai.configure(api_key=api_key)
title_ai = get_image_base64("./Assert/full-logo-apex.png")

def generate_response(model, question, context):
    """Generate a response from the LLM based on the question and context provided."""
    try:
        response = model.generate_content([question, context])
        return response.text
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "Sorry, there was an error generating a response."

def setup_chat_page():
    """Set up the chat interface for PDF."""
    # st.set_page_config(page_title="Apex AI Chat", layout="wide")

    # Display the logo image at the top instead of a text title
    st.markdown("""
    <style>
    .stApp {
        background-color: black;
    }
    .css-1d391kg {
        padding-top: 3rem;
    }
    .centered-image {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    
    /* Styling for the chat input field */
    div[data-baseweb="input"] > div {
        background-color: white;
        border: 2px solid red !important;  /* Red border */
        border-radius: 8px;
        padding: 5px;
        box-shadow: 0px 0px 5px rgba(255, 0, 0, 0.5); /* Optional red shadow */
    }
    
    input[type="text"] {
        color: black;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display the image (logo) centered
    st.markdown(f"""
    <div class="centered-image">
        <img src='data:image/png;base64,{title_ai}' style='width: 300px;'>
    </div>
    """, unsafe_allow_html=True)




def display_message(message, role):
    """Display a message in the chat with appropriate alignment and icons."""
    user_image = get_image_base64("./Assert/sathish-p.webp")
    bot_image = get_image_base64("./Assert/only-logo-apex.png")
    
    if role == "user":
        st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 15px;'>
                <div style='background-color: #e6f3ff; color: #333; padding: 15px; border-radius: 15px; max-width: 70%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>
                    <p style='margin: 0;'>{message}</p>
                </div>
                <img src='data:image/png;base64,{user_image}' style='width: 50px; height: 50px; border-radius: 50%; margin-left: 10px;'>
            </div>
        """, unsafe_allow_html=True)
    elif role == "assistant":
        st.markdown(f"""
            <div style='display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 15px;'>
                <img src='data:image/png;base64,{bot_image}' style='width: 50px; height: 50px; border-radius: 20%; margin-right: 10px;'>
                <div style='background-color: #f0f0f0; color: #333; padding: 15px; border-radius: 15px; max-width: 50%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>
                    <p style='margin: 0;'>{message}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

def chat_with_pdf(uploaded_file):
    """Main chat function for PDF interaction."""
    setup_chat_page()

    # Default model and generation parameters
    model_name = "gemini-1.5-flash"
    temperature = 0.7
    top_p = 0.95
    max_tokens = 2000

    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_tokens,
    }

    model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        default_message = "Hi! I'm Apex Bot. How can I assist you today?"
        st.session_state.messages.append({"role": "assistant", "content": default_message})

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        display_message(message["content"], message["role"])

    # Sticky upload button with improved styling


    # Custom upload button for PDF file with drag-and-drop functionality
    with st.container():
        st.markdown('<div class="sticky-upload">', unsafe_allow_html=True)
        # uploaded_file = st.file_uploader("Upload your PDF file", type='pdf', label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    # Company profile to be used when no file is uploaded
    default_context = """
    Company Profile:
    Since its inception in 1978, Apex Laboratories has been led by Mr. S.S. Vanangamudi. A pioneer in Zinc-based formulations, Apex is a leader in the Multivitamin Mineral Supplements segment. 
    Apex has grown into a company with over 3000 employees, state-of-the-art manufacturing, and a robust distribution network. Apex is ranked among the top 50 pharmaceutical companies in India, 
    with strong growth and innovative product development for both domestic and global markets.

    your Role :Your expert in Helpdesk Bot your working in Apex Labs
    """

    # Accept user input
    prompt = st.chat_input("Type your question here...")
    
    if prompt:
        context = default_context
        if uploaded_file is not None:
            with st.spinner("Processing your PDF..."):
                pdf_reader = PdfReader(uploaded_file)
                context = "".join(page.extract_text() for page in pdf_reader.pages)

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message(prompt, "user")

        default_prompt = """As an expert in analyzing monthly sales reports, you excel at reviewing key details such as company names, chemist names, and product information. You are adept at interpreting financial metrics like product value, batch numbers, and sales figures, ensuring a clear understanding of the data. Your keen eye tracks bill numbers, bill dates, and ensures proper alignment with city and pincode information for accurate regional analysis. You specialize in identifying trends and patterns, helping businesses pinpoint areas for growth or improvement. By focusing on data clarity, you present complex information in a straightforward manner. Your ability to provide short, crisp summaries helps decision-makers quickly grasp key insights. Ultimately, you bring a structured, analytical approach to organizing and interpreting sales data for maximum business impact. Output must be 4 lines"""
        
        question = f"Question: {prompt}"

        # Generate response from the assistant
        response_text = generate_response(model, default_prompt + question, context)
        
        # Display the full response
        display_message(response_text, "assistant")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_text})

if __name__ == '__main__':
    chat_with_pdf(uploaded_file=None)