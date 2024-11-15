# WebScrappy 2.0 - Charleston RiverDogs News Scraper 🤖

An automated web scraping system for collecting and managing news articles from the Charleston RiverDogs website. Built with Python, Flask, and SQLite.

## 🌟 Features

- Real-time scraping progress monitoring
- Database management with SQLite
- JSON backup system
- RESTful API endpoints
- Health checks and system monitoring
- Elegant CLI interface with emoji support
- Error logging and handling
- Article search functionality

## 🔧 Components

### 1. monitor.py
- Real-time scraping progress visualization
- System health monitoring
- Performance metrics tracking
- Emoji-enhanced CLI interface

### 2. status_check.py
- System status reporting
- Database statistics
- File system checks
- SQLite command helper

### 3. trigger_scraping.py
- Initiates scraping process
- Server status verification
- Progress monitoring setup
- Error handling

### 4. scraper.py
- Article content extraction
- Image handling
- Progress tracking
- Data validation
- Rate limiting

### 5. routes.py
- RESTful API endpoints
- Request logging
- Error handling
- Enhanced status reporting

### 6. data_manager.py
- Database operations
- JSON backup management
- Error logging
- Data validation

## 🚀 Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
flask db upgrade
```

3. Start Flask server:
```bash
export FLASK_APP=app.py
flask run
```

4. Start scraping:
```bash
python3 trigger_scraping.py
```

5. Monitor progress:
```bash
python3 monitor.py
```

## 📡 API Endpoints

### Scraping Operations
- `POST /api/start-scraping` - Start scraping process
- `GET /api/scraping-progress` - Get current progress
- `POST /api/refresh` - Refresh articles

### Data Access
- `GET /api/articles` - Get paginated articles
- `GET /api/search` - Search articles
- `GET /api/database-stats` - Get database statistics

### System
- `GET /health` - Health check
- `GET /api/system-status` - Complete system status

## 📊 Monitoring

The monitor provides real-time information about:
- Scraping progress
- Articles processed
- Success/failure rates
- Processing speed
- Estimated completion time
- Database status
- System health

## 💾 Data Storage

Articles are stored in:
1. SQLite database (`instance/charleston_news.db`)
2. JSON backups (`data/articles/`)

## 🔍 Error Handling

- Comprehensive error logging
- Automatic retry mechanisms
- Transaction management
- Data validation
- Health monitoring

## 📝 Notes

- Rate limiting is implemented to respect website policies
- JSON backups are created for all successfully scraped articles
- System automatically handles duplicate articles
- Progress monitoring is available through CLI interface

## 🛠️ Troubleshooting

If scraping fails:
1. Check server status: `python3 status_check.py`
2. Verify database connection
3. Check log files for errors
4. Ensure proper network connectivity
5. Verify API endpoints are responding

## 🔒 Prerequisites

- Python 3.8+
- Flask
- SQLite3
- BeautifulSoup4
- Requests

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📄 License

This project is licensed under the MIT License.
