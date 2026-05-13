import sys
import os
import re
import requests
from bs4 import BeautifulSoup
import urllib.parse

def download_telegram_post(url):
    """
    Downloads media and text from a Telegram post URL
    Works with t.me links
    """
    
    print(f"🔗 Processing: {url}")
    print("=" * 50)
    
    # Create downloads folder
    os.makedirs("telegram_downloads", exist_ok=True)
    
    # Convert t.me to telegram embed for easier scraping
    if "t.me" in url:
        # Try to extract channel and message ID
        parts = url.replace("https://t.me/", "").replace("http://t.me/", "").split("/")
        
        if len(parts) >= 2:
            channel = parts[0]
            msg_id = parts[1]
            
            # Use Telegram's public preview
            embed_url = f"https://t.me/{channel}/{msg_id}?embed=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                response = requests.get(embed_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text content
                text_div = soup.find('div', class_='tgme_widget_message_text')
                if text_div:
                    text_content = text_div.get_text(strip=True)
                    print(f"📝 Text found: {text_content[:100]}...")
                    
                    # Save text
                    with open(f"telegram_downloads/{channel}_{msg_id}.txt", "w", encoding="utf-8") as f:
                        f.write(text_content)
                    print("✅ Text saved")
                
                # Find images
                images = soup.find_all('a', class_='tgme_widget_message_photo_wrap')
                for i, img in enumerate(images):
                    style = img.get('style', '')
                    url_match = re.search(r"url\('(.+?)'\)", style)
                    if url_match:
                        img_url = url_match.group(1)
                        download_file(img_url, f"telegram_downloads/{channel}_{msg_id}_image_{i+1}.jpg")
                
                # Find videos
                videos = soup.find_all('video')
                for i, video in enumerate(videos):
                    source = video.find('source')
                    if source and source.get('src'):
                        video_url = source.get('src')
                        download_file(video_url, f"telegram_downloads/{channel}_{msg_id}_video_{i+1}.mp4")
                
                # Find document links
                docs = soup.find_all('a', class_='tgme_widget_message_document_wrap')
                for i, doc in enumerate(docs):
                    doc_url = doc.get('href', '')
                    if doc_url:
                        download_file(doc_url, f"telegram_downloads/{channel}_{msg_id}_doc_{i+1}")
                
                print("\n✅ Download complete!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                sys.exit(1)
        else:
            print("❌ Invalid Telegram URL format")
            print("📌 Use format: https://t.me/channel_name/message_id")
            sys.exit(1)
    else:
        print("❌ Only t.me links are supported")
        sys.exit(1)

def download_file(url, filename):
    """Download a file from URL"""
    try:
        print(f"⬇️ Downloading: {filename}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size_mb = os.path.getsize(filename) / (1024 * 1024)
        print(f"✅ Downloaded: {filename} ({size_mb:.2f} MB)")
    except Exception as e:
        print(f"⚠️ Failed to download {filename}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ No URL provided")
        sys.exit(1)
    
    download_telegram_post(sys.argv[1])
