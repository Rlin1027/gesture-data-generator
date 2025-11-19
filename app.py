from flask import Flask, render_template, request, jsonify, send_file
from gemini_client import GeminiClient
from utils import process_image, image_to_bytes, bytes_to_image
import io
import base64
from PIL import Image

app = Flask(__name__)

# In-memory storage for simplicity (or use temp files)
# For a real app, use a database or file system
# We won't store images permanently on server for this demo, just process and return.

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        api_key = request.form.get('api_key')
        model_name = request.form.get('model_name', 'gemini-2.5-flash-image')
        prompt = request.form.get('prompt')
        mode = request.form.get('mode') # 'variation' or 'modification'
        
        if not api_key:
            return jsonify({'error': 'API Key is required'}), 400

        client = GeminiClient(api_key=api_key, model_name=model_name)

        seed_file = request.files.get('seed_image')
        if not seed_file:
            return jsonify({'error': 'Seed image is required'}), 400
            
        seed_image = process_image(seed_file)
        if not seed_image:
            return jsonify({'error': 'Invalid seed image'}), 400

        result_image = None

        if mode == 'variation':
            # Function 1: Variation
            # result_image = client.generate_variation(seed_image, prompt)
            # Mocking response for now as we can't actually call the API without a key
            # In real scenario:
            try:
                result_image = client.generate_variation(seed_image, prompt)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        elif mode == 'modification':
            # Function 2: Modification
            ref_file = request.files.get('reference_image')
            if not ref_file:
                return jsonify({'error': 'Reference image is required for modification'}), 400
            
            ref_image = process_image(ref_file)
            try:
                result_image = client.modify_gesture(seed_image, ref_image, prompt)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        else:
            return jsonify({'error': 'Invalid mode'}), 400

        # Handle the result
        # If result_image is a PIL Image, return it
        # If it's a response object, we might need to extract the image
        # For this template, let's assume we get a PIL Image back or we handle it here.
        # If the API call fails or returns text, we need to handle that.
        
        if isinstance(result_image, Image.Image):
            # Ensure it's 320x180 grayscale
            result_image = result_image.convert("L").resize((320, 180), Image.Resampling.LANCZOS)
            
            img_bytes = image_to_bytes(result_image)
            return send_file(
                io.BytesIO(img_bytes),
                mimetype='image/png',
                as_attachment=False,
                download_name='generated.png'
            )
        else:
            # If we got something else (like a text response saying it can't do it)
            return jsonify({'error': 'Model did not return an image', 'details': str(result_image)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        api_key = request.form.get('api_key')
        if not api_key:
            return jsonify({'error': 'API Key is required'}), 400

        image_file = request.files.get('image')
        if not image_file:
            return jsonify({'error': 'Image is required'}), 400

        image = process_image(image_file)
        if not image:
            return jsonify({'error': 'Invalid image'}), 400

        # Use a default model for analysis if not specified, or the one from client
        # We'll use the client's default which we set to gemini-2.5-flash-image
        # But inside analyze_image we force gemini-1.5-flash for better VQA
        client = GeminiClient(api_key=api_key)
        
        analysis_result = client.analyze_image(image)
        
        return jsonify(analysis_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
