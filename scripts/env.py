import os
from dotenv import load_dotenv


def load():
    load_dotenv()


def get_max_time():
    max_time = os.getenv('MAX_TIME')
    if max_time is None or not max_time.isdigit():
        max_time = 600
    else:
        max_time = int(max_time)
    return max_time


def get_token():
    token = os.getenv('TOKEN')
    if token is None:
        raise ValueError('Token is not defined')
    return token
