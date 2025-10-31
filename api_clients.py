import time
import discogs_client
import pylast

# API
DISCOGS_APP_TOKEN = 'fJqiqcsBHozXqkieZUvJNbNKjNSDySUDRaRxwnxE'
LASTFM_APP_KEY = '5bb5b358b3a7c21d712f85611678088a'
LASTFM_APP_SECRET = 'ecee8bbf22c251acdad5a5b35af8adb5'

class ApiClients:
    def __init__(self, lastfm_username, lastfm_password):
        self.discogs_client = discogs_client.Client('ScrobblerApp/0.1', user_token=DISCOGS_APP_TOKEN)

        password_hash = pylast.md5(lastfm_password)
        self.lastfm_network = pylast.LastFMNetwork(
            api_key=LASTFM_APP_KEY,
            api_secret=LASTFM_APP_SECRET,
            username=lastfm_username,
            password_hash=password_hash,
        )

    def get_discogs_release(self, release_id: str):
        try:
            release = self.discogs_client.release(int(release_id))
            tracklist = [
                {'position': track.position, 'title': track.title, 'duration': track.duration}
                for track in release.tracklist
            ]
            return {
                'artist': release.artists[0].name,
                'album': release.title,
                'tracks': tracklist
            }
        except Exception as e:
            print(f"Discogs data import error: {e}")
            return None

    def scrobble_to_lastfm(self, artist: str, album: str, tracks_to_scrobble: list):
        current_timestamp = int(time.time())
        for track in reversed(tracks_to_scrobble):
            track['timestamp'] = current_timestamp
            duration = track['duration'] if track['duration'] > 0 else 180
            current_timestamp -= duration

        print("Scrobbling...")
        for track in tracks_to_scrobble:
            print(f"  -> {artist} - {track['title']}")
            try:
                self.lastfm_network.scrobble(
                    artist=artist,
                    title=track['title'],
                    timestamp=track['timestamp'],
                    album=album
                )
            except Exception as e:
                print(f"Couldn't scrobble track: '{track['title']}': {e}")
        print("Scrobbled successfully.")