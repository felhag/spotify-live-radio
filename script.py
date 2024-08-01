import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import CacheFileHandler
from requests import get
from conf import *

def run():
    response = get('https://api.kink.nl/programming/kink?nocache=1&serializer=data&includes=songs&day=0')
    json = response.json()
    day = json.get('meta').get('day')
    programs = json.get('data')[0].get(day).get('data')
    songs = map(lambda p: p.get('playedSongs').get('data'), programs)
    played = sorted([item for sublist in songs for item in sublist], key=lambda p: p.get('start_datetime'), reverse=True)
    if len(played) == 0:
        return

    api = get_api()

    with open("last", "r+") as file:
        prev = file.read()
        uris = []

        for i, song in enumerate(played):
            if i >= 50 or str(song.get('short_id')) == prev:
                break

            search = api.search(song.get('artist') + ' ' + song.get('title')).get('tracks').get('items')

            if len(search) > 0:
                uris.append(search[0].get('uri'))
            else:
                print(f"Cant find anything for {song.get('artist')} - {song.get('track')}")

        last = str(played[0].get('short_id'))
        if last != prev:
            print(f'Adding {len(uris)} items to playlist')
            api.playlist_add_items(playlist_id=playlistId, items=uris)

            file.seek(0)
            file.write(last)
            file.truncate()


def get_api():
    handler = CacheFileHandler(cache_path='cache', username='tonnytorpedo')
    auth_manager = SpotifyOAuth(client_id=clientId,
                                client_secret=clientSecret,
                                cache_handler=handler,
                                redirect_uri=redirectUrl,
                                open_browser=False,
                                scope="playlist-modify-private playlist-modify-public playlist-read-private")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


run()
