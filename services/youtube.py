import yt_dlp


def fetch_video_metadata(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title"),
        "duration": info.get("duration"),
    }


def fetch_playlist_metadata(playlist_id: str) -> dict:
    """
    Fetch all video IDs and titles from a YouTube playlist.
    Always uses the pure playlist URL to avoid yt-dlp treating it as a single video.

    Returns:
    {
        "playlist_id": str,
        "title": str,
        "channel": str,
        "total_videos": int,
        "videos": [
            {"video_id": str, "title": str, "index_in_playlist": int},
            ...
        ]
    }
    """
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries") or []
    videos = [
        {
            "video_id": entry.get("id"),
            "title": entry.get("title") or entry.get("id"),
            "index_in_playlist": idx,  # 0-based
        }
        for idx, entry in enumerate(entries)
        if entry.get("id")
    ]

    return {
        "playlist_id": info.get("id"),
        "title": info.get("title") or playlist_id,
        "channel": info.get("channel") or info.get("uploader") or "Unknown",
        "total_videos": len(videos),
        "videos": videos,
    }