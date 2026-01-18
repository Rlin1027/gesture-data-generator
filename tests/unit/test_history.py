"""Unit tests for history functionality."""

import os
import sys
import json
import tempfile
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Flask
from database import db, init_db
from models import GenerationRecord


@pytest.fixture
def app():
    """Create application for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Use temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{tmpdir}/test.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(app)

        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestGenerationRecordModel:
    """Tests for GenerationRecord model."""

    def test_create_record(self, app):
        """Test creating a new generation record."""
        with app.app_context():
            record = GenerationRecord(
                mode='variation',
                prompt='Test prompt',
                model='gemini-2.5-flash-image',
                batch_size=3,
                status='success',
                success_count=3
            )
            db.session.add(record)
            db.session.commit()

            assert record.id is not None
            assert record.mode == 'variation'
            assert record.prompt == 'Test prompt'
            assert record.batch_size == 3
            assert record.status == 'success'

    def test_record_to_dict(self, app):
        """Test converting record to dictionary."""
        with app.app_context():
            record = GenerationRecord(
                mode='modification',
                prompt='Test prompt',
                model='gemini-2.5-flash-image',
                batch_size=2,
                output_images=['images/test1.png', 'images/test2.png'],
                status='success',
                success_count=2,
                api_latency_ms=1500
            )
            db.session.add(record)
            db.session.commit()

            result = record.to_dict()

            assert result['id'] == record.id
            assert result['mode'] == 'modification'
            assert result['prompt'] == 'Test prompt'
            assert result['output_images'] == ['images/test1.png', 'images/test2.png']
            assert result['api_latency_ms'] == 1500

    def test_record_defaults(self, app):
        """Test default values for record fields."""
        with app.app_context():
            record = GenerationRecord(
                mode='variation',
                model='test-model',
                batch_size=1
            )
            db.session.add(record)
            db.session.commit()

            assert record.status == 'success'
            assert record.success_count == 0
            assert record.created_at is not None
            assert record.output_images is None

    def test_query_by_mode(self, app):
        """Test querying records by mode."""
        with app.app_context():
            # Create records with different modes
            for i in range(3):
                record = GenerationRecord(
                    mode='variation',
                    model='test-model',
                    batch_size=1
                )
                db.session.add(record)

            for i in range(2):
                record = GenerationRecord(
                    mode='modification',
                    model='test-model',
                    batch_size=1
                )
                db.session.add(record)

            db.session.commit()

            variation_records = GenerationRecord.query.filter_by(mode='variation').all()
            modification_records = GenerationRecord.query.filter_by(mode='modification').all()

            assert len(variation_records) == 3
            assert len(modification_records) == 2

    def test_query_by_status(self, app):
        """Test querying records by status."""
        with app.app_context():
            statuses = ['success', 'success', 'partial', 'failed']
            for status in statuses:
                record = GenerationRecord(
                    mode='variation',
                    model='test-model',
                    batch_size=1,
                    status=status
                )
                db.session.add(record)

            db.session.commit()

            success_records = GenerationRecord.query.filter_by(status='success').all()
            failed_records = GenerationRecord.query.filter_by(status='failed').all()

            assert len(success_records) == 2
            assert len(failed_records) == 1

    def test_delete_record(self, app):
        """Test deleting a record."""
        with app.app_context():
            record = GenerationRecord(
                mode='variation',
                model='test-model',
                batch_size=1
            )
            db.session.add(record)
            db.session.commit()

            record_id = record.id

            db.session.delete(record)
            db.session.commit()

            deleted_record = GenerationRecord.query.get(record_id)
            assert deleted_record is None

    def test_prompt_search(self, app):
        """Test searching records by prompt content."""
        with app.app_context():
            prompts = [
                'Generate sunny background',
                'Create dark scene',
                'Make it sunny and warm'
            ]
            for prompt in prompts:
                record = GenerationRecord(
                    mode='variation',
                    prompt=prompt,
                    model='test-model',
                    batch_size=1
                )
                db.session.add(record)

            db.session.commit()

            sunny_records = GenerationRecord.query.filter(
                GenerationRecord.prompt.ilike('%sunny%')
            ).all()

            assert len(sunny_records) == 2

    def test_order_by_created_at(self, app):
        """Test ordering records by creation time."""
        with app.app_context():
            for i in range(5):
                record = GenerationRecord(
                    mode='variation',
                    prompt=f'Prompt {i}',
                    model='test-model',
                    batch_size=1
                )
                db.session.add(record)
                db.session.commit()

            # Query in descending order (newest first)
            records = GenerationRecord.query.order_by(
                GenerationRecord.created_at.desc()
            ).all()

            assert len(records) == 5
            # Check that records are in descending order
            for i in range(len(records) - 1):
                assert records[i].created_at >= records[i + 1].created_at


class TestJSONFields:
    """Tests for JSON fields in the model."""

    def test_output_images_json(self, app):
        """Test storing and retrieving output images as JSON."""
        with app.app_context():
            images = ['images/001.png', 'images/002.png', 'images/003.png']
            record = GenerationRecord(
                mode='variation',
                model='test-model',
                batch_size=3,
                output_images=images
            )
            db.session.add(record)
            db.session.commit()

            # Retrieve and verify
            retrieved = GenerationRecord.query.get(record.id)
            assert retrieved.output_images == images
            assert len(retrieved.output_images) == 3

    def test_analysis_results_json(self, app):
        """Test storing and retrieving analysis results as JSON."""
        with app.app_context():
            analysis = {
                'gesture_type': 'swipe_left',
                'confidence': 0.95,
                'details': {
                    'hand_position': 'center',
                    'motion_blur': False
                }
            }
            record = GenerationRecord(
                mode='variation',
                model='test-model',
                batch_size=1,
                analysis_results=analysis
            )
            db.session.add(record)
            db.session.commit()

            # Retrieve and verify
            retrieved = GenerationRecord.query.get(record.id)
            assert retrieved.analysis_results['gesture_type'] == 'swipe_left'
            assert retrieved.analysis_results['confidence'] == 0.95
            assert retrieved.analysis_results['details']['hand_position'] == 'center'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
