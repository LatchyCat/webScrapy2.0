# monitor.py
import requests
import json
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Monitor')

# Emojis for different states and indicators
EMOJIS = {
    'running': '🔄',
    'completed': '✅',
    'error': '❌',
    'idle': '💤',
    'progress': '📊',
    'time': '⏱️',
    'article': '📰',
    'success': '🎉',
    'failed': '⚠️',
    'stats': '📈',
    'health': '❤️',
    'warning': '⚡',
    'loading': '⌛',
    'url': '🔗',
    'database': '💾',
    'info': 'ℹ️'
}

class ProgressMonitor:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.progress_endpoint = f"{base_url}/api/scraping-progress"
        self.status_endpoint = f"{base_url}/api/system-status"
        self.health_endpoint = f"{base_url}/health"
        self.last_status = None
        self.start_time = None
        self.last_article = None
        self.articles_per_minute = 0
        self.last_processed = 0
        self.last_time = datetime.now()

    def get_system_status(self):
        """Get complete system status"""
        try:
            response = requests.get(self.status_endpoint)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def check_health(self):
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return False

    def calculate_speed(self, processed):
        """Calculate articles processing speed"""
        current_time = datetime.now()
        time_diff = (current_time - self.last_time).total_seconds() / 60
        if time_diff > 0:
            articles_diff = processed - self.last_processed
            self.articles_per_minute = articles_diff / time_diff
            self.last_processed = processed
            self.last_time = current_time

    def monitor_progress(self):
        try:
            response = requests.get(self.progress_endpoint)
            system_status = self.get_system_status()

            if response.status_code == 200 and system_status:
                progress_data = response.json()

                # Update start time when scraping begins
                if progress_data.get('status') == 'running' and self.last_status != 'running':
                    self.start_time = datetime.now()
                    self.last_time = datetime.now()
                    self.last_processed = 0
                    self.articles_per_minute = 0

                self.last_status = progress_data.get('status')

                # Calculate processing speed
                if self.last_status == 'running':
                    self.calculate_speed(progress_data.get('processed_urls', 0))

                return self._format_display(progress_data, system_status)
            else:
                logger.error(f"Error fetching progress: Status code {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error monitoring progress: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None

    def _format_display(self, progress_data, system_status):
        """Format the display output"""
        if not progress_data or not system_status:
            return "No data available"

        status = progress_data.get('status', 'unknown')
        processed = progress_data.get('processed_urls', 0)
        total = progress_data.get('total_urls', 0)
        percentage = (processed / total * 100) if total > 0 else 0

        lines = [
            f"\n{'='*50}",
            f"🤖 Charleston News Scraper Monitor {EMOJIS['health']}",
            f"{'='*50}",
            f"\n{EMOJIS[status.lower()]} Status: {status.upper()}",
            f"{EMOJIS['progress']} Progress: {processed}/{total} articles ({percentage:.1f}%)"
        ]

        # Add database status
        db_status = system_status.get('database', {})
        lines.extend([
            f"\n{EMOJIS['database']} Database Status:",
            f"- Total articles: {db_status.get('total_articles', 0)}",
        ])
        if db_status.get('latest_article'):
            lines.append(f"- Latest article: {db_status['latest_article']['title']}")

        # Add file system status
        fs_status = system_status.get('file_system', {})
        lines.extend([
            f"\n{EMOJIS['stats']} File System:",
            f"- JSON files: {fs_status.get('json_files', 0)}",
            f"- Log file: {'✅' if fs_status.get('log_file_exists') else '❌'}"
        ])

        # Add performance metrics
        if status == 'running':
            if self.start_time:
                elapsed_time = datetime.now() - self.start_time
                lines.append(f"\n{EMOJIS['time']} Running time: {str(elapsed_time).split('.')[0]}")

            if self.articles_per_minute > 0:
                lines.append(f"{EMOJIS['stats']} Speed: {self.articles_per_minute:.1f} articles/minute")
                remaining_articles = total - processed
                if remaining_articles > 0:
                    minutes_remaining = remaining_articles / self.articles_per_minute
                    lines.append(f"{EMOJIS['loading']} Est. time remaining: {int(minutes_remaining)} minutes")

        # Add current article info
        if progress_data.get('current_article'):
            current = progress_data['current_article']
            if current != self.last_article:
                self.last_article = current
                lines.extend([
                    f"\n{EMOJIS['article']} Current article:",
                    f"{EMOJIS['url']} {current}"
                ])

        # Add completion status
        if status == 'completed':
            lines.extend([
                f"\n{EMOJIS['success']} Scraping completed:",
                f"- Successful: {progress_data.get('successful_scrapes', 0)}",
                f"- Failed: {progress_data.get('failed_scrapes', 0)}",
                f"- Total time: {progress_data.get('elapsed_time', 'unknown')}"
            ])

        return "\n".join(lines)

def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")

def main():
    monitor = ProgressMonitor()

    print(f"\n🤖 Starting Charleston News Scraper Monitor...")
    print(f"{EMOJIS['warning']} Press Ctrl+C to stop")
    print(f"{EMOJIS['info']} Checking every 30 seconds to reduce API load")

    try:
        while True:
            if not monitor.check_health():
                print(f"\n{EMOJIS['error']} Flask application is not running!")
                time.sleep(30)
                continue

            clear_screen()
            progress = monitor.monitor_progress()
            if progress:
                print(progress)
                print(f"\n{EMOJIS['time']} Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{EMOJIS['loading']} Next check in 30 seconds...")

            time.sleep(30)

    except KeyboardInterrupt:
        print(f"\n{EMOJIS['completed']} Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n{EMOJIS['error']} Monitoring stopped due to error: {e}")

if __name__ == "__main__":
    main()
