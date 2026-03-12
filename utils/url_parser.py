from urllib.parse import urlparse, parse_qs
import re


def extract_video_id(url: str):
    parsed = urlparse(url)

    if "youtu.be" in parsed.netloc:
        return parsed.path.lstrip("/")

    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]

    return None


def extract_playlist_id(url: str):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return qs.get("list", [None])[0]


def extract_playlist_index(url: str) -> int:
    """Extract the index param from a playlist URL. Returns 0 if not present."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    idx = qs.get("index", [None])[0]
    if idx and str(idx).isdigit():
        return int(idx) - 1  # YouTube index is 1-based, we store 0-based
    return 0


def extract_timestamp_seconds(url: str) -> int:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    t_param = qs.get("t")
    if t_param:
        t = t_param[0]

        if t.isdigit():
            return int(t)

        match = re.match(r"(?:(\d+)m)?(?:(\d+)s)?", t)
        if match:
            minutes = int(match.group(1) or 0)
            seconds = int(match.group(2) or 0)
            return minutes * 60 + seconds

    start_param = qs.get("start")
    if start_param and start_param[0].isdigit():
        return int(start_param[0])

    return 0