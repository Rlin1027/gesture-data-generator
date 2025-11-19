import requests
import os

# Use the dummy image created earlier
IMAGE_PATH = 'dummy_seed.png'
API_URL = 'http://127.0.0.1:5000/api/analyze'
API_KEY = 'dummy_key' # The backend will try to use this, it will fail at Gemini API call but we can check if endpoint is reachable

def test_analyze_endpoint():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: {IMAGE_PATH} not found. Run create_dummy.py first.")
        return

    print(f"Testing /api/analyze with {IMAGE_PATH}...")
    
    with open(IMAGE_PATH, 'rb') as img_file:
        files = {'image': img_file}
        data = {'api_key': API_KEY}
        
        try:
            response = requests.post(API_URL, files=files, data=data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("SUCCESS: Endpoint reachable and returned 200 (Mocked or Real).")
                # Note: Since we use a dummy key, we expect the inner Gemini call to fail 
                # and return a JSON with error details in the 'issues' field or similar,
                # OR the backend might catch the exception and return 200 with error info 
                # if we handled it gracefully in analyze_image.
                # Let's check the response content.
                result = response.json()
                if "fingerCount" in result:
                    print("Structure looks correct.")
                else:
                    print("Unexpected structure.")
            else:
                print("FAILURE: Endpoint returned error.")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_analyze_endpoint()
