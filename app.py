"""Flask application for gesture data generation with history tracking."""

import io
import os
import base64
import time
import uuid
import zipfile
import concurrent.futures
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image

from gemini_client import GeminiClient
from utils import process_image
from database import db, init_db, get_images_dir
from models import GenerationRecord

app = Flask(__name__)

# Initialize database
init_db(app)


def save_image_to_file(img, prefix='gen'):
    """Save a PIL Image to the images directory and return the relative path."""
    images_dir = get_images_dir()
    filename = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(images_dir, filename)

    # Ensure grayscale and correct size
    img = img.convert("L").resize((320, 180), Image.Resampling.LANCZOS)
    img.save(filepath, format="PNG")

    # Return relative path for storage in database
    return f"images/{filename}"


def save_upload_to_file(file_storage, prefix='seed'):
    """Save an uploaded file to the images directory and return the relative path."""
    images_dir = get_images_dir()
    ext = os.path.splitext(file_storage.filename)[1] or '.png'
    filename = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(images_dir, filename)

    # Read and process the image
    img = process_image(file_storage)
    if img:
        img.save(filepath, format="PNG")
        return f"images/{filename}"
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/history')
def history_page():
    return render_template('history.html')


@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        start_time = time.time()

        batch_size = int(request.form.get('batch_size', 1))
        batch_size = max(1, min(batch_size, 4))

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

        # Save seed image
        seed_file.seek(0)
        seed_image_path = save_upload_to_file(seed_file, prefix='seed')

        # Prepare reference image if needed
        ref_image = None
        ref_image_path = None
        if mode == 'modification':
            ref_file = request.files.get('reference_image')
            if not ref_file:
                return jsonify({'error': 'Reference image is required for modification'}), 400
            ref_image = process_image(ref_file)
            ref_file.seek(0)
            ref_image_path = save_upload_to_file(ref_file, prefix='ref')

        # Helper function for single generation
        def generate_single():
            try:
                if mode == 'variation':
                    return client.generate_variation(seed_image, prompt)
                elif mode == 'modification':
                    return client.modify_gesture(seed_image, ref_image, prompt)
                else:
                    raise ValueError("Invalid mode")
            except Exception as e:
                print(f"Generation error: {e}")
                return None

        # Run in parallel
        generated_images = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [executor.submit(generate_single) for _ in range(batch_size)]
            for future in concurrent.futures.as_completed(futures):
                img = future.result()
                if img and isinstance(img, Image.Image):
                    generated_images.append(img)

        # Calculate latency
        api_latency_ms = int((time.time() - start_time) * 1000)

        # Determine status
        if not generated_images:
            status = 'failed'
        elif len(generated_images) < batch_size:
            status = 'partial'
        else:
            status = 'success'

        # Save generated images and prepare response
        output_paths = []
        encoded_images = []

        for img in generated_images:
            # Save to file
            path = save_image_to_file(img, prefix='gen')
            output_paths.append(path)

            # Prepare base64 for response
            img = img.convert("L").resize((320, 180), Image.Resampling.LANCZOS)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            encoded_images.append(f"data:image/png;base64,{img_str}")

        # Create database record
        record = GenerationRecord(
            mode=mode,
            prompt=prompt,
            model=model_name,
            batch_size=batch_size,
            seed_image_path=seed_image_path,
            reference_image_path=ref_image_path,
            output_images=output_paths,
            status=status,
            success_count=len(generated_images),
            api_latency_ms=api_latency_ms
        )
        db.session.add(record)
        db.session.commit()

        if not generated_images:
            return jsonify({'error': 'Failed to generate any images', 'record_id': record.id}), 500

        return jsonify({
            'images': encoded_images,
            'record_id': record.id,
            'status': status,
            'success_count': len(generated_images)
        })

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

        client = GeminiClient(api_key=api_key)
        analysis_result = client.analyze_image(image)

        # Optionally update a record's analysis_results if record_id is provided
        record_id = request.form.get('record_id')
        if record_id:
            record = GenerationRecord.query.get(int(record_id))
            if record:
                record.analysis_results = analysis_result
                db.session.commit()

        return jsonify(analysis_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get paginated history with filtering support."""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        per_page = min(per_page, 50)  # Limit max per page

        # Filter parameters
        mode = request.args.get('mode')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        q = request.args.get('q')  # Search query for prompt

        # Build query
        query = GenerationRecord.query

        if mode:
            query = query.filter(GenerationRecord.mode == mode)
        if status:
            query = query.filter(GenerationRecord.status == status)
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from)
                query = query.filter(GenerationRecord.created_at >= from_date)
            except ValueError:
                pass
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to)
                query = query.filter(GenerationRecord.created_at <= to_date)
            except ValueError:
                pass
        if q:
            query = query.filter(GenerationRecord.prompt.ilike(f'%{q}%'))

        # Order by newest first
        query = query.order_by(GenerationRecord.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [record.to_dict() for record in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<int:record_id>', methods=['GET'])
def get_history_detail(record_id):
    """Get a single history record by ID."""
    try:
        record = GenerationRecord.query.get(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404

        return jsonify(record.to_dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<int:record_id>', methods=['DELETE'])
def delete_history(record_id):
    """Delete a history record and its associated files."""
    try:
        record = GenerationRecord.query.get(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404

        # Delete associated image files
        from database import DATA_DIR
        files_to_delete = []

        if record.seed_image_path:
            files_to_delete.append(os.path.join(DATA_DIR, record.seed_image_path))
        if record.reference_image_path:
            files_to_delete.append(os.path.join(DATA_DIR, record.reference_image_path))
        if record.output_images:
            for path in record.output_images:
                files_to_delete.append(os.path.join(DATA_DIR, path))

        # Delete files (ignore errors for missing files)
        for filepath in files_to_delete:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except OSError:
                pass

        # Delete database record
        db.session.delete(record)
        db.session.commit()

        return jsonify({'success': True, 'message': f'Record {record_id} deleted'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<int:record_id>/download', methods=['GET'])
def download_history(record_id):
    """Download all images from a record as a ZIP file."""
    try:
        record = GenerationRecord.query.get(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404

        from database import DATA_DIR

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add seed image
            if record.seed_image_path:
                filepath = os.path.join(DATA_DIR, record.seed_image_path)
                if os.path.exists(filepath):
                    zip_file.write(filepath, f'seed_{os.path.basename(filepath)}')

            # Add reference image
            if record.reference_image_path:
                filepath = os.path.join(DATA_DIR, record.reference_image_path)
                if os.path.exists(filepath):
                    zip_file.write(filepath, f'reference_{os.path.basename(filepath)}')

            # Add output images
            if record.output_images:
                for i, path in enumerate(record.output_images):
                    filepath = os.path.join(DATA_DIR, path)
                    if os.path.exists(filepath):
                        zip_file.write(filepath, f'output_{i+1}_{os.path.basename(filepath)}')

            # Add metadata
            metadata = f"""Generation Record #{record.id}
Mode: {record.mode}
Model: {record.model}
Prompt: {record.prompt or 'N/A'}
Created: {record.created_at}
Status: {record.status}
Success Count: {record.success_count}/{record.batch_size}
API Latency: {record.api_latency_ms}ms
"""
            zip_file.writestr('metadata.txt', metadata)

        zip_buffer.seek(0)

        filename = f"generation_{record_id}_{record.created_at.strftime('%Y%m%d_%H%M%S')}.zip"
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/data/images/<path:filename>')
def serve_image(filename):
    """Serve images from the data/images directory."""
    from database import IMAGES_DIR
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    return jsonify({'error': 'Image not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
