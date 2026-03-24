import os
import yt_dlp
from yt_dlp.utils import DownloadError
from scripts import env

def try_download(url, channel_id):
    output_path = os.path.join(os.getcwd(), "audio", str(channel_id), "%(id)s.%(ext)s")

    ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        "js_runtimes": {
            "node": {}  # key = runtime, empty config
        },
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '128'
            }
        ],
        'noplaylist': True,  # optional, prevents playlist expansion
        'quiet': True,
    }

    try:
        print('[DOWNLOADER] Processing request')

        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            # Download + extract info in one go
            info = ytdl.extract_info(url, download=True)

            # Prepare info
            title = info.get('title')
            audio_path = ytdl.prepare_filename(info).rsplit('.', 1)[0] + '.opus'

            # Check cache / duration
            if os.path.exists(audio_path):
                print('[DOWNLOADER] Music cached')
                return title, audio_path
            elif info.get('duration') and info['duration'] > env.get_max_time():
                print('[DOWNLOADER] Song too long!')
                return None

            return title, audio_path

    except DownloadError:
        print('[DOWNLOADER] Download Error!')
        return None

