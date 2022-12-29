import spotipy 
import spotipy.oauth2

def spotify_auth(config):
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id=config['client_id'], client_secret=config['client_secret'],redirect_uri=config['redirect_uri'],scope=config['scope'])
    url = sp_oauth.get_authorize_url()
    return url

def get_token(config, code):
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id=config['client_id'], client_secret=config['client_secret'],redirect_uri=config['redirect_uri'],scope=config['scope'])
    token = sp_oauth.get_access_token(code)
    return token
    
def check_if_token_is_expired(token):
    return spotipy.oauth2.is_token_expired(token)

def refresh_token(config, refresh_token):
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id=config['client_id'], client_secret=config['client_secret'],redirect_uri=config['redirect_uri'],scope=config['scope'])
    token = sp_oauth.refresh_access_token(refresh_token)
    return token

def get_user_info(spotify_object):
    return spotify_object.current_user()

def get_spotify_object(token):
    return spotipy.Spotify(auth=token)