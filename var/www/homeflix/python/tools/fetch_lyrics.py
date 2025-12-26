#!/usr/bin/env python3
import requests
import os
import re
import sys
from bs4 import BeautifulSoup

def fetch_album_lyrics(album_path):
    API_TOKEN = "-NvDJdTBHnGuB_DufRrxtWMXEtfi8hvez35Gz09VUVJlgNGoj68DWNSyIreL9eEK"
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    }
    
    # Extract artist from main card.yaml
    main_card = os.path.join(album_path, "card.yaml")
    with open(main_card, 'r') as f:
        main_content = f.read()
    
    performer_match = re.search(r'performer:\s*(.+)', main_content)
    artist = performer_match.group(1).strip()
    print(f"Artist: {artist}")
    
    # Get track directories
    track_dirs = [d for d in os.listdir(album_path) if d.isdigit() and len(d) == 2]
    track_dirs.sort()
    
    for track_num in track_dirs:
        card_file = os.path.join(album_path, track_num, "card.yaml")
        
        if os.path.exists(card_file):
            with open(card_file, 'r') as f:
                content = f.read()
            
            title_match = re.search(r'titles:\s*\n\s*en:\s*(.+)', content)
            if title_match:
                track_title = title_match.group(1).strip()
                
                try:
                    print(f"Fetching lyrics for: {track_title}")
                    
                    # Search for song
                    search_url = "https://api.genius.com/search"
                    params = {'q': f"{artist} {track_title}"}
                    
                    response = requests.get(search_url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        hits = data.get('response', {}).get('hits', [])
                        
                        if hits:
                            song_url = hits[0]['result']['url']
                            song_id = hits[0]['result']['id']
                            
                            # Try to get lyrics from song page
                            song_response = requests.get(song_url, headers=headers)
                            
                            if song_response.status_code == 200:
                                soup = BeautifulSoup(song_response.text, 'html.parser')
                                
                                # Look for lyrics in various possible containers
                                lyrics_divs = soup.find_all('div', {'data-lyrics-container': 'true'})
                                if not lyrics_divs:
                                    lyrics_divs = soup.find_all('div', class_=re.compile(r'lyrics|Lyrics'))
                                
                                if lyrics_divs:
                                    # Extract text from all lyrics containers and combine
                                    all_lyrics_text = []
                                    for div in lyrics_divs:
                                        lyrics_text = div.get_text(separator='\n').strip()
                                        if lyrics_text:
                                            all_lyrics_text.append(lyrics_text)
                                    
                                    combined_lyrics = '\n'.join(all_lyrics_text)
                                    
                                    if combined_lyrics and len(combined_lyrics) > 50:  # Basic validation
                                        # Check if it's an instrumental track
                                        if "this song is an instrumental" in combined_lyrics.lower():
                                            # Handle instrumental track
                                            lyrics_section = "lyrics:\n  en: |\n"
                                            
                                            # Update sounds to empty array for instrumental
                                            content = re.sub(r'sounds:\s*\n\s*-\s*en', 'sounds: []', content)
                                            
                                            # Replace lyrics section
                                            content = re.sub(r'lyrics:.*?(?=\n\w)', lyrics_section, content, flags=re.DOTALL)
                                            
                                            with open(card_file, 'w') as f:
                                                f.write(content)
                                            
                                            print(f"🎵 Updated {track_num}/card.yaml - instrumental track")
                                            continue
                                        # Clean up lyrics
                                        lines = combined_lyrics.split('\n')
                                        cleaned_lines = []
                                        lyrics_started = False
                                        
                                        for line in lines:
                                            line = line.strip()
                                            
                                            # Skip header lines and descriptions
                                            if (line.endswith('Contributors') or 
                                                line.endswith('Lyrics') or
                                                'Read More' in line or
                                                line.startswith('You might also like') or
                                                'is Depeche Mode' in line or
                                                'single' in line.lower() and ('chart' in line.lower() or 'peak' in line.lower()) or
                                                'album' in line.lower() and 'track' in line.lower() or
                                                line.startswith('"') and line.endswith('…') or
                                                not line):
                                                continue
                                            
                                            # Start collecting lyrics when we hit a verse/chorus marker or actual lyrics
                                            if (line.startswith('[') and line.endswith(']')) or lyrics_started:
                                                lyrics_started = True
                                                cleaned_lines.append(line)
                                            # Also start if line looks like actual lyrics (not description)
                                            elif not any(word in line.lower() for word in ['single', 'chart', 'peak', 'album', 'track', 'group', 'band']):
                                                lyrics_started = True
                                                cleaned_lines.append(line)
                                        
                                        # Add spacing between sections
                                        formatted_lines = []
                                        for i, line in enumerate(cleaned_lines):
                                            if line.startswith('[') and line.endswith(']') and i > 0:
                                                formatted_lines.append('')  # Add empty line before sections
                                            formatted_lines.append(line)
                                        
                                        # Format for YAML
                                        lyrics_section = "lyrics:\n  en: |\n"
                                        for line in formatted_lines:
                                            if line == '':  # Empty line should be truly empty
                                                lyrics_section += "\n"
                                            else:
                                                lyrics_section += f"    {line}\n"
                                        
                                        # Replace lyrics section
                                        content = re.sub(r'lyrics:.*?(?=\n\w)', lyrics_section, content, flags=re.DOTALL)
                                        
                                        with open(card_file, 'w') as f:
                                            f.write(content)
                                        
                                        print(f"✅ Updated {track_num}/card.yaml with lyrics")
                                    else:
                                        print(f"⚠️  Could not extract lyrics from page for: {track_title}")
                                        print(f"   URL: {song_url}")
                                else:
                                    print(f"⚠️  No lyrics container found for: {track_title}")
                                    print(f"   URL: {song_url}")
                            else:
                                print(f"❌ Could not access song page for: {track_title}")
                        else:
                            print(f"❌ No search results for: {track_title}")
                    else:
                        print(f"❌ API error for {track_title}: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error fetching lyrics for {track_title}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 fetch_lyrics_working.py '/path/to/album/folder'")
        sys.exit(1)
    
    album_path = sys.argv[1]
    fetch_album_lyrics(album_path)
