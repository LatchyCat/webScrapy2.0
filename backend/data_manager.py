# data_manager.py
from scraper import CharlestonNewsScraper
from models import db, Article
import logging
from datetime import datetime
from typing import Dict, Optional
import json
import os
from error_handler import ErrorLogger
from flask import Flask, current_app

class DataManager:
    def __init__(self):
        self.scraper = CharlestonNewsScraper()
        self.logger = logging.getLogger('DataManager')
        self.json_backup_dir = 'data/articles'
        self.error_logger = ErrorLogger()
        os.makedirs(self.json_backup_dir, exist_ok=True)

    def validate_json_data(self, data: Dict) -> bool:
        """Validate if the data is JSON serializable"""
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError) as e:
            self.logger.error(f"JSON validation failed: {e}")
            return False

    def save_to_json_file(self, article_data: Dict, filename: Optional[str] = None) -> str:
        """Save individual article to JSON file for RAG processing"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"article_{article_data.get('id', timestamp)}.json"

        filepath = os.path.join(self.json_backup_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            self.logger.error(f"Error saving article to JSON: {e}")
            return None


    def process_articles(self) -> Dict:
        """Scrape articles and save to database with JSON backup"""
        try:
            with current_app.app_context():  # Ensure we're in application context
                self.logger.info("Starting article processing")
                scraped_articles = self.scraper.scrape_all_articles()

                stats = {
                    'new_articles': 0,
                    'updated_articles': 0,
                    'failed_saves': 0,
                    'json_backups': 0,
                    'start_time': datetime.now(),
                    'end_time': None
                }

                for article_data in scraped_articles:
                    try:
                        # Validate and process article
                        if not self.validate_json_data(article_data):
                            self.error_logger.log_error(
                                'JSONSerializationError',
                                f"Invalid JSON data for article: {article_data.get('title', 'Unknown')}"
                            )
                            stats['failed_saves'] += 1
                            continue

                        # Create or update article
                        article = self.save_article_to_db(article_data)
                        if article:
                            # Save JSON backup
                            json_path = self.save_to_json_file(article_data)
                            if json_path:
                                stats['json_backups'] += 1

                        db.session.commit()

                    except Exception as e:
                        db.session.rollback()
                        self.error_logger.log_error(
                            'DatabaseError',
                            str(e),
                            {'article_title': article_data.get('title')}
                        )
                        stats['failed_saves'] += 1

                stats['end_time'] = datetime.now()
                return stats

        except Exception as e:
            error_entry = self.error_logger.log_error(
                'WorkingOutsideApplication',
                str(e)
            )
            return {
                'status': 'error',
                'message': str(e),
                'solution': error_entry['solution']
            }

    def save_article_to_db(self, article_data):
        """Save article to database"""
        try:
            self.logger.info(f"Attempting to save article: {article_data.get('title')}")

            # Create a copy of the data and remove fields that aren't in the model
            filtered_data = article_data.copy()
            if 'last_updated' in filtered_data:
                try:
                    filtered_data['last_updated'] = datetime.fromisoformat(filtered_data['last_updated'])
                except (ValueError, TypeError):
                    filtered_data['last_updated'] = datetime.utcnow()

            existing_article = Article.query.filter_by(
                url=filtered_data['url']
            ).first()

            if existing_article:
                # Update existing article
                self.logger.info(f"Updating existing article: {existing_article.title}")
                for key, value in filtered_data.items():
                    if hasattr(existing_article, key):
                        setattr(existing_article, key, value)
                existing_article.updated_at = datetime.utcnow()
                db.session.commit()  # Commit the changes
                self.logger.info(f"Successfully updated article: {existing_article.title}")
                return existing_article
            else:
                # Create new article
                self.logger.info(f"Creating new article: {filtered_data['title']}")
                new_article = Article.from_scraper_data(filtered_data)
                db.session.add(new_article)
                db.session.commit()  # Commit the changes
                self.logger.info(f"Successfully created article: {new_article.title}")
                return new_article

        except Exception as e:
            db.session.rollback()
            error_entry = self.error_logger.log_error(
                'DatabaseSaveError',
                str(e),
                {'article_data': article_data}
            )
            self.logger.error(f"Failed to save article: {str(e)}")
            return None

    def get_database_stats(self) -> Dict:
        """Get current database statistics"""
        try:
            with current_app.app_context():  # Add this line
                total_articles = Article.query.count()
                latest_article = Article.query.order_by(Article.created_at.desc()).first()
                oldest_article = Article.query.order_by(Article.created_at.asc()).first()

                # Count JSON backups
                json_files = len([f for f in os.listdir(self.json_backup_dir)
                                if f.endswith('.json')])

                return {
                    'total_articles': total_articles,
                    'latest_article': latest_article.to_dict() if latest_article else None,
                    'oldest_article': oldest_article.to_dict() if oldest_article else None,
                    'json_backups': json_files,
                    'last_update': datetime.now().isoformat()
                }
        except Exception as e:
            error_entry = self.error_logger.log_error(  # Use error logger
                'DatabaseStatsError',
                str(e)
            )
            return {
                'status': 'error',
                'message': str(e),
                'solution': error_entry['solution']
            }
