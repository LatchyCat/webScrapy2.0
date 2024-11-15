# models.py
# https://www.milb.com/charleston/news
from app import db
from datetime import datetime

class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    content = db.Column(db.Text)
    date = db.Column(db.String(100))
    subheadline = db.Column(db.String(500))
    images = db.Column(db.JSON)
    section = db.Column(db.String(100))
    tags = db.Column(db.JSON)
    social_shares = db.Column(db.JSON)
    author = db.Column(db.JSON)
    last_updated = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'date': self.date,
            'subheadline': self.subheadline,
            'images': self.images,
            'section': self.section,
            'tags': self.tags,
            'social_shares': self.social_shares,
            'author': self.author,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def from_scraper_data(data):
        # Convert last_updated string to datetime if it exists
        last_updated = None
        if 'last_updated' in data:
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except (ValueError, TypeError):
                last_updated = datetime.utcnow()

        # Create filtered data with only model fields
        model_fields = Article.__table__.columns.keys()
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Set last_updated separately
        filtered_data['last_updated'] = last_updated

        return Article(**filtered_data)
