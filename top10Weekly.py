import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'YOUR_SECRET_KEY'
TOKEN_INFO = 'token_info'

def get_top_tracks(sp):
    # Get your recently played tracks
    recently_played = sp.current_user_recently_played(limit=50)  # Limit to 50 tracks for analysis

    # Create a dictionary to count play counts for each track
    track_play_counts = {}
    
    # Analyze your recently played tracks and count play counts
    for track in recently_played['items']:
        track_uri = track['track']['uri']
        if track_uri in track_play_counts:
            track_play_counts[track_uri] += 1
        else:
            track_play_counts[track_uri] = 1

    # Sort the tracks by play count in descending order
    sorted_tracks = sorted(track_play_counts.items(), key=lambda x: x[1], reverse=True)

    # Extract the track URIs of the top tracks (e.g., top 10)
    top_tracks = [track_uri for track_uri, play_count in sorted_tracks[:10]]  # Change 10 to the desired number of tracks

    return top_tracks

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('create_top_10_weekly', _external=True))

@app.route('/createTop10Weekly')
def create_top_10_weekly():
    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect("/")

    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Get the user's playlists
    current_playlists = sp.current_user_playlists()['items']

    # Initialize variables
    top_tracks = get_top_tracks(sp)  # Get the top tracks based on your listening history
    playlist_name = "Top 10 Weekly"  # Change the name as needed

    # get the current user's id
    user_id = sp.current_user()['id']

    # Create the "Top 10 Weekly" playlist
    playlist_creation_response = sp.user_playlist_create(user_id, playlist_name, public=False, collaborative=False)

    # Check if the playlist creation was successful
    if 'id' in playlist_creation_response:
        top_10_weekly_playlist_id = playlist_creation_response['id']

        # Add the top tracks to the playlist
        sp.user_playlist_add_tracks(user_id, top_10_weekly_playlist_id, top_tracks)

        return ('Top 10 Weekly playlist created and updated successfully')
    else:
        return ('Error creating the playlist')

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', _external=False))
    
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = 'YOUR_CLIENT_ID',
        client_secret = 'YOUR_CLIENT_SECRET',
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private user-read-recently-played'
    )

app.run(debug=True)
