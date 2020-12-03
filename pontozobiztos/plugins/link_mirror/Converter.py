from typing import Union, Tuple, List, TypedDict
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import ytmusicapi
from unidecode import unidecode
import re
from dotenv import load_dotenv
load_dotenv()


spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials())

ytmusic = ytmusicapi.YTMusic()


class Artists:
    def __init__(self):
        self.original: List[str] = []
        self.cover: List[str] = []
        self.feat: List[str] = []
        self.vs: List[str] = []
        self.remix: List[str] = []
        self.edit: List[str] = []
        self.other: List[str] = []

    def __repr__(self):
        return str(self.__dict__)

    def __bool__(self):
        return bool(self.original or self.cover or self.feat
                    or self.vs or self.remix or self.edit or self.other)

    @staticmethod
    def _remove_the_a_an(val):
        return re.sub('(^the |^a |^an )', '', val)

    def remove_the_a_an(self):
        self.original = [self._remove_the_a_an(x) for x in self.original]
        self.cover = [self._remove_the_a_an(x) for x in self.cover]
        self.feat = [self._remove_the_a_an(x) for x in self.feat]
        self.vs = [self._remove_the_a_an(x) for x in self.vs]
        self.remix = [self._remove_the_a_an(x) for x in self.remix]
        self.edit = [self._remove_the_a_an(x) for x in self.edit]
        self.other = [self._remove_the_a_an(x) for x in self.other]


class ConverterBase:
    URI_BASE: str

    @staticmethod
    def _parse_title(title: str) -> Tuple[str, Artists]:
        def run_regex(inp, *pat):
            res_list = []
            for p in pat:
                if match := re.search(p, inp):
                    res_list.append(match.group(1))
                    inp = re.sub(p, '', inp)
            return inp, res_list

        title = title.lower()
        title = unidecode(title)

        for p in ['[', '{']:
            title = title.replace(p, '(')
        for p in [']', '}']:
            title = title.replace(p, ')')

        artists: Artists = Artists()

        feat_patterns = [
            re.compile(r'\(feat. ([^)]*)\)'),
            re.compile(r'\(ft. ([^)]*)\)'),
            re.compile(r'feat. ([^-]*)'),
            re.compile(r'ft. ([^-]*)')
        ]
        title, artists_temp = run_regex(title, *feat_patterns)
        artists.feat += artists_temp

        cover_patterns = [
            re.compile(r'\(.*cover by ([^)]*)\)'),
            re.compile(r'\(([^)]*) cover\)'),
            re.compile(r'([^\s]+) cover')
        ]
        title, artists_temp = run_regex(title, *cover_patterns)
        artists.cover += artists_temp

        edit_patterns = [
            re.compile(r'\(([^)]*) edit\)'),
            re.compile(r'([^\s]+) edit')
        ]
        title, artists_temp = run_regex(title, *edit_patterns)
        artists.edit += artists_temp

        remix_patterns = [
            re.compile(r'\(([^)]*) remix\)'),
            re.compile(r'- .* - (.*) remix')
        ]
        title, artists_temp = run_regex(title, *remix_patterns)
        artists.remix += artists_temp

        if m := re.search(re.compile(r'\(([^)]*) vs\.? ([^)]*)\)'), title):
            artists.vs = [m.group(1), m.group(2)]
            title = re.sub(p, '', title)

        other_patterns = [
            re.compile(r'\(([^)]*) x ([^)]*)\)')
        ]
        for p in other_patterns:
            if m := re.search(p, title):
                artists.other.append(m.group(1))
                title = re.sub(p, '', title)

        # if there's any other parenthesis, remove them
        pattern = re.compile(r'(\(.*\)|\[.*])')
        title, _ = pattern.subn('', title)

        title, final_title = run_regex(title, re.compile('"(.*)"'))
        final_title = final_title[0] if final_title else ''

        vert_loc = title.find('|')
        if vert_loc != -1:
            title = title[:vert_loc]

        # if it starts with a number, delete it
        pattern = re.compile(r'^\d+\.')
        title = re.sub(pattern, '', title)

        pattern = re.compile(r'\.{3}')
        title = re.sub(pattern, '', title)

        # remove excess whitespaces
        title = title.strip()

        splt = title.split(' - ')
        for i in range(len(splt)):
            if not splt[i]:
                del splt[i]

        try:
            artists.original = [splt[0]]
            final_title = splt[1]
        except IndexError:
            artists.original = []
            final_title = final_title or title

        def split_at_delimeters(inp):
            delims = ['&', ' & ',  ', ', ' vs ', ' vs. ', ' x ', ' and ', ' és ']
            for d in delims:
                inp = inp.replace(d, ' & ')
            return [s.strip() for s in inp.split(' & ')]

        if artists.original:
            og_artist_list = split_at_delimeters(artists.original[0])
            for artist in [x for x in og_artist_list if x]:
                spoti_search_result = spotify.search(q=artist, type='artist')
                for it in spoti_search_result['artists']['items']:
                    if it['name'].lower() == artist:
                        artists.original = og_artist_list
                        break
        else:
            # this case assumes title - artist format
            og_artist_list = split_at_delimeters(final_title)
            for artist in [x for x in og_artist_list if x]:
                spoti_search_result = spotify.search(q=artist, type='artist')
                for it in spoti_search_result['artists']['items']:
                    if it['name'].lower() == artist:
                        tmp = artists.original
                        artists.original = [final_title]
                        final_title = " ".join(tmp)
                        break

        artists.remove_the_a_an()
        return final_title, artists

    @classmethod
    def parse_title(cls, title: str) -> Tuple[str, List[str]]:
        return Spotify.title_artist_gen(*cls._parse_title(title))

    @classmethod
    def check_uri(cls, uri: str) -> bool:
        uri = uri.replace('www.', '')
        uri_base_length = len(cls.URI_BASE)
        if len(uri) > uri_base_length and uri[:uri_base_length] == cls.URI_BASE:
            return True
        return False

    @classmethod
    def get_url_from_data(cls, title: str, artists: [str] = None) -> str:
        raise NotImplemented

    @classmethod
    def get_title_and_artists(cls, uri: str) -> (str, [str]):
        raise NotImplemented

    @classmethod
    def convert(cls, uri: str) -> [str]:
        raise NotImplemented


class Youtube(ConverterBase):
    URI_BASE = "https://www.youtube.com"

    @classmethod
    def check_uri(cls, uri: str) -> bool:
        if uri.startswith('https://www.youtube.com/watch?v=') or \
           uri.startswith('https://youtu.be/'):
            return True
        else:
            return False

    @classmethod
    def get_title_and_artists(cls, uri) -> Tuple[str, List[str]]:
        if match := re.match(cls.URI_BASE + r'/watch\?v=([^&]*)',
                             uri):
            track_id = match.group(1)
        elif match := re.match('https://youtu.be/([^&]*)', uri):
            track_id = match.group(1)
        else:
            raise PluginException('Invalid YouTube url')
        try:
            res = ytmusic.get_song(track_id)
        except KeyError:
            raise PluginException('Video Unavailable')
        try:
            if res['category'] not in ('Music', 'Entertainment'):
                raise PluginException('Not a music video')

            if int(res['lengthSeconds']) > 15 * 60:
                raise PluginException('This is probably a live recording')
        except KeyError:
            raise PluginException('Video not available')

        def split_at_and(inp):
            new_artists = []
            for a in inp:
                a = a.replace(' and ', ' & ')
                new_artists += a.split(' & ')
            return new_artists

        art = []
        try:
            art += split_at_and([a['name'] for a in res['artists']])
        except TypeError:
            art += split_at_and(res['artists'])
        except KeyError:
            pass

        t, a_ = cls.parse_title(res['title'])
        art = art or a_
        art = [Artists._remove_the_a_an(a) for a in art]

        if not art:
            PluginException('Probably not a music video. No artists found')

        return t, art

    @classmethod
    def convert(cls, uri: str) -> List[str]:
        title, artists = cls.get_title_and_artists(uri)
        if not artists:
            raise PluginException('Artist not found.')
        try:
            return [YoutubeMusic.get_url_from_data(title, artists),
                    Spotify.get_url_from_data(title, artists)]
        except InnenTudodHogyJoException:
            raise PluginException('Probably not a music video.')


class YoutubeMusic(ConverterBase):
    URI_BASE = "https://music.youtube.com"

    @classmethod
    def generate_link(cls, track_id):
        return 'https://music.youtube.com/watch?v=' + track_id

    @classmethod
    def get_url_from_data(cls, title: str, artists: List[str] = None) -> str:
        artists = artists or []
        res = ytmusic.search(' '.join([title, *artists]), filter="songs")
        if not res:
            raise PluginException("Could not find track on YouTube Music: "
                                  + title + ' - ' + ', '.join(artists))
        return cls.generate_link(res[0]['videoId'])

    @classmethod
    def get_title_and_artists(cls, uri) -> Tuple[str, List[str]]:
        if match := re.match(cls.URI_BASE + r'/watch\?v=([^&]*)', uri):
            track_id = match.group(1)
        else:
            raise PluginException('Invalid YouTube Music url')

        res = ytmusic.get_song(track_id)

        if int(res['lengthSeconds']) > 15 * 60:
            raise PluginException('This is probably a live recording')

        pattern = re.compile(r'(\(.*\)|\[.*])')
        title_subbed, _ = pattern.subn('', res['title'])

        def split_at_and(inp):
            new_artists = []
            for a in inp:
                a = a.replace('and', '&')
                new_artists += a.split(' & ')
            return new_artists

        try:
            return title_subbed, split_at_and([a['name'] for a in res['artists']])
        except TypeError:
            return title_subbed, split_at_and(res['artists'])
        except KeyError:
            return cls.parse_title(res['title'])

    @classmethod
    def convert(cls, uri) -> List[str]:
        return [Spotify.get_url_from_data(*cls.get_title_and_artists(uri))]


class Spotify(ConverterBase):
    URI_BASE = "https://open.spotify.com"

    @staticmethod
    def strip_title(title):
        if not title:
            return ''
        title = title.split(' - ')[0]
        title = title.split(' (')[0]
        return title.strip()

    @staticmethod
    def _search(title: str, artists: List[str] = None) -> str:
        def local_search(t, a):
            if a:
                r = spotify.search(" ".join([t, "artist:", *a]))
            else:
                r = spotify.search(t)

            for item in r['tracks']['items']:
                title_baseline = Spotify.strip_title(item['name'])
                if title_baseline == title.lower():
                    return item['external_urls']['spotify']
            for a in artists:
                t_temp = t + ' ' + a
                r = spotify.search(t_temp)
                for item in r['tracks']['items']:
                    title_baseline = Spotify.strip_title(item['name'])
                    if title_baseline == title.lower():
                        return item['external_urls']['spotify']
            try:
                return r['tracks']['items'][0]['external_urls']['spotify']
            except IndexError:
                raise ValueError
        try:
            return local_search(title, artists)
        except ValueError:
            artists = artists[::-1][1:]
            for artist in artists:
                try:
                    return local_search(title, artists)
                except ValueError:
                    artists.remove(artist)
        raise InnenTudodHogyJoException('Na innen tudod, hogy jó')

    @staticmethod
    def title_artist_gen(og_title: str, artists: Artists = None) -> Tuple[str, List[str]]:
        def form(to: str, val: List[str]) -> Tuple[str, List[str]]:
            if not val:
                return '', []
            if to == 'remix_title':
                return f' - {val[0]} remix', []
            if to == 'vs_title':
                return f' - {val[0]} vs {val[1]}', []
            if to == 'edit':
                return f' - {val[0]} edit', []
            if to in ('remix_artists', 'cover', 'feat', 'original', 'vs_artists', 'other'):
                return '', [*val]
            return '', []

        result_list = []
        # first try with remix: it's the most likely in the chat
        if artists.remix:
            result_list.append(form('remix_artists', artists.remix))
            result_list.append(form('vs_artists', artists.vs))
            result_list.append(form('cover', artists.cover))
            result_list.append(form('other', artists.other))
            result_list.append(form('edit', artists.edit))
        elif artists.vs:
            result_list.append(form('vs_artists', artists.vs))
            result_list.append(form('cover', artists.cover))
            result_list.append(form('other', artists.other))
            result_list.append(form('edit', artists.edit))
        elif artists.cover:
            result_list.append(form('cover', artists.cover))
            result_list.append(form('other', artists.other))
            result_list.append(form('edit', artists.edit))
        elif artists.original:
            result_list.append(form('original', artists.original))
            result_list.append(form('feat', artists.feat))
            result_list.append(form('edit', artists.edit))

        title = "".join([og_title] + [x[0] for x in result_list])
        artist_list = [y for x in result_list for y in x[1]]
        return title, artist_list

    @classmethod
    def get_url_from_data(cls, title: str, artists: List[str] = None) -> str:
        return cls._search(title, artists)

    @classmethod
    def get_title_and_artists(cls, uri) -> Tuple[str, List[str]]:
        try:
            track = spotify.track(uri)
        except spotipy.exceptions.SpotifyException:
            raise PluginException('Invalid spotify url')

        title = track["name"]
        artists = [artist["name"] for artist in track["artists"]]
        return title, artists

    @classmethod
    def convert(cls, uri) -> List[str]:
        return [YoutubeMusic.get_url_from_data(*cls.get_title_and_artists(uri))]


def convert_uri(uri: str) -> Union[List[str], None]:
    if Youtube.check_uri(uri):
        return Youtube.convert(uri)
    elif YoutubeMusic.check_uri(uri):
        return YoutubeMusic.convert(uri)
    elif Spotify.check_uri(uri):
        return Spotify.convert(uri)
    else:
        return []


class PluginException(BaseException):
    pass


class InnenTudodHogyJoException(PluginException):
    pass
