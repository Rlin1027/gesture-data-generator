"""GenerationRecord model for storing image generation history."""

from datetime import datetime
from database import db


class GenerationRecord(db.Model):
    """Model to store image generation history."""

    __tablename__ = 'generations'

    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(20), nullable=False)  # 'variation' | 'modification'
    prompt = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(100), nullable=False)
    batch_size = db.Column(db.Integer, nullable=False, default=1)
    seed_image_path = db.Column(db.String(500), nullable=True)
    reference_image_path = db.Column(db.String(500), nullable=True)
    output_images = db.Column(db.JSON, nullable=True)  # ['images/001.png', ...]
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), index=True, default='success')  # 'success' | 'partial' | 'failed'
    success_count = db.Column(db.Integer, default=0)
    api_latency_ms = db.Column(db.Integer, nullable=True)
    analysis_results = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        """Convert record to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'mode': self.mode,
            'prompt': self.prompt,
            'model': self.model,
            'batch_size': self.batch_size,
            'seed_image_path': self.seed_image_path,
            'reference_image_path': self.reference_image_path,
            'output_images': self.output_images or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'success_count': self.success_count,
            'api_latency_ms': self.api_latency_ms,
            'analysis_results': self.analysis_results
        }

    def __repr__(self):
        return f'<GenerationRecord {self.id} - {self.mode} @ {self.created_at}>'
