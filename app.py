from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
import os

app = Flask(__name__)
PORT = int(os.getenv('PORT', '1200'))

@app.route('/api/lyrics', methods=['GET'])
def get_lyrics():
    search_query = request.args.get('q')
    
    if not search_query:
        return jsonify({
            'creator': 'Chamod Nimsara',
            'error': 'Please provide a search query with the "q" parameter'
        }), 400
    
    try:
        search_url = f"https://genius.com/api/search/multi?per_page=5&q={quote(search_query)}"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
        }
        
        search_response = requests.get(search_url, headers=headers)
        search_response.raise_for_status()
        response_data = search_response.json()
        
        song_result = None
        for section in response_data['response']['sections']:
            if section['type'] in ['song', 'lyric'] and section.get('hits'):
                for hit in section['hits']:
                    if hit['type'] in ['song', 'lyric']:
                        song_result = hit['result']
                        break
                if song_result:
                    break
        
        if not song_result:
            return jsonify({
                'creator': 'Chamod Nimsara',
                'error': 'No song found matching your query'
            }), 404
        
        artist_name = song_result.get('artist_names')
        song_title = song_result.get('title')
        song_url = song_result.get('url')
        image_url = song_result.get('header_image_url')
        api_path = song_result.get('api_path')
        
        if not song_url:
            return jsonify({
                'creator': 'Chamod Nimsara',
                'error': "Couldn't find lyrics URL for this song"
            }), 404
        
        # Optional view count update
        if api_path:
            song_id = api_path.split('/')[-1]
            try:
                requests.post(
                    f'https://genius.com/api/songs/{song_id}/count_view',
                    json={},
                    headers={
                        'accept': '*/*',
                        'referer': song_url,
                        'user-agent': 'Mozilla/5.0'
                    }
                )
            except Exception:
                pass
        
        # Get lyrics content
        lyrics_page = requests.get(song_url).text
        soup = BeautifulSoup(lyrics_page, 'html.parser')
        
        lyrics_divs = soup.select('#lyrics-root > div[data-lyrics-container="true"]')
        lyrics_text = ""
        for div in lyrics_divs:
            verse_html = str(div).replace('<br/>', '\n')
            verse_text = BeautifulSoup(verse_html, 'html.parser').get_text().strip()
            if verse_text:
                lyrics_text += verse_text + "\n\n"
        
        cleaned_lyrics = re.sub(r'^[\s\S]*?(\[Verse 1\])', r'\1', lyrics_text).strip()
        
        return jsonify({
            'creator': 'Chamod Nimsara',
            'title': song_title,
            'artist': artist_name,
            'link': song_url,
            'image': image_url,
            'lyrics': cleaned_lyrics
        })
        
    except Exception as error:
        print(f'Lyrics fetch error: {str(error)}')
        return jsonify({
            'creator': 'Chamod Nimsara',
            'error': "Failed to fetch lyrics",
            'details': str(error)
        }), 500

@app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>🎵 Genius Lyrics API - Chamod Nimsara</title>
        <style>
            body {
                background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                color: white;
                font-family: 'Poppins', sans-serif;
                text-align: center;
                padding: 50px;
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(90deg, #00dbde, #fc00ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p {
                font-size: 1.1em;
                color: #ddd;
            }
            code {
                background: rgba(255,255,255,0.1);
                padding: 5px 8px;
                border-radius: 6px;
                color: #00dbde;
            }
            a {
                color: #00dbde;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
            footer {
                margin-top: 40px;
                font-size: 0.9em;
                color: #aaa;
            }
        </style>
    </head>
    <body>
        <h1>🎵 Genius Lyrics API</h1>
        <p>Search for song lyrics easily using this simple API.</p>
        <p>Example usage:</p>
        <p><code>/api/lyrics?q=Dynasty MIIA</code></p>
        <p>Try it now 👉 <a href="/api/lyrics?q=Dynasty MIIA">View Example</a></p>
        <footer>Developed by <b>Chamod Nimsara</b> 💻 | WhiteShadow™</footer>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
