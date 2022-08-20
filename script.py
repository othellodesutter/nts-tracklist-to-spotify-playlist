from bs4 import BeautifulSoup
import requests
import spotipy 
import base64
from fuzzywuzzy import fuzz
from PIL import Image
from io import BytesIO

def get_spotify_object(token):
    return spotipy.Spotify(auth=token)

def get_source(url):
    try:
        page_content = requests.get(url).text
    except:
        return "Invalid url"
    soup = BeautifulSoup(page_content, 'html.parser')
    return soup

def get_tracklist_from_set(soup):
    tracks = []
    # scrape NTS website for setlist
    try:
        for li in soup.find_all('li', attrs={'class': 'track'}):
            title = str(li.find('span', attrs={'class': 'track__title'}).text.lstrip().rstrip())
            # if there are multiple artists, add all of them to the query
            artists = str('')
            for artist in li.find_all('span', attrs={'class': 'track__artist track__artist--mobile'}):
                artists+=str(artist.text.lstrip().rstrip())
            tracks.append({'title': title, 'artists': artists})
    except:
        pass
    
    if len(tracks) == 0:
        return None
    return tracks

def generate_queries_from_tracklist(tracks):
    queries = []
    for track in tracks:
        query = 'track: ' + track['title'] + ' artist: ' + track['artists']
        print(query)
        queries.append(query)
    return queries

def get_spotify_uris_from_queries(queries, spotify_object):
    tracks = []
    for query in queries:
        # multiple types of queries to get more results
        query1 = query[:-1]
        query2 = query.replace('track: ', '').replace('artist: ', '')
        query3 = str(query.split(' artist: ')[0])[:-1] + ' artist: ' + query.split(' artist: ')[1]
        
        try:
            results1 = spotify_object.search(query1, type='track', limit=10)
            results2 = spotify_object.search(query2, type='track', limit=10)
            results3 = spotify_object.search(query3, type='track', limit=10)

            items = results1['tracks']['items'] + results2['tracks']['items'] + results3['tracks']['items']

        # to catch 'HTTP Error for GET to https://api.spotify.com/v1/search returned 404 due to Not found.' 
        except:
            return None

        query_track = query.split(' artist: ')[0].split('track: ')[1]
        query_artist = query.split('artist: ')[1]
        
        print('NTS: ' + query_track + ' - ' + query_artist)
        found_track = choose_best_corresponding_track(query_track, query_artist, items)
        try:
            if found_track is not None:
                tracks.append(found_track['uri'])
        except:
                pass
        print('--------------------------------------------')
    
    if len(tracks) == 0:
        return None
    return tracks

def choose_best_corresponding_track(query_track, query_artist, spotify_tracks):
    list_of_scores = []
    track = query_track + ' - ' + query_artist
    for item in spotify_tracks:
        spotify_artists = ",".join([str(artist['name']) for artist in item['artists']])

        ratio_title = fuzz.token_set_ratio(query_track, item['name'])
        ratio_artist = fuzz.token_set_ratio(query_artist, spotify_artists)
        score = fuzz.ratio(track, item['name'] + ' - ' + spotify_artists)

        print('SPT: ' + str(ratio_title) + ' ' + str(ratio_artist) + ' ' + str(score) + '% ' + item['name'] + ' - ' + str(spotify_artists))
        list_of_scores.append({'track': item, 'score': score, 'ratio_title': ratio_title, 'ratio_artist': ratio_artist})

    best_corresponding_tracks = []
    for item in list_of_scores:
        if item['ratio_title'] > 60:
            if item['ratio_artist'] > 60:
                best_corresponding_tracks.append(item)

    if len(best_corresponding_tracks) > 0:
        # of all the tracks that are still left (where title and artist similarity are higher than 60), it chooses the track with the highest combination score
        best_corresponding_track = max(best_corresponding_tracks, key=lambda x: x['score'])
        if best_corresponding_track['score'] > 50:
            print('BEST: ' + str(best_corresponding_track['score']) + '% ' + best_corresponding_track['track']['name'] + ' - ' + str(",".join([str(artist['name']) for artist in best_corresponding_track['track']['artists']])))
            return best_corresponding_track['track']
        else:
            return None
    else:
        return None

# cannot upload png files for a spotify playlist cover photo, so we need to convert it to jpg and then to base64
def convert_png_to_base64(image_url):
    image = Image.open(BytesIO(requests.get(image_url).content))
    with BytesIO() as f:
        image.convert('RGB').save(f, format='JPEG')
        f.seek(0)
        encoded_image = base64.b64encode(f.read()).decode("utf-8")
    return encoded_image

def create_new_spotify_playlist_and_add_tracks(url, token):
    # error handler if url field is empty
    if url is None:
        return "No url given"
    # error handler if url is not a nts.live url
    if "nts.live" not in url:
        return "Invalid url"
    # error handler if link doesn't start with http/https to prevent requests error
    if (url.startswith('nts.live')) or url.startswith('www.nts.live'):
        url = 'https://' + url

    source = get_source(url)
    tracks = get_tracklist_from_set(source)

    # error handler if tracklist on nts.live url is empty
    if tracks is None:
        return "No tracks found in given tracklist"

    spotify_object = get_spotify_object(token)
    queries = generate_queries_from_tracklist(tracks)
    uris = get_spotify_uris_from_queries(queries, spotify_object)

    # error handler if none of the nts tracks are found on spotify
    if uris is None:
        return "No tracks found on Spotify"

    playlist_name = source.find('h1', attrs={'class': 'text-bold'}).text.lstrip().rstrip()
    username = spotify_object.current_user()['id']

    playlist = spotify_object.user_playlist_create(username, playlist_name, description='')
    spotify_object.user_playlist_add_tracks(username, playlist['id'], uris)

    # extract orginal url from <meta content="https://www.nts.live/shows/bottega-radio/episodes/bottega-radio-16th-june-2022" property="og:url"/>
    try:
        nts_url = source.find('meta', attrs={'property': 'og:url'})['content']
        description = source.find('div', attrs={'class': 'description'})
        description = description.find('h3').getText() + ' (auto generated from ' + nts_url + ')'
        print(description)
        spotify_object.playlist_change_details(playlist['id'], description=str(description))
    except:
        pass

    try:
        date = source.find('span', attrs={'id': 'episode-broadcast-date'}).text.lstrip().rstrip()
        # if commas are in the date, remove them
        try:
            if "," in date:
                date = date.split(',')[1].lstrip().rstrip()
        except:
            pass
        playlist_name = playlist_name + ' | NTS ' + date
        print(playlist_name)
        spotify_object.playlist_change_details(playlist['id'], name=playlist_name)
    except:
        pass

    # another way to find the image url is in the meta tags, in the top of the html
    try:
        image = source.find('section', attrs={'class': 'background-image hidden-desktop'})
        image_url = image['style'].replace('background-image:url(', '').replace(')', '')
        print(image_url)

        # png images cannot be uploaded for playlist images
        if image_url.endswith('.png'):
            encoded_image  = convert_png_to_base64(image_url)
        else:
            encoded_image = base64.b64encode(requests.get(image_url).content).decode("utf-8")
        spotify_object.playlist_upload_cover_image(playlist['id'], encoded_image)
    except:
        pass

    return "Playlist created and added to Spotify"