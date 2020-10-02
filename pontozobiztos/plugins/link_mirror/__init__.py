from fbchat import Message, ShareAttachment
from pontozobiztos.models.User import User
from pontozobiztos.MyClient import ClientProxy

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import ytmusicapi

import re
from dotenv import load_dotenv
from requests.exceptions import HTTPError
load_dotenv()


def on_message(client, author, message):
    """On message callback

    Args:
        client (ClientProxy): a proxy fbchat.Client
        author (User): pontozobiztos.models.User object
        message (Message): Received fbchat.Message object
    """
    try:
        if message.text[:31] == "https://open.spotify.com/track/":
            client.send_uri_reply(message.uid, sp2yt(message.text))
        elif message.text[:31] == "https://music.youtube.com/watch":
            client.send_uri_reply(message.uid, yt2sp(message.text))
        else:
            return False
    except PluginException as e:
        client.send_reply(message.uid, str(e))
    return True



spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials())

ytmusic = ytmusicapi.YTMusic()


def sp_find_track_metadata_by_url(url):
    try:
        track = spotify.track(url)
    except HTTPError:
        raise PluginException("Invalid spotify url: " + url)

    title = track["name"]
    artists = [artist["name"] for artist in track["artists"]]
    return title, artists


def sp_find_track_url_by_metadata(title: str, artists: []):
    res = spotify.search(" ".join([title, " artist:", *artists]))
    if not (items := res['tracks']['items']):
        raise PluginException("Could not find track on Spotify: "
                              + title + ' - ' + ', '.join(artists))
    return items[0]['external_urls']['spotify']


def yt_find_track_metadata_by_url(url):
    if match := re.match(r'https://music.youtube.com/watch\?v=([^&]*)', url):
        track_id = match.group(1)
    else:
        raise PluginException('Invalid YouTube Music url: ' + url)

    res = ytmusic.get_song(track_id)
    return res['title'], res.get('artists', [])


def yt_find_track_url_by_metadata(title: str, artists: []):
    res = ytmusic.search(' '.join([title, *artists]), filter="songs")
    if not res:
        raise PluginException("Could not find track on YouTube Music: "
                              + title + ' - ' + ', '.join(artists))
    video_id = res[0]['videoId']
    return 'https://music.youtube.com/watch?v=' + video_id


def yt2sp(url):
    title, artists = yt_find_track_metadata_by_url(url)
    return sp_find_track_url_by_metadata(title, artists)


def sp2yt(url):
    title, artists = sp_find_track_metadata_by_url(url)
    return yt_find_track_url_by_metadata(title, artists)


class PluginException(BaseException):
    pass
