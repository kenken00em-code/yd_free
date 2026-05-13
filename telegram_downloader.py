#!/usr/bin/env python3
"""
Telegram Media Downloader
Downloads all files (exe, apk, txt, pdf, mp4, etc.) from Telegram posts
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from typing import Set, List, Dict

class TelegramDownloader:
    def __init__(self, channel: str, msg_id: str, backup_dir: str, folder_name: str):
        self.channel = channel
        self.msg_id = msg_id
        self.backup_dir = backup_dir
        self.folder_name = folder_name
        self.downloaded_files = []
        
    def download_file(self, url: str, filename: str = None) -> bool:
        """Download a file from URL"""
        try:
            if not filename:
                filename = url.split('/')[-1].split('?')[0]
                if not filename or '.' not in filename:
                    filename = f"file_{len(self.downloaded_files) + 1}.bin"
            
            # Clean filename
            filename = re.sub(r'[^\w\-_.]', '_', filename)
            
            filepath = os.path.join(self.backup_dir, self.folder_name, filename)
            
            print(f"⬇️ Downloading: {filename}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=300) as response:
                data = response.read()
                with open(filepath, 'wb') as f:
                    f.write(data)
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"✅ Downloaded: {filename} ({size_mb:.2f} MB)")
                self.downloaded_files.append(filename)
                return True
            else:
                print(f"❌ Failed: {filename} (empty file)")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading {filename}: {str(e)}")
            return False
    
    def download_from_api(self) -> bool:
        """Download files using Telegram API"""
        try:
            api_url = f"https://tg.i-c-a.su/json/{self.channel}/{self.msg_id}"
            print(f"📡 Fetching from API: {api_url}")
            
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Save text content
            text = data.get('text', '')
            if text:
                text_file = os.path.join(self.backup_dir, self.folder_name, 'message.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                print("✅ Text content saved")
            
            # Download documents (exe, apk, pdf, zip, etc.)
            documents = data.get('document', [])
            if documents:
                print(f"📁 Found {len(documents)} document(s)")
                for doc in documents:
                    filename = doc.get('file_name', f"document_{doc.get('id', 'unknown')}")
                    download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.msg_id}/{filename}"
                    self.download_file(download_url, filename)
            
            # Download videos
            videos = data.get('video', [])
            if videos:
                print(f"🎬 Found {len(videos)} video(s)")
                for idx, video in enumerate(videos):
                    filename = video.get('file_name', f"video_{idx+1}.mp4")
                    download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.msg_id}/{filename}"
                    self.download_file(download_url, filename)
            
            # Download photos
            photos = data.get('photo', [])
            if photos:
                print(f"🖼️ Found {len(photos)} photo(s)")
                for idx, photo in enumerate(photos):
                    filename = f"photo_{idx+1}.jpg"
                    download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.msg_id}/{filename}"
                    self.download_file(download_url, filename)
            
            # Download audio files
            audio_files = data.get('audio', [])
            if audio_files:
                print(f"🎵 Found {len(audio_files)} audio file(s)")
                for idx, audio in enumerate(audio_files):
                    filename = audio.get('file_name', f"audio_{idx+1}.mp3")
                    download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.msg_id}/{filename}"
                    self.download_file(download_url, filename)
            
            # Download animations/gifs
            animations = data.get('animation', [])
            if animations:
                print(f"🎞️ Found {len(animations)} animation(s)")
                for idx, anim in enumerate(animations):
                    filename = anim.get('file_name', f"animation_{idx+1}.gif")
                    download_url = f"https://tg.i-c-a.su/dl/{self.channel}/{self.msg_id}/{filename}"
                    self.download_file(download_url, filename)
            
            return len(self.downloaded_files) > 0
            
        except Exception as e:
            print(f"⚠️ API method failed: {str(e)}")
            return False
    
    def download_from_html(self) -> bool:
        """Fallback: Extract and download files from HTML"""
        try:
            url = f"https://t.me/{self.channel}/{self.msg_id}?embed=1"
            print(f"📄 Fetching HTML: {url}")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')
            
            # Pattern for common file extensions
            extensions = r'(exe|apk|zip|rar|7z|tar|gz|bz2|pdf|doc|docx|xls|xlsx|ppt|pptx|txt|md|mp4|mp3|wav|flac|avi|mkv|mov|wmv|flv|webm|jpg|jpeg|png|gif|bmp|webp|svg|ico|ttf|otf|woff|woff2|css|js|html|htm|xml|json|sql|py|java|cpp|c|h|rb|go|php|swift|kt|rs|sh|bat|ps1|vbs|pl|pm|r|m|matlab|scss|less|sass|yml|yaml|toml|ini|cfg|conf|log|csv|tsv|ics|vcf|torrent|iso|img|dmg|pkg|deb|rpm|msi|appimage|bin|dat|db|sqlite|bak|old|tmp|swp|lock|part|crdownload|download)'
            
            # Find all file URLs
            pattern = rf'https?://[^"\'\s<>]+\.{extensions}(?:\?[^"\'\s<>]*)?'
            urls = re.findall(pattern, html, re.IGNORECASE)
            
            # Also look for telegram CDN links
            cdn_pattern = r'https?://cdn[^"\'\s<>]+\.\w+'
            urls.extend(re.findall(cdn_pattern, html))
            
            # Also look for href attributes
            href_pattern = r'href="([^"]+\.(?:' + extensions + r'))'
            urls.extend(re.findall(href_pattern, html, re.IGNORECASE))
            
            # Remove duplicates
            urls = list(set(urls))
            
            if urls:
                print(f"🔍 Found {len(urls)} file links in HTML")
                for url in urls:
                    self.download_file(url)
                return len(self.downloaded_files) > 0
            else:
                print("⚠️ No file links found in HTML")
                return False
                
        except Exception as e:
            print(f"⚠️ HTML parsing failed: {str(e)}")
            return False
    
    def download_from_main_page(self) -> bool:
        """Try downloading from main page (non-embed)"""
        try:
            url = f"https://t.me/{self.channel}/{self.msg_id}"
            print(f"📄 Fetching main page: {url}")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')
            
            # Look for media URLs
            patterns = [
                r'https://[^"]+\.(?:mp4|mkv|avi|mov|webm)',
                r'https://[^"]+\.(?:jpg|jpeg|png|gif|webp)',
                r'https://[^"]+\.(?:exe|apk|zip|rar|pdf|docx?)',
                r'data-video="([^"]+)"',
                r'src="([^"]+)"'
            ]
            
            all_urls = set()
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                all_urls.update(matches)
            
            if all_urls:
                print(f"🔍 Found {len(all_urls)} potential media links")
                for url in all_urls:
                    if url.startswith('http'):
                        self.download_file(url)
                return len(self.downloaded_files) > 0
            else:
                print("⚠️ No media links found in main page")
                return False
                
        except Exception as e:
            print(f"⚠️ Main page parsing failed: {str(e)}")
            return False
    
    def create_readme(self):
        """Create README.md with download information"""
        readme_path = os.path.join(self.backup_dir, self.folder_name, "README.md")
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# 📩 Telegram Download: {self.channel}/{self.msg_id}\n\n")
            f.write("## 📋 Information\n")
            f.write(f"- **Channel:** @{self.channel}\n")
            f.write(f"- **Message ID:** {self.msg_id}\n")
            f.write(f"- **Download Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write("## 📁 Downloaded Files\n\n")
            
            if self.downloaded_files:
                for file in sorted(self.downloaded_files):
                    file_path = os.path.join(self.backup_dir, self.folder_name, file)
                    if os.path.exists(file_path):
                        size_bytes = os.path.getsize(file_path)
                        size_mb = size_bytes / (1024 * 1024)
                        f.write(f"- **{file}** ({size_mb:.2f} MB)\n")
            else:
                f.write("*No files were downloaded*\n")
            
            f.write("\n## 🔗 Access Files\n\n")
            f.write(f"Files are available in the `telegram_downloads/{self.folder_name}/` directory\n")
        
        print(f"✅ README created at {readme_path}")
    
    def run(self):
        """Main execution method"""
        print(f"\n🚀 Starting download for @{self.channel}/{self.msg_id}")
        print(f"📁 Target folder: {self.folder_name}\n")
        
        # Create folder
        os.makedirs(os.path.join(self.backup_dir, self.folder_name), exist_ok=True)
        
        # Try different methods
        success = False
        
        # Method 1: API
        if self.download_from_api():
            success = True
        
        # Method 2: HTML parsing
        if not success:
            print("\n🔄 Trying HTML extraction method...")
            if self.download_from_html():
                success = True
        
        # Method 3: Main page
        if not success:
            print("\n🔄 Trying main page extraction...")
            if self.download_from_main_page():
                success = True
        
        # Create README
        self.create_readme()
        
        # Summary
        print(f"\n" + "="*50)
        if self.downloaded_files:
            print(f"✅ Successfully downloaded {len(self.downloaded_files)} file(s)!")
            for file in self.downloaded_files:
                print(f"   📄 {file}")
        else:
            print("⚠️ No files were downloaded. The post might not contain any downloadable media.")
        print("="*50)
        
        return len(self.downloaded_files)

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 telegram_downloader.py <channel> <msg_id> <backup_dir> <folder_name>")
        sys.exit(1)
    
    channel = sys.argv[1]
    msg_id = sys.argv[2]
    backup_dir = sys.argv[3]
    folder_name = sys.argv[4]
    
    downloader = TelegramDownloader(channel, msg_id, backup_dir, folder_name)
    file_count = downloader.run()
    
    # Save file count to a temp file for the next step
    with open('/tmp/downloaded_files_count.txt', 'w') as f:
        f.write(str(file_count))
    
    sys.exit(0 if file_count > 0 else 1)

if __name__ == "__main__":
    main()
