from typing import Union
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import ytmusicapi

import re
from dotenv import load_dotenv
load_dotenv()


spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials())

ytmusic = ytmusicapi.YTMusic()


class ConverterBase:
    URI_BASE: str

    def __init__(self, original_url: str):
        self.original_url = original_url.replace('www.', '')

    @classmethod
    def check_uri(cls, uri: str) -> bool:
        uri = uri.replace('www.', '')
        uri_base_length = len(cls.URI_BASE)
        if len(uri) > uri_base_length and uri[:uri_base_length] == cls.URI_BASE:
            return True
        return False

    @staticmethod
    def get_url_from_data(title: str, artists: [str] = None) -> str:
        raise NotImplemented

    def get_title_and_artists(self) -> (str, [str]):
        raise NotImplemented

    def convert(self) -> [str]:
        raise NotImplemented


class Youtube(ConverterBase):
    URI_BASE = "https://youtube.com"

    def get_title_and_artists(self) -> (str, [str]):
        if match := re.match(self.URI_BASE + r'/watch\?v=([^&]*)',
                             self.original_url):
            track_id = match.group(1)
        else:
            raise PluginException('Invalid YouTube url')
        res = ytmusic.get_song(track_id)
        pattern = re.compile(r'(\(.*\)|\[.*])')
        title, _ = pattern.subn('', res['title'])
        title.strip()
        split_title = title.split(' - ')

        if len(split_title) <= 1:
            raise ValueError("Not a music video")

        # remove empty strings
        for i in range(len(split_title)-1, -1, -1):
            if not split_title[i]:
                del split_title[i]

        title = split_title[1]
        artists = split_title[0]

        delim_pattern = re.compile('(, |,| x | X |&| \| |\|)')
        title, _ = delim_pattern.subn(' & ', title)
        title = title.split(' & ')

        artists, _ = delim_pattern.subn(' & ', artists)
        artists = artists.split(' & ')

        # swap if title and artists are likely to be swapped
        if len(title) != 1 and len(artists) == 1:
            tmp = title
            title = artists
            artists = tmp

        # merge title if it is accidentally split (and hope for the best)
        title = ' '.join(title)

        return title, artists

    def convert(self) -> [str]:
        title, artists = self.get_title_and_artists()
        return [YoutubeMusic.get_url_from_data(title, artists),
                Spotify.get_url_from_data(title, artists)]


class YoutubeMusic(ConverterBase):
    URI_BASE = "https://music.youtube.com"

    @staticmethod
    def get_url_from_data(title: str, artists: [str] = None) -> str:
        artists = artists or []
        res = ytmusic.search(' '.join([title, *artists]), filter="songs")
        if not res:
            raise PluginException("Could not find track on YouTube Music: "
                                  + title + ' - ' + ', '.join(artists))
        video_id = res[0]['videoId']
        return 'https://music.youtube.com/watch?v=' + video_id

    def get_title_and_artists(self) -> (str, [str]):
        if match := re.match(self.URI_BASE + r'/watch\?v=([^&]*)',
                             self.original_url):
            track_id = match.group(1)
        else:
            raise PluginException('Invalid YouTube Music url')

        res = ytmusic.get_song(track_id)
        return res['title'], res.get('artists', [])

    def convert(self) -> [str]:
        return [Spotify.get_url_from_data(*self.get_title_and_artists())]


class Spotify(ConverterBase):
    URI_BASE = "https://open.spotify.com"

    @staticmethod
    def get_url_from_data(title: str, artists: [str] = None) -> str:
        artists = artists or []
        res = spotify.search(" ".join([title, " artist:", *artists]))
        if not (items := res['tracks']['items']):
            # raise PluginException("Could not find track on Spotify: "
            #                       + title + ' - ' + ', '.join(artists))
            raise PluginException("Na innen tudod, hogy jó.")
        return items[0]['external_urls']['spotify']

    def get_title_and_artists(self) -> (str, [str]):
        try:
            track = spotify.track(self.original_url)
        except spotipy.exceptions.SpotifyException:
            raise PluginException('Invalid spotify url')

        title = track["name"]
        artists = [artist["name"] for artist in track["artists"]]
        return title, artists

    def convert(self) -> [str]:
        return [YoutubeMusic.get_url_from_data(*self.get_title_and_artists())]


def create_converter(uri: str) -> Union[ConverterBase, None]:
    if Youtube.check_uri(uri):
        return Youtube(uri)
    elif YoutubeMusic.check_uri(uri):
        return YoutubeMusic(uri)
    elif Spotify.check_uri(uri):
        return Spotify(uri)
    else:
        return None


class PluginException(BaseException):
    pass


if __name__ == '__main__':
    asd = Youtube('https://youtube.com/watch?v=_tTber0f8qc')
    print(asd.get_title_and_artists())