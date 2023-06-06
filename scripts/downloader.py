import os

import yt_dlp
from yt_dlp.utils import DownloadError

from scripts import env


def try_download(url):
    ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '/audio/%(id)s.%(ext)s',
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
            video_info = ytdl.extract_info(url, download=False)
            title = video_info.get('title')
            duration = video_info.get('duration')
            filename = os.path.splitext(ytdl.prepare_filename(video_info))[0] + '.opus'
            print(title)
            if duration and duration <= env.get_max_time():
                ytdl.download([url])
                audio_path = os.path.join(os.getcwd(), filename)
                return title, audio_path
            else:
                print('Video was too long!')
        except DownloadError:
            print('Download Error!')
