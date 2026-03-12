import yt_dlp
import json
from urllib.parse import urlparse, parse_qs

def extract_playlist_id(url: str):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return qs.get("list", [None])[0]


def test_fetch_playlist_videos(playlist_url: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,  # don't fetch full info for each video, just IDs
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    print("=== PLAYLIST INFO ===")
    print(f"  playlist_id: {info.get('id')}")
    print(f"  title: {info.get('title')}")
    print(f"  channel: {info.get('channel')}")
    print(f"  video count: {len(info.get('entries', []))}")

    print("\n=== VIDEOS ===")
    for entry in info.get("entries", []):
        print(f"  [{entry.get('playlist_index')}] {entry.get('id')} — {entry.get('title')}")

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=ASRCJK2aWk0&list=PLZoTAELRMXVPC8r1xF68Gksi241DAtMsK&index=4"
    
    playlist_id = extract_playlist_id(url)
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    
    print(f"Extracted playlist_id: {playlist_id}")
    print(f"Fetching: {playlist_url}\n")
    
    test_fetch_playlist_videos(playlist_url)