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
        batch_size = int(request.form.get('batch_size', 1))
        # Limit batch size to avoid abuse/timeouts
        batch_size = max(1, min(batch_size, 4))

        # Retrieve required fields
        api_key = request.form.get('api_key')
        model_name = request.form.get('model_name', 'gemini-2.5-flash-image')
        prompt = request.form.get('prompt')
        mode = request.form.get('mode')

        if not api_key:
            return jsonify({'error': 'API Key is required'}), 400

        client = GeminiClient(api_key=api_key, model_name=model_name)

        seed_file = request.files.get('seed_image')
        if not seed_file:
            return jsonify({'error': 'Seed image is required'}), 400
            
        seed_image = process_image(seed_file)
        if not seed_image:
            return jsonify({'error': 'Invalid seed image'}), 400

        # Helper function for single generation
        def generate_single():
            try:
                if mode == 'variation':
                    return client.generate_variation(seed_image, prompt)
                elif mode == 'modification':
                    # We need to process ref_image inside or pass it. 
                    # Since ref_image is same for all, process once outside.
                    return client.modify_gesture(seed_image, ref_image, prompt)
                else:
                    raise ValueError("Invalid mode")
            except Exception as e:
                print(f"Generation error: {e}")
                return None

        # Prepare reference image if needed
        ref_image = None
        if mode == 'modification':
            ref_file = request.files.get('reference_image')
            if not ref_file:
                return jsonify({'error': 'Reference image is required for modification'}), 400
            ref_image = process_image(ref_file)

        # Run in parallel
        import concurrent.futures
        generated_images = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [executor.submit(generate_single) for _ in range(batch_size)]
            for future in concurrent.futures.as_completed(futures):
                img = future.result()
                if img and isinstance(img, Image.Image):
                    generated_images.append(img)

        if not generated_images:
            return jsonify({'error': 'Failed to generate any images'}), 500

        # Process and convert to Base64
        encoded_images = []
        for img in generated_images:
            # Ensure 320x180 grayscale
            img = img.convert("L").resize((320, 180), Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            encoded_images.append(f"data:image/png;base64,{img_str}")

        return jsonify({'images': encoded_images})

    except Exception as e:
        print(f"Error in generate endpoint: {e}")
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
