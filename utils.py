import requests


class SpotifyPlayback:
    def __init__(self, access_token, device_id=None):
        self.access_token = access_token
        self.device_id = device_id
        
    def play_track(self, track_uri):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "uris": [track_uri]
        }
        if self.device_id:
            params = {
                "device_id": self.device_id
            }
            url = "https://api.spotify.com/v1/me/player/play"
        else:
            url = "https://api.spotify.com/v1/me/player/play?device_id=devicedefault"
        response = requests.put(url, headers=headers, json=data, params=params)
        if response.status_code != 204:
            raise Exception(f"Failed to play track {track_uri}")
