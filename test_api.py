import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables if .env exists
load_dotenv()

def test_connection():
    api_key = input("Enter your Gemini API Key: ")
    model_name = "gemini-2.5-flash-image"
    
    print(f"Configuring API with model: {model_name}...")
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel(model_name)
        print("Model initialized successfully.")
        
        # Simple test prompt
        print("Sending test prompt...")
        response = model.generate_content("Explain what you are in one sentence.")
        print("Response received:")
        print(response.text)
        print("\n✅ API Connection Successful!")
        
    except Exception as e:
        print(f"\n❌ API Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()
