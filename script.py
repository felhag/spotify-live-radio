import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import CacheFileHandler
from requests import get
from conf import *


def last_played():
    """
    retrieves last played tracks from kink api
    :return: array of tracks
    """
    response = get('https://api.kink.nl/programming/kink?nocache=1&serializer=data&includes=songs&day=0')
    json = response.json()
    day = json.get('meta').get('day')
    programs = json.get('data')[0].get(day).get('data')
    songs = map(lambda p: p.get('playedSongs').get('data'), programs)
    return sorted([item for sublist in songs for item in sublist], key=lambda p: p.get('start_datetime'), reverse=True)


def get_api():
    """
    initiates spotipy api instance
    :return: new api instance
    """
    handler = CacheFileHandler(cache_path='cache', username='tonnytorpedo')
    auth_manager = SpotifyOAuth(client_id=clientId,
                                client_secret=clientSecret,
                                cache_handler=handler,
                                redirect_uri=redirectUrl,
                                open_browser=False,
                                scope="playlist-modify-private playlist-modify-public playlist-read-private")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


def add_new(api, prev, played):
    """
    adds new tracks to playlist
    :param api:     spotipy api object
    :param prev:    last handled track id from previous run
    :param played:  list of last played tracks
    :return:        last handled track in this iteration
    """
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

    return last


def cleanup(api):
    """
    removes first added tracks from playlist based on maxSize configuration
    :param api: spotipy api object
    """
    total = api.playlist_items(playlist_id=playlistId,fields="total").get('total')
    if total > maxSize:
        chunk = min(100, total - maxSize)
        tracks = api.playlist_items(playlist_id=playlistId,fields="items(added_at,track(id))",limit=chunk).get('items')
        ids = map(lambda item: item.get('track').get('id'), tracks)
        api.playlist_remove_all_occurrences_of_items(playlist_id=playlistId,items=ids)
        print(f'Removed {len(tracks)} items from playlist which contained {total} items.')



def run():
    played = last_played()
    if len(played) == 0:
        return

    api = get_api()

    with open("last", "r+") as file:
        prev = file.read()
        last = add_new(api, prev, played)

        if last != prev:
            file.seek(0)
            file.write(last)
            file.truncate()

    cleanup(api)


run()
