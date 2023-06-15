import os

import yt_dlp
from yt_dlp.utils import DownloadError

from scripts import env


def try_download(url, channel_id):
    output_path = os.path.join("/audio", str(channel_id), "%(id)s.%(ext)s")

    ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '128',
            }
        ],
    }

    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        try:
            print('[DOWNLOADER] Checking information')
            video_info = ytdl.extract_info(url, download=False)
            title = video_info.get('title')
            duration = video_info.get('duration')
            filename = os.path.splitext(ytdl.prepare_filename(video_info))[0] + '.opus'
            audio_path = os.path.join(os.getcwd(), filename)
            if os.path.exists(audio_path):
                print('[DOWNLOADER] Music already cached')
                return title, audio_path
            elif duration and duration <= env.get_max_time():
                print('[DOWNLOADER] Downloading & converting requested music')
                ytdl.download([url])
                return title, audio_path
            else:
                print('[DOWNLOADER] Song was too long!')
                return None
        except DownloadError:
            print('[DOWNLOADER] Download Error!')
