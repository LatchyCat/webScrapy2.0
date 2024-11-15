# status_check.py
import requests
import json
from datetime import datetime

def check_status():
    """Check the complete system status"""
    try:
        # Get both system status and scraping progress
        response = requests.get('http://127.0.0.1:5000/api/system-status')
        progress_response = requests.get('http://127.0.0.1:5000/api/scraping-progress')

        if response.status_code == 200 and progress_response.status_code == 200:
            data = response.json()
            progress_data = progress_response.json()

            print("\n=== System Status Check ===")
            print(f"Status: {data['status']}")
            print(f"Timestamp: {data['timestamp']}")

            # Database Status with more detail
            print("\n📊 Database Status:")
            print(f"- Total articles: {data['database']['total_articles']}")
            if data['database']['latest_article']:
                print(f"- Latest article: {data['database']['latest_article']['title']}")
                print(f"- Created at: {data['database']['latest_article']['created_at']}")
                print(f"- Database path: instance/charleston_news.db")

            # File System Status
            print("\n📁 File System Status:")
            print(f"- Data directory: {'✅' if data['file_system']['data_dir_exists'] else '❌'}")
            print(f"- Articles directory: {'✅' if data['file_system']['articles_dir_exists'] else '❌'}")
            print(f"- JSON files: {data['file_system']['json_files']}")
            print(f"- Log file: {'✅' if data['file_system']['log_file_exists'] else '❌'}")

            # Scraping Process Status
            print("\n🤖 Scraping Status:")
            print(f"- Process status: {progress_data.get('status', 'unknown').upper()}")
            print(f"- Total URLs found: {progress_data.get('total_urls', 0)}")
            print(f"- URLs processed: {progress_data.get('processed_urls', 0)}")
            print(f"- Successful scrapes: {progress_data.get('successful_scrapes', 0)}")
            print(f"- Failed scrapes: {progress_data.get('failed_scrapes', 0)}")

            # Show recent activity
            if progress_data.get('last_scraped_articles'):
                print("\n📰 Recently Scraped Articles:")
                for article in progress_data['last_scraped_articles'][-3:]:
                    print(f"- {article['title']}")
                    print(f"  {article['url']}")
                    print(f"  Scraped at: {article['timestamp']}")

            # Database commands helper
            print("\n💡 SQLite Commands:")
            print("To check database:")
            print("$ sqlite3 instance/charleston_news.db")
            print("sqlite> .mode column")
            print("sqlite> .headers on")
            print("sqlite> SELECT COUNT(*) FROM articles;")

        else:
            print(f"Error: Server returned status code {response.status_code}")

    except requests.RequestException as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    check_status()
