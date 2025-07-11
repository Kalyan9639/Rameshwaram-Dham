import easyocr
from fastapi import FastAPI, Form, HTTPException # Import Form for form data, HTTPException for errors
from fastapi.responses import JSONResponse # To return structured JSON responses
import os # To check if the file path exists
from langchain_community.llms import ollama # Import Ollama for LLM invocation

app = FastAPI()


# --- EasyOCR Reader Caching ---
# Initialize EasyOCR reader once when the app starts, and cache for performance.
# This prevents reloading the model for every request.
reader_cache = {}

def get_easyocr_reader(lang_code: str):
    """
    Retrieves or creates an EasyOCR reader for the given language code.
    Caches readers for performance.
    """
    if lang_code not in reader_cache:
        # EasyOCR reader expects a list of language codes
        print(f"Initializing EasyOCR reader for language: {lang_code}...") # Debug print
        reader_cache[lang_code] = easyocr.Reader([lang_code])
        print(f"Reader for {lang_code} initialized.") # Debug print
    return reader_cache[lang_code]

# --- FastAPI Endpoint (CORRECTED) ---
@app.post("/") # Endpoint matches the frontend's FASTAPI_URL = "http://127.0.0.1:8000/"
async def get_description(
    image_path: str = Form(..., description="The path to the image file on the server."),
    lang_code: str = Form(..., description="The two-letter language code (e.g., 'en', 'hi', 'fr').")
):
    """
    Receives an image path and a language code, performs OCR, and generates an AI description.
    NOTE: This endpoint assumes the image path is accessible on the FastAPI server's filesystem.
    """
    try:
        # 1. Verify the path exists and is a file
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail=f"Image file not found at path: {image_path}. Ensure both frontend and backend share the same file system for the image_cache folder.")
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=400, detail=f"The provided path is not a valid file: {image_path}")

        # 2. Get the EasyOCR reader for the specified language
        reader = get_easyocr_reader(lang_code)

        # 3. Perform OCR directly from the file path
        print(f"Performing OCR on image from path: {image_path} with language: {lang_code}...") # Debug print
        results = reader.readtext(image_path, detail=0) # EasyOCR can read from a path directly
        print(f"OCR results: {results}") # Debug print

        # 4. Convert the list of results to a single string for the LLM
        extracted_text = " ".join(results)
        if not extracted_text.strip():
            extracted_text = "No discernible text found in the image."
            print("No text extracted by OCR.") # Debug print

        # 5. Initialize and invoke the Ollama LLM
        print("Invoking Ollama LLM...") # Debug print
        llm = ollama.Ollama(model="llama3.2") # Ensure 'llama3.2' is available in your Ollama setup
        
        description = llm.invoke(f"""
        I am going to give you a list of text extracted from an image using easyocr. By keeping in mind, the potential inaccuracies or fragmented nature of text extracted by OCR, create a coherent, full description of the image based on this text.
        
        Assume all the text collectively pertains to a similar category or theme within the image. Your task is to synthesize this information into an effective, descriptive summary of the image in 5 sentences.
        
        Do not include any additional introductory or concluding remarks, just the description.
        
        Here is the text extracted from the image:
        ---
        {extracted_text}
        ---
        """)
        print("LLM description generated.") # Debug print

        # 6. Return the description as a JSON response
        return JSONResponse(content={"description": description})

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        print(f"Error during processing: {e}") # Debug print
        raise HTTPException(status_code=500, detail=f"An error occurred during image processing or LLM generation: {e}")