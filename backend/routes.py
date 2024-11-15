# routes.py

from app import app, db
from models import Article
from scraper import CharlestonNewsScraper
from data_manager import DataManager
from flask import jsonify, request
from datetime import datetime, UTC
import logging
import threading
from functools import wraps
import time
import os

# Enhanced logger setup
logger = logging.getLogger('Routes')
logger.setLevel(logging.INFO)

# Route emojis and tags for better visualization
ROUTE_INFO = {
    'scraping-progress': {'emoji': '📊', 'tag': '[PROGRESS]', 'color': '\033[94m'},  # Blue
    'start-scraping': {'emoji': '🚀', 'tag': '[SCRAPER]', 'color': '\033[92m'},      # Green
    'refresh': {'emoji': '🔄', 'tag': '[REFRESH]', 'color': '\033[93m'},             # Yellow
    'health': {'emoji': '❤️', 'tag': '[HEALTH]', 'color': '\033[95m'},               # Magenta
    'articles': {'emoji': '📰', 'tag': '[ARTICLES]', 'color': '\033[96m'},           # Cyan
    'database-stats': {'emoji': '📈', 'tag': '[STATS]', 'color': '\033[97m'},        # White
    'search': {'emoji': '🔍', 'tag': '[SEARCH]', 'color': '\033[91m'}               # Red
}

# ANSI escape codes for colors
RESET_COLOR = '\033[0m'

def log_route(func):
    """Decorator to log route information with enhanced formatting"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # Get route name from the function name
        route_name = func.__name__.replace('_', '-')

        # Get route info
        route_info = ROUTE_INFO.get(route_name, {'emoji': '🔵', 'tag': '[API]', 'color': '\033[0m'})

        # Log request
        logger.info(f"{route_info['color']}{route_info['emoji']} "
                   f"{route_info['tag']} Request to {route_name} "
                   f"[{request.method}] from {request.remote_addr}{RESET_COLOR}")

        # Execute route
        result = func(*args, **kwargs)

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Log response
        status_code = result[1] if isinstance(result, tuple) else 200
        status_emoji = '✅' if status_code < 400 else '❌'

        logger.info(f"{route_info['color']}{status_emoji} "
                   f"{route_info['tag']} Response from {route_name} "
                   f"[{status_code}] in {execution_time:.2f}ms{RESET_COLOR}")

        return result
    return wrapper

# Initialize components
data_manager = DataManager()
scraper = CharlestonNewsScraper()

def run_scraper():
    """Run the scraper in a separate thread"""
    try:
        logger.info("🔄 Starting scraper thread...")
        with app.app_context():  # Add this line
            data_manager.process_articles()
    except Exception as e:
        logger.error(f"❌ Error in scraper thread: {e}")
        scraper.progress.status = 'error'
        scraper.progress.error_message = str(e)

@app.route('/api/scraping-progress', methods=['GET'])
@log_route
def get_scraping_progress():
    """Get the current scraping progress"""
    try:
        progress = scraper.progress.to_dict()
        return jsonify(progress)
    except Exception as e:
        logger.error(f"❌ Error getting progress: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/start-scraping', methods=['POST'])
@log_route
def start_scraping():
    """Start the scraping process"""
    try:
        if scraper.progress.status == 'running':
            logger.warning("⚠️ Scraping already in progress")
            return jsonify({
                'status': 'error',
                'message': 'A scraping operation is already in progress'
            }), 409

        # Reset progress
        scraper.progress.status = 'running'
        scraper.progress.processed_urls = 0
        scraper.progress.successful_scrapes = 0
        scraper.progress.failed_scrapes = 0
        scraper.progress.total_urls = 0
        scraper.progress.start_time = datetime.now()
        scraper.progress.error_message = None
        scraper.progress.last_scraped_articles = []

        # Start scraping thread
        thread = threading.Thread(target=run_scraper)
        thread.daemon = True
        thread.start()

        logger.info("🚀 Scraping process initiated")
        return jsonify({
            'status': 'success',
            'message': 'Scraping process started'
        })

    except Exception as e:
        logger.error(f"❌ Error starting scraping: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/refresh', methods=['POST'])
@log_route
def refresh_articles():
    """Scrape new articles and update database"""
    try:
        if data_manager.scraper.progress.status == 'running':
            logger.warning("⚠️ Refresh already in progress")
            return jsonify({
                'status': 'error',
                'message': 'A scraping operation is already in progress'
            }), 409

        # Reset progress and start scraping
        logger.info("🔄 Initiating refresh process")
        return start_scraping()

    except Exception as e:
        logger.error(f"❌ Error in refresh_articles: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
@log_route
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'scraper_status': scraper.progress.status
    })

@app.route('/api/articles', methods=['GET'])
@log_route
def get_articles():
    """Get paginated articles from database"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        logger.info(f"📃 Fetching articles page {page} (per_page: {per_page})")
        articles = Article.query.order_by(Article.date.desc())\
                             .paginate(page=page, per_page=per_page)

        return jsonify({
            'status': 'success',
            'count': articles.total,
            'pages': articles.pages,
            'current_page': articles.page,
            'data': [article.to_dict() for article in articles.items],
            'database_stats': data_manager.get_database_stats()
        })
    except Exception as e:
        logger.error(f"❌ Error in get_articles: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/database-stats', methods=['GET'])
@log_route
def get_database_stats():
    """Get current database statistics"""
    try:
        stats = data_manager.get_database_stats()
        stats['scraper_status'] = scraper.progress.status
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Error getting database stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/search', methods=['GET'])
@log_route
def search_articles():
    """Search articles by query string"""
    try:
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if not query:
            logger.warning("⚠️ Empty search query received")
            return jsonify({
                'status': 'error',
                'message': 'Search query is required'
            }), 400

        logger.info(f"🔍 Searching for: '{query}' (page {page}, per_page: {per_page})")
        pagination = Article.query.filter(
            db.or_(
                Article.title.ilike(f'%{query}%'),
                Article.content.ilike(f'%{query}%')
            )
        ).order_by(Article.date.desc())\
         .paginate(page=page, per_page=per_page)

        return jsonify({
            'status': 'success',
            'count': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'data': [article.to_dict() for article in pagination.items]
        })
    except Exception as e:
        logger.error(f"❌ Error in search_articles: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/system-status', methods=['GET'])
@log_route
def system_status():
    """Get complete system status"""
    try:
        # Database status
        db_status = {
            'total_articles': Article.query.count(),
            'latest_article': None,
            'database_connected': True
        }

        latest = Article.query.order_by(Article.created_at.desc()).first()
        if latest:
            db_status['latest_article'] = {
                'title': latest.title,
                'created_at': latest.created_at.isoformat()
            }

        # File system status
        fs_status = {
            'data_dir_exists': os.path.exists('data'),
            'articles_dir_exists': os.path.exists('data/articles'),
            'json_files': 0,
            'log_file_exists': os.path.exists('scraper.log')
        }

        if os.path.exists('data/articles'):
            fs_status['json_files'] = len([f for f in os.listdir('data/articles')
                                         if f.endswith('.json')])

        # Scraper status
        scraper_status = {
            'status': scraper.progress.status,
            'total_urls': scraper.progress.total_urls,
            'processed_urls': scraper.progress.processed_urls,
            'successful_scrapes': scraper.progress.successful_scrapes,
            'failed_scrapes': scraper.progress.failed_scrapes,
            'current_article': scraper.progress.current_article,
            'start_time': scraper.progress.start_time.isoformat() if scraper.progress.start_time else None
        }

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'file_system': fs_status,
            'scraper': scraper_status
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
