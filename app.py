import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import os
import uuid # To generate unique filenames

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Image to Text AI Model",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for a sleek, dark theme ---
st.markdown(
    """
    <style>
    body {
        background-color: black;
        color: white;
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: black;
        color: white;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    h1 {
        color: #00FFFF; /* Cyan for main heading */
        text-shadow: 0 0 10px #00FFFF;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 1.5em;
    }
    .stFileUploader > label {
        color: white;
        font-size: 1.2em;
    }
    .stTextInput > div > label {
        color: white;
        font-size: 1.2em;
    }
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid #00FFFF;
        border-radius: 5px;
        padding: 8px;
    }
    .stButton > button {
        background-color: #007BFF;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 1.1em;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 0 0 10px rgba(0, 123, 255, 0.7);
    }
    .stButton > button:hover {
        background-color: #0056b3;
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 123, 255, 0.9);
    }
    .stSpinner > div > div {
        border-top-color: #00FFFF !important;
    }
    .stAlert {
        background-color: rgba(255, 0, 0, 0.1);
        color: #FF6347;
        border-left: 5px solid #FF6347;
    }
    .stInfo {
        background-color: rgba(0, 255, 255, 0.1);
        color: #00FFFF;
        border-left: 5px solid #00FFFF;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }
    .stImage {
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- FastAPI Backend URL ---
# Make sure this matches your backend's endpoint path
FASTAPI_URL = "http://127.0.0.1:8000/" 

# --- Cache Directory Configuration ---
CACHE_DIR = "image_cache"
# Create the cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

st.title("Image to Text AI Model")

uploaded_file = st.file_uploader("Upload an image (JPG, PNG)", type=["jpg", "jpeg", "png"])

description = None

if uploaded_file is not None:
    # Read image bytes for preview
    image_bytes = uploaded_file.getvalue()
    image_preview = Image.open(BytesIO(image_bytes))

    # Streamlit can display PIL Image objects directly
    st.image(image_preview, caption='Image Preview', use_column_width=True)

    # Ask for language after image is uploaded
    language_code = st.text_input(
        "Enter language code of text in image (e.g., 'en' for English, 'hi' for Hindi, 'fr' for French):",
        value="en" # Default to English
    )

    if st.button("Process Image"):
        if not language_code:
            st.error("Please enter a language code before processing the image.")
        else:
            with st.spinner("Analyzing image with AI model..."):
                try:
                    # 1. Generate a unique filename for the uploaded image
                    file_extension = uploaded_file.name.split('.')[-1]
                    unique_filename = f"{uuid.uuid4()}.{file_extension}"
                    saved_image_path = os.path.join(CACHE_DIR, unique_filename)

                    # 2. Save the uploaded image bytes to the cache folder
                    with open(saved_image_path, "wb") as f:
                        f.write(image_bytes)
                    st.success(f"Image saved to cache: {saved_image_path}")

                    # 3. Prepare data to send the path and language code to FastAPI
                    data = {
                        'image_path': saved_image_path, # Send the path as a string
                        'lang_code': language_code
                    }

                    # Make the POST request to FastAPI with the path and language code
                    response = requests.post(FASTAPI_URL, data=data) 

                    # Check for successful response
                    if response.status_code == 200:
                        data = response.json()
                        description = data.get("description", "No description found.")
                    else:
                        error_detail = response.json().get("detail", "Unknown error from backend.")
                        st.error(f"Error from backend: {response.status_code} - {error_detail}")

                except requests.exceptions.ConnectionError:
                    st.error(f"Could not connect to the FastAPI backend. Please ensure FastAPI is running at {FASTAPI_URL}.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

# Display the description if available
if description:
    st.markdown("### AI Generated Description:")
    st.info(description)