import yt_dlp


def get_video_info(url: str):
    ydl_opts = {
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return {
        "title": info.get("title"),
        "channel": info.get("uploader"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail")
    }