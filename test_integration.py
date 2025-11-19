import requests
import os

def test_integration():
    url = 'http://127.0.0.1:5000/api/generate'
    
    # Create dummy files if they don't exist
    if not os.path.exists('dummy_seed.png'):
        print("Please run create_dummy.py first")
        return

    files = {
        'seed_image': ('dummy_seed.png', open('dummy_seed.png', 'rb'), 'image/png')
    }
    
    data = {
        'api_key': 'dummy_key', # This will fail at Gemini API level, but should pass Flask validation
        'model_name': 'gemini-2.5-flash-image',
        'prompt': 'Test prompt',
        'mode': 'variation'
    }
    
    print("Sending request to local server...")
    try:
        response = requests.post(url, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success! Received image response.")
        elif response.status_code == 500:
            print("ℹ️ Server Error (Expected with dummy key):")
            print(response.text)
            # If we get a 500 error related to API key, it means the request reached the backend logic
            if "API key not valid" in response.text or "400" in response.text or "403" in response.text:
                 print("✅ Integration verified: Request reached Gemini client.")
            else:
                 print("⚠️ Unexpected error.")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_integration()
