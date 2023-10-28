import os
from spotipy import Spotify, oauth2
from spotipy.cache_handler import MemoryCacheHandler


def get_spotify(client_id, client_secret):
    redirect_uri = "http://localhost:8090/callback/"

    token = {
        "access_token": os.environ.get("SPOTIFY_ACCESS_TOKEN"),
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": None,
        "expires_at": 1697942466,
        "refresh_token": os.environ.get("SPOTIFY_REFRESH_TOKEN"),
    }

    cache_handler = MemoryCacheHandler(token)

    spotify = Spotify(
        auth_manager=oauth2.SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='',
            cache_handler=cache_handler,
        )
    )

    return spotify


def get_podcast_episodes(spotify, show_id):
    beans_show = spotify.show(show_id)
    episode_count = beans_show["total_episodes"]
    episodes = []
    for idx in range(0, episode_count, 50):
        episodes_chunk = spotify.show_episodes(show_id, limit=50, offset=idx)
        episodes += episodes_chunk["items"]

    return episodes


def get_spotify_episode_info(client_id, client_secret, spotify_show_id):
    spotify = get_spotify(client_id, client_secret)
    spotify_episodes_full_detail = get_podcast_episodes(spotify, spotify_show_id)
    spotify_episodes = [
        {
            "id": episode["id"],
            "name": episode["name"],
            "release_date": episode["release_date"],
        }
        for episode in spotify_episodes_full_detail
    ]
    spotify_episode_mapping = {
        (e["name"], e["release_date"]): e["id"] for e in spotify_episodes
    }

    return spotify_episodes, spotify_episode_mapping
