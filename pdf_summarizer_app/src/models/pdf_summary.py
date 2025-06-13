from src.models.user import db
from datetime import datetime

class PDFSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    google_drive_link = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    key_messages = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_processed = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PDFSummary {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'file_path': self.file_path,
            'google_drive_link': self.google_drive_link,
            'summary': self.summary,
            'key_messages': self.key_messages,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'date_processed': self.date_processed.isoformat() if self.date_processed else None
        }

