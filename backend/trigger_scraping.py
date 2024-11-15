# trigger_scraping.py
import requests
import sys
import time

def check_server_status():
    """Check if the Flask server is running"""
    try:
        response = requests.get('http://127.0.0.1:5000/health')
        return response.status_code == 200
    except requests.RequestException:
        return False

def trigger_scraping():
    """Trigger the scraping process"""
    print("\n🔍 Checking server status...")

    if not check_server_status():
        print("❌ Error: Flask server is not running!")
        print("👉 Please start the server with:")
        print("   export FLASK_APP=app.py")
        print("   flask run")
        return False

    try:
        print("🚀 Starting scraping process...")
        response = requests.post('http://127.0.0.1:5000/api/start-scraping')

        if response.status_code == 200:
            print("✅ Scraping process started successfully!")
            print("\n📊 Monitor the progress by running:")
            print("python3 monitor.py")
            return True
        elif response.status_code == 409:
            print("⚠️  A scraping operation is already in progress")
            return False
        else:
            print(f"❌ Error: {response.json().get('message', 'Unknown error')}")
            return False

    except requests.RequestException as e:
        print(f"❌ Error connecting to server: {e}")
        return False

if __name__ == "__main__":
    if not trigger_scraping():
        sys.exit(1)

    # Keep the script running to show immediate progress
    print("\n⌛ Waiting for scraping to start...")
    time.sleep(2)

    # Show initial progress
    try:
        progress = requests.get('http://127.0.0.1:5000/api/scraping-progress')
        if progress.status_code == 200:
            data = progress.json()
            print(f"\n📈 Initial Status: {data.get('status', 'Unknown')}")
            print(f"📑 Articles found: {data.get('total_urls', 0)}")
    except:
        pass

    print("\n👉 Run 'python3 monitor.py' in a new terminal to see full progress")
