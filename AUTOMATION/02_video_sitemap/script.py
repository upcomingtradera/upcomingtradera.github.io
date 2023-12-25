import re
import os
import sys
import json
import hashlib
import requests

# Check if YT_CLIENT_SECRET is set
if 'YT_API_KEY' not in os.environ:
    print("Error: YT_API_KEY environment variable is not set.")
    exit(1)

API_KEY = os.environ.get('YT_API_KEY')

# Absolute paths for data and content directories
CONTENT_DIR = '/home/bb/Documents/upcomingtrader_blog/content/'
DATA_DIR = '/home/bb/Documents/upcomingtrader_blog/data/videos'

# HUGO_CONTENT_URL_BASE = "https://www.upcomingtrader.com/"
HUGO_CONTENT_URL_BASE = ""
YOUTUBE_VIDEO_API_URL = "https://www.googleapis.com/youtube/v3/videos?id={}&key={}&part=snippet,contentDetails"
YOUTUBE_PLAYLIST_API_URL = "https://www.googleapis.com/youtube/v3/playlists?id={}&key={}&part=snippet"
YOUTUBE_PLAYLIST_ITEMS_API_URL = "https://www.googleapis.com/youtube/v3/playlistItems?playlistId={}&key={}&part=snippet"


if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def fetch_video_details(video_id, is_playlist=False):
    api_url = YOUTUBE_PLAYLIST_API_URL.format(video_id, API_KEY) if is_playlist else YOUTUBE_VIDEO_API_URL.format(video_id, API_KEY)
    # print(api_url)
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        if data.get('items'):
            return data
        else:
            print(f"No data returned for {'playlist' if is_playlist else 'video'} ID: {video_id}")
            return None

def fetch_playlist_details(playlist_id):
    api_url = YOUTUBE_PLAYLIST_API_URL.format(playlist_id, API_KEY)
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    sys.exit(1)

def fetch_playlist_items(playlist_id):
    api_url = YOUTUBE_PLAYLIST_ITEMS_API_URL.format(playlist_id, API_KEY)
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    sys.exit(1)


def process_video_data(video_data, file_path):
    # Extract necessary data
    snippet = video_data['items'][0]['snippet']
    content_details = video_data['items'][0]['contentDetails']

    contentUrl = f"https://www.youtube.com/watch?v={video_id}"
    embedUrl = f"https://www.youtube.com/embed/{video_id}"

    hugo_data = {
        "video_id": video_id,
        "title": snippet['title'],
        "description": snippet['description'],
        "thumbnail": snippet['thumbnails']['default']['url'],
        "uploadDate": snippet['publishedAt'],
        "duration": content_details['duration'],
        "contentUrl": contentUrl,
        "embedUrl": embedUrl,
        # "url": HUGO_CONTENT_URL_BASE + file_path.replace(CONTENT_DIR, '').replace('.md', '/'),  # Assuming the file structure mirrors the URL structure
        "url": HUGO_CONTENT_URL_BASE + file_path.replace(CONTENT_DIR, '').replace('index.md', '')
    }

    if "Documents" in hugo_data['url']:
        return


    filename = f"{video_id}_{generate_file_hash(file_path)}.json"
    print(hugo_data['url'])
    with open(os.path.join(DATA_DIR, filename), 'w') as json_file:
        json.dump(hugo_data, json_file)
    # print(hugo_data['url'])
    # with open(os.path.join(DATA_DIR, f"{video_id}.json"), 'w') as json_file:
        # json.dump(hugo_data, json_file)


def process_playlist_data(playlist_data, playlist_items_data, file_path):
    # Extract necessary data for the playlist
    snippet = playlist_data['items'][0]['snippet']

    # Extract video details from playlist items
    videos = []
    for item in playlist_items_data['items']:
        video_snippet = item['snippet']
        videos.append({
            "video_id": video_id,
            "title": video_snippet['title'],
            "description": video_snippet['description'],
            "thumbnail": video_snippet['thumbnails']['default']['url'],
            "uploadDate": video_snippet['publishedAt'],
            "videoId": video_snippet['resourceId']['videoId'],
            "url": HUGO_CONTENT_URL_BASE + file_path.replace(CONTENT_DIR, '').replace('index.md', '')
        })

    hugo_data = {
        "video_id": video_id,
        "title": snippet['title'],
        "description": snippet['description'],
        "thumbnail": snippet['thumbnails']['default']['url'],
        "uploadDate": snippet['publishedAt'],
        "videos": videos,
        "url": HUGO_CONTENT_URL_BASE + file_path.replace(CONTENT_DIR, '').replace('index.md', ''),
    }

    if "Documents" in hugo_data['url']:
        return


    filename = f"{playlist_data['items'][0]['id']}_{generate_file_hash(file_path)}.json"
    print(hugo_data['url'])
    with open(os.path.join(DATA_DIR, filename), 'w') as json_file:
        json.dump(hugo_data, json_file)

    # print(hugo_data['url'])
    # with open(os.path.join(DATA_DIR, f"{playlist_data['items'][0]['id']}.json"), 'w') as json_file:
        # json.dump(hugo_data, json_file)

def get_url_from_path(base_url, path, content_dir):
    """Generate the URL for a given file path."""
    relative_path = os.path.relpath(path, content_dir)
    url_path = relative_path.replace(os.path.sep, '/')
    if url_path.endswith('.md'):
        url_path = url_path[:-3]  # Remove .md extension
    return base_url + url_path

def is_within_comment(shortcode, content):
    """Check if the shortcode is within an HTML comment."""
    matches = re.finditer(r'<!--.*?-->', content, re.DOTALL)
    for match in matches:
        if shortcode in match.group():
            return True
    return False

def extract_shortcodes(content, pattern):
    """Extract shortcodes that are not within HTML comments."""
    shortcodes = re.findall(pattern, content)
    return [shortcode for shortcode in shortcodes if not re.search(r'<!--.*{}.*-->'.format(re.escape(shortcode)), content)]


def extract_ids_from_shortcode(content, pattern):
    """Extract video or playlist IDs from the shortcode."""
    return re.findall(pattern, content)

def generate_file_hash(file_path):
    return hashlib.md5(file_path.encode()).hexdigest()

video_ids = []
playlist_ids = []


for subdir, _, files in os.walk(CONTENT_DIR):
    for file in files:
        if file.endswith(".md"):
            _filename = os.path.join(subdir, file)
            with open(_filename, 'r') as f:
            # with open(os.path.join(subdir, file), 'r') as f:
                # print(f"Processing {_filename}.")
                content = f.read()

                # Extract video IDs from youtube shortcodes
                youtube_ids = extract_ids_from_shortcode(content, r'{{< youtube ([^>]+) >}}')
                for video_id in youtube_ids:
                    if not is_within_comment('{{< youtube {} >}}'.format(video_id), content):
                        video_data = fetch_video_details(video_id)
                        if video_data:
                            process_video_data(video_data, os.path.join(subdir, file))
                            # print(f"video id: {video_id} -- {f}")
                            print(f"Processing youtube video\n{_filename}\n{video_id}\n")
                
                # Extract playlist IDs from youtubepl shortcodes
                youtubepl_ids = extract_ids_from_shortcode(content, r'{{< youtubepl ([^>]+) >}}')
                for playlist_id in youtubepl_ids:
                    if not is_within_comment('{{< youtubepl {} >}}'.format(playlist_id), content):
                        playlist_data = fetch_playlist_details(playlist_id)
                        playlist_items_data = fetch_playlist_items(playlist_id)
                        if playlist_data and playlist_items_data:
                            process_playlist_data(playlist_data, playlist_items_data, os.path.join(subdir, file))
                            # print(f"playlist id: {youtubepl_ids} -- {f}")
                            print(f"Processing youtube playlistt\n{_filename}\n{video_id}\n")

print("Processing complete.")
