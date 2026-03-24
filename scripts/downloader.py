import os
import yt_dlp
from yt_dlp.utils import DownloadError
from scripts import env

def try_download(url, channel_id):
    output_path = os.path.join(os.getcwd(), "audio", str(channel_id), "%(id)s.%(ext)s")

    ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '128'
            }
        ],
        'noplaylist': True,
        'quiet': True,
        'socket_timeout': 10,
        'retries': 3,
    }

    try:
        print('[DOWNLOADER] Processing request')

        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            # Fetch metadata only first (fast) to check cache and duration
            info = ytdl.extract_info(url, download=False)

            title = info.get('title')
            audio_path = ytdl.prepare_filename(info).rsplit('.', 1)[0] + '.opus'

            # Return cached file immediately without re-downloading
            if os.path.exists(audio_path):
                print('[DOWNLOADER] Music cached')
                return title, audio_path

            # Reject before downloading if song is too long
            if info.get('duration') and info['duration'] > env.get_max_time():
                print('[DOWNLOADER] Song too long!')
                return None

            # Now download
            ytdl.download([url])
            return title, audio_path

    except DownloadError:
        print('[DOWNLOADER] Download Error!')
        return None

