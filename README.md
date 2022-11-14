# NTS tracklist to Spotify playlist

Script to convert the tracklist of a given [NTS radio show](https://www.nts.live/) into a Spotify playlist on the account of the user that is logged in (using oauth2). Frontend using FastApi, backend using Spotipy and BeautifulSoup.

<img src="/static/nts2sp.jpg" width="150"/>

## Installation
Install the requirements (BeautifulSoup, Spotipy, FastApi etc.) by using pip.

```bash
pip install -r requirements.txt
```

## Configuration
Make a new file in the main directory called *config.py* with the following structure:

```python
config = {
    'scope': 'user-read-private playlist-modify-public playlist-modify-private ugc-image-upload',
    'client_id': '',
    'client_secret': '',
    'redirect_uri': 'http://localhost:8000/callback',
    'session_middleware_key': ''
}
```

On the [dashboard of the Spotify for developers site](https://developer.spotify.com/dashboard/), make a new app and copy the *client_id* and *client_secret* to the *config.py* file and add the *redirect_uri* to the app settings (and don't forget to save them). Generate a random key to use for the session and paste it into the same file for the *session_middleware_key*.

## Usage
Launch the application by using one of the following commands:

```bash
uvicorn main:app
```

```bash
python3 main.py
```

Access the site by browsing to *localhost:8000* in your browser. Paste the url of your favorite [NTS show](https://www.nts.live/shows/) and enjoy your fresh Spotify playlist!
