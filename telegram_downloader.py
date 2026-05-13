#!/usr/bin/env python3
"""
Telegram File Downloader
Extracted from av6387/all-in-one-download-telegram-bot
Downloads all file types (exe, apk, txt, pdf, etc.) from Telegram posts
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
import ssl
from html.parser import HTMLParser
from typing import List, Dict, Optional

class TelegramFileDownloader:
    """Core downloader extracted from the Telegram bot"""
    
    def __init__(self, channel: str, message_id: str, output_dir: str):
        self.channel = channel
        self.message_id = message_id
        self.output_dir = output_dir
        self.downloaded_files = []
        
    def download_telegram_file(self, file_url: str, file_name: str) -> bool:
        """Download a file from Telegram CDN"""
        try:
            file_path = os.path.join(self.output_dir, file_name)
            
            # Create request with proper headers (extracted from bot's code)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            req = urllib.request.Request(file_url, headers=headers)
            
            # Download with progress tracking
            with urllib.request.urlopen(req, timeout=300) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress indicator
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r  Progress: {percent:.1f}% ({downloaded//1024}/{total_size//1024} KB)", end='')
                
            print()  # New line after progress
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"✅ Downloaded: {file_name} ({size_mb:.2f} MB)")
                self.downloaded_files.append(file_name)
                return True
            else:
                print(f"❌ Failed: {file_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading {file_name}: {str(e)}")
            return False
    
    def extract_from_telegram_post(self) -> List[Dict]:
        """Extract all downloadable files from a Telegram post (method from bot)"""
        files = []
        
        # First try: Telegram's embed API (like bot does)
        embed_url = f"https://t.me/{self.channel}/{self.message_id}?embed=1"
        print(f"📡 Fetching embed: {embed_url}")
        
        try:
            req = urllib.request.Request(embed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                html_content = response.read().decode('utf-8')
                
                # Look for all file types (extracted from bot's patterns)
                patterns = [
                    # Telegram CDN links
                    r'https://cdn[^"\']+\.(exe|apk|zip|rar|7z|pdf|doc|docx|xls|xlsx|txt|mp4|mp3|jpg|jpeg|png|gif|webm|mkv|avi|mov|bin|dmg|iso|img|msi|deb|rpm|sh|bat|ps1|py|js|html|css|json|xml|sql|db|csv|log|ini|cfg|conf|yaml|yml|toml)',
                    
                    # Direct file links
                    r'href="(https://t\.me/[^"]+\.(exe|apk|zip|rar|7z|pdf|doc|docx|xls|xlsx|txt|mp4|mp3|jpg|jpeg|png|gif|webm|mkv|avi|mov))"',
                    
                    # Media files
                    r'<a[^>]+href="([^"]+\.(mp4|mkv|avi|mov|webm))"[^>]*>',
                    r'<source src="([^"]+\.(mp4|webm|mkv))"',
                    
                    # Document links
                    r'<a[^>]+href="([^"]+\.(exe|apk|zip|rar|7z|pdf|doc|docx|xls|xlsx|txt))"[^>]*>',
                    
                    # Images
                    r'<img[^>]+src="([^"]+\.(jpg|jpeg|png|gif|webp))"',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        url = match if isinstance(match, str) else match[0]
                        if url.startswith('http'):
                            # Extract filename
                            filename = url.split('/')[-1].split('?')[0]
                            if not filename or '.' not in filename:
                                filename = f"file_{len(files)+1}.bin"
                            
                            files.append({
                                'url': url,
                                'name': filename
                            })
                            
        except Exception as e:
            print(f"⚠️ Embed extraction failed: {str(e)}")
        
        return files
    
    def use_telegram_api(self) -> List[Dict]:
        """Use Telegram's API to get file info (like the bot does)"""
        files = []
        
        # Try multiple public Telegram APIs (from the bot's config)
        apis = [
            f"https://tg.i-c-a.su/json/{self.channel}/{self.message_id}",
            f"https://api.telegram.org/botDUMMY/getUpdates",  # Will fail, but pattern matters
        ]
        
        for api_url in apis:
            try:
                print(f"📡 Trying API: {api_url}")
                req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # Extract documents
                    if 'document' in data and data['document']:
                        for doc in data['document']:
                            if 'file_name' in doc:
                                download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.message_id}/{doc['file_name']}"
                                files.append({
                                    'url': download_url,
                                    'name': doc['file_name']
                                })
                    
                    # Extract videos
                    if 'video' in data and data['video']:
                        for idx, video in enumerate(data['video']):
                            name = video.get('file_name', f"video_{idx+1}.mp4")
                            download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.message_id}/{name}"
                            files.append({'url': download_url, 'name': name})
                    
                    # Extract audio
                    if 'audio' in data and data['audio']:
                        for idx, audio in enumerate(data['audio']):
                            name = audio.get('file_name', f"audio_{idx+1}.mp3")
                            download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.message_id}/{name}"
                            files.append({'url': download_url, 'name': name})
                    
                    if files:
                        break  # Success, stop trying APIs
                        
            except Exception as e:
                print(f"⚠️ API {api_url} failed: {str(e)}")
                continue
        
        return files
    
    def download_all_files(self):
        """Main method to download all files"""
        print(f"\n🚀 Starting download from @{self.channel}/{self.message_id}")
        print(f"📁 Output: {self.output_dir}\n")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Method 1: Try API first
        print("🔍 Method 1: Trying Telegram API...")
        files = self.use_telegram_api()
        
        # Method 2: Try HTML extraction
        if not files:
            print("\n🔍 Method 2: Trying HTML extraction...")
            files = self.extract_from_telegram_post()
        
        # Method 3: Direct page download (fallback)
        if not files:
            print("\n🔍 Method 3: Trying direct page download...")
            try:
                page_url = f"https://t.me/{self.channel}/{self.message_id}"
                req = urllib.request.Request(page_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    html = response.read().decode('utf-8')
                    
                    # Generic file pattern
                    generic_pattern = r'https://[^"\']+\.(exe|apk|zip|rar|7z|pdf|doc|docx|xls|xlsx|txt|mp4|mp3|jpg|jpeg|png|gif|webm|mkv|avi|mov)'
                    urls = re.findall(generic_pattern, html, re.IGNORECASE)
                    
                    for url in urls:
                        filename = url.split('/')[-1].split('?')[0]
                        files.append({'url': url, 'name': filename})
            except Exception as e:
                print(f"⚠️ Direct page failed: {str(e)}")
        
        # Download all found files
        if files:
            # Remove duplicates
            unique_files = []
            seen_urls = set()
            for file in files:
                if file['url'] not in seen_urls:
                    seen_urls.add(file['url'])
                    unique_files.append(file)
            
            print(f"\n📁 Found {len(unique_files)} file(s) to download\n")
            
            for file in unique_files:
                print(f"📥 Downloading: {file['name']}")
                self.download_telegram_file(file['url'], file['name'])
                time.sleep(1)  # Small delay between downloads
        else:
            print("\n⚠️ No downloadable files found in this Telegram post")
        
        # Summary
        print("\n" + "="*50)
        if self.downloaded_files:
            print(f"✅ Successfully downloaded {len(self.downloaded_files)} file(s)!")
            for f in self.downloaded_files:
                print(f"   📄 {f}")
        else:
            print("❌ No files were downloaded")
        print("="*50)
        
        return len(self.downloaded_files)

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 telegram_downloader.py <channel> <message_id> <output_dir>")
        print("Example: python3 telegram_downloader.py mychannel 123 ./downloads")
        sys.exit(1)
    
    channel = sys.argv[1]
    message_id = sys.argv[2]
    output_dir = sys.argv[3]
    
    downloader = TelegramFileDownloader(channel, message_id, output_dir)
    file_count = downloader.download_all_files()
    
    # Save results for GitHub Actions workflow
    with open('/tmp/downloaded_files_count.txt', 'w') as f:
        f.write(str(file_count))
    
    sys.exit(0 if file_count > 0 else 1)

if __name__ == "__main__":
    main()
