# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging
from typing import List, Dict, Optional
import os

class ScrapingProgress:
    def __init__(self):
        self.total_urls = 0
        self.processed_urls = 0
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        self.current_article = None
        self.start_time = None
        self.end_time = None
        self.status = 'idle'  # idle, running, completed, error
        self.error_message = None
        self.last_scraped_articles = []

    def to_dict(self):
        return {
            'status': self.status,
            'total_urls': self.total_urls,
            'processed_urls': self.processed_urls,
            'successful_scrapes': self.successful_scrapes,
            'failed_scrapes': self.failed_scrapes,
            'current_article': self.current_article,
            'progress_percentage': (self.processed_urls / self.total_urls * 100) if self.total_urls > 0 else 0,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'elapsed_time': str(self.end_time - self.start_time) if (self.end_time and self.start_time) else None,
            'error_message': self.error_message,
            'last_scraped_articles': self.last_scraped_articles[-5:]  # Last 5 articles
        }

class CharlestonNewsScraper:
    def __init__(self):
        self.base_url = "https://www.milb.com/charleston/news"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.setup_logging()
        self.progress = ScrapingProgress()

    def scrape_all_articles(self) -> List[Dict]:
        """Scrapes all articles from the news page"""
        try:
            self.progress = ScrapingProgress()  # Reset progress
            self.progress.status = 'running'
            self.progress.start_time = datetime.now()

            # Get URLs first
            urls = self.get_article_urls()
            self.progress.total_urls = len(urls)

            if not urls:
                self.logger.error("No article URLs found")
                self.progress.status = 'error'
                self.progress.error_message = "No article URLs found"
                return []

            self.logger.info(f"Starting to scrape {len(urls)} articles")
            articles = []

            for i, url in enumerate(urls, 1):
                try:
                    self.progress.current_article = url
                    self.logger.info(f"Scraping article {i}/{len(urls)}: {url}")

                    article = self.scrape_article(url)

                    if article and article.get('title') and article.get('content'):
                        articles.append(article)
                        self.progress.successful_scrapes += 1
                        self.progress.last_scraped_articles.append({
                            'title': article['title'],
                            'url': url,
                            'timestamp': datetime.now().isoformat()
                        })
                        self.logger.info(f"Successfully scraped: {article['title']}")
                    else:
                        self.progress.failed_scrapes += 1
                        self.logger.warning(f"Failed to scrape article: {url}")

                    self.progress.processed_urls += 1

                except Exception as e:
                    self.progress.failed_scrapes += 1
                    self.progress.processed_urls += 1
                    self.logger.error(f"Error scraping article {url}: {e}")

                # Be nice to the server
                time.sleep(1)

            self.progress.status = 'completed'
            self.progress.end_time = datetime.now()

            self.logger.info(f"""
    Scraping completed:
    - Total articles found: {len(urls)}
    - Successfully scraped: {self.progress.successful_scrapes}
    - Failed scrapes: {self.progress.failed_scrapes}
    - Time taken: {self.progress.end_time - self.progress.start_time}
            """)

            return articles

        except Exception as e:
            self.progress.status = 'error'
            self.progress.error_message = str(e)
            self.logger.error(f"Error in scrape_all_articles: {e}")
            return []

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('CharlestonNewsScraper')

    def get_article_urls(self) -> List[str]:
        """Scrapes all article URLs from the news page"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            article_links = []
            articles = soup.find_all('a', href=lambda x: x and '/charleston/news/' in x)

            for article in articles:
                url = f"https://www.milb.com{article['href']}"
                if url not in article_links:
                    article_links.append(url)

            self.logger.info(f"Found {len(article_links)} article URLs")
            return article_links

        except requests.Timeout:
            self.logger.error("Timeout while fetching article URLs")
            return []
        except requests.RequestException as e:
            self.logger.error(f"Error fetching article URLs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching article URLs: {e}")
            return []

    def extract_images(self, article_data: Dict) -> List[Dict]:
        """Extracts image information from article data"""
        images = []
        try:
            # Extract main image
            if 'media' in article_data and article_data['media'].get('content', {}).get('cuts'):
                for cut in article_data['media']['content']['cuts']:
                    images.append({
                        'url': cut.get('src', ''),
                        'width': cut.get('width', ''),
                        'aspect_ratio': cut.get('aspectRatio', ''),
                        'type': 'main'
                    })

            # Extract thumbnail
            if 'thumbnail' in article_data and article_data['thumbnail'].get('image', {}).get('cuts'):
                for cut in article_data['thumbnail']['image']['cuts']:
                    images.append({
                        'url': cut.get('src', ''),
                        'width': cut.get('width', ''),
                        'aspect_ratio': cut.get('aspectRatio', ''),
                        'type': 'thumbnail'
                    })
        except Exception as e:
            self.logger.error(f"Error extracting images: {e}")

        return images

    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrapes content from a single article URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            article_data = None

            # Method 1: Look for article-json in scripts
            for script in soup.find_all('script'):
                if script.string and 'window.MiLB_ARTICLES' in script.string:
                    try:
                        self.logger.debug(f"Found script with MiLB_ARTICLES: {script.string[:200]}...")

                        if 'article-json=' in script.string:
                            json_str = script.string.split('article-json=')[1].strip()[1:-2]
                        elif 'articlePage:' in script.string:
                            json_str = script.string.split('articlePage:')[1].split(',')[0].strip()
                        else:
                            continue

                        article_data = json.loads(json_str)
                        break
                    except Exception as e:
                        self.logger.debug(f"Failed to parse script JSON: {e}")
                        continue

            # Method 2: Direct HTML parsing if JSON not found
            if not article_data:
                # Find main article content
                article_content = soup.find('div', class_='article-item__bottom')
                article_text = ''

                if article_content:
                    # Get all text paragraphs from the article
                    paragraphs = article_content.find_all('p')
                    article_text = '\n'.join([p.get_text(strip=True) for p in paragraphs])

                # Get article metadata
                article_meta = soup.find('div', class_='article-item__meta-container')
                date = ''
                author = ''

                if article_meta:
                    date_element = article_meta.find('div', class_='article-item__contributor-date')
                    if date_element:
                        date = date_element.get_text(strip=True)

                    author_element = article_meta.find('div', class_='article-item__contributor-info')
                    if author_element:
                        author = author_element.get_text(strip=True)

                # Get title
                title_element = soup.find('h1', class_='article-item__headline')
                title = title_element.get_text(strip=True) if title_element else ''

                article = {
                    'title': title,
                    'subheadline': '',
                    'date': date,
                    'content': article_text,
                    'url': url,
                    'images': [],
                    'section': 'news',
                    'tags': {
                        'topics': [],
                        'teams': ['Charleston RiverDogs'],
                        'players': [],
                        'contributors': [author] if author else [],
                        'leagues': ['Carolina League']
                    },
                    'social_shares': {
                        'facebook': '',
                        'twitter': '',
                    },
                    'author': {'name': author} if author else {},
                    'last_updated': datetime.now().isoformat()
                }

                # Extract images
                for img in soup.find_all('img'):
                    if img.get('src'):
                        article['images'].append({
                            'url': img['src'],
                            'width': img.get('width', ''),
                            'aspect_ratio': '',
                            'type': 'main'
                        })

                if article['title'] and article['content']:
                    return article

            # If we found JSON data, process it
            if article_data:
                article = self._process_article_json(article_data, url)

                # Enhance with HTML content if available
                article_content = soup.find('div', class_='article-item__bottom')
                if article_content:
                    paragraphs = article_content.find_all('p')
                    html_content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
                    if html_content.strip():
                        article['content'] = html_content

                return article

            self.logger.warning(f"No article data found for {url}")
            return None

        except requests.Timeout:
            self.logger.error(f"Timeout while scraping article {url}")
            return None
        except requests.RequestException as e:
            self.logger.error(f"Error scraping article {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing article JSON from {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing article {url}: {e}")
            return None

    def _process_article_json(self, article_data: Dict, url: str) -> Dict:
        """Process JSON article data into standardized format"""
        article = {
            'title': article_data.get('headline', ''),
            'subheadline': article_data.get('subHeadline', ''),
            'date': article_data.get('timestamp', ''),
            'content': '',
            'url': url,
            'images': self.extract_images(article_data),
            'section': article_data.get('section', ''),
            'tags': {
                'topics': article_data.get('tags', {}).get('topics', []),
                'teams': article_data.get('tags', {}).get('teams', []),
                'players': article_data.get('tags', {}).get('players', []),
                'contributors': article_data.get('tags', {}).get('contributors', []),
                'leagues': article_data.get('tags', {}).get('leagues', [])
            },
            'social_shares': {
                'facebook': article_data.get('social', {}).get('facebook', ''),
                'twitter': article_data.get('social', {}).get('twitter', ''),
            },
            'author': article_data.get('byline', {}),
            'last_updated': datetime.now().isoformat()
        }

        # Extract content
        content_parts = article_data.get('articleParts', [])
        for part in content_parts:
            if part.get('type') == 'markdown':
                article['content'] += part.get('content', '')

        # Clean up content
        if article['content']:
            soup = BeautifulSoup(article['content'], 'html.parser')
            article['content'] = soup.get_text(separator=' ').strip()

        return article

    def save_articles(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """Saves scraped articles to a JSON file"""
        if filename is None:
            filename = f"charleston_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(articles)} articles to {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error saving articles to {filename}: {e}")
            raise
