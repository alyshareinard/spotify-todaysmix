import streamlit as st
import spotipy
import os
from bottle import route, run, request
from spotipy import oauth2
import json
import random

from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

cid = st.secrets["cid"]
secret = st.secrets["secret"]
redirect_URI = 'https://alyshareinard-spotify-todaysmix-main-j0043u.streamlit.app/'

scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative user-library-modify playlist-modify-private playlist-modify-public user-read-recently-played '
#sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
#CACHE = '.spotipyoauthcache'
#client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
#sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

#results = sp.current_user_saved_tracks()
sp_oauth = oauth2.SpotifyOAuth(cid, secret,redirect_URI,scope=scope)#,cache_path=CACHE )
sp = spotipy.Spotify(auth_manager=sp_oauth)

playlists = sp.current_user_playlists()



@route('/')
def index():
        
    access_token = ""

    token_info = sp_oauth.get_cached_token()

    if token_info:
        print("Found cached token!")
        access_token = token_info['access_token']
    else:
        url = request.url
        code = sp_oauth.parse_response_code(url)
        if code != url:
            print("Found Spotify auth code in Request URL! Trying to get valid access token...")
            token_info = sp_oauth.get_access_token(code)
            access_token = token_info['access_token']

    if access_token:
        print("Access token available! Trying to get user information...")
        sp = spotipy.Spotify(access_token)
        results = sp.current_user()
        return results

    else:
        return htmlForLoginButton()

def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
    return htmlLoginButton

def getSPOauthURI():
    auth_url = sp_oauth.get_authorize_url()
    return auth_url

st.title("Create today's mix")
playlists2combine = st.multiselect(
    'Which playlists do you want to hear',
    playlists['items'], [], format_func=lambda x:x['name'],
    )
playlists2exclude = st.multiselect(
    'Playlists you do NOT want to include (all songs that also fall in the above playlist(s) will be removed)',
    playlists['items'], [], format_func=lambda x:x['name'],
    )

playlist_today = st.multiselect(
    'Choose playlist to fill (will delete all current contents)',
    playlists['items'], [], format_func=lambda x:x['name'],
    )
if playlist_today:
    playlist_today=playlist_today[0]
    playlist_id=playlist_today['id']
#print(playlist_id)

skip_songs=[]
for item in playlists2exclude:
#    print(item['id'])
    playlist_songs = sp.playlist(item['id'], additional_types=('track',))
#    print(playlist_songs)
#    print("\n\n")
    for song in playlist_songs['tracks']['items']:
#        print(song['track']['name'],"\n")
#        print(song['track']['uri'],"\n")
        skip_songs.append(song['track']['uri'])

recents = sp.current_user_recently_played()

recent_songs=[]
for song in recents['items']:
#        print(song['track']['name'],"\n")
#        print(song['track']['uri'],"\n")
#    print("Recent", song['track']['name'])
    recent_songs.append(song['track']['uri'])


todays_songs=[]
filler=[]
for item in playlists2combine:
#    print(item['id'])
    playlist_songs = sp.playlist(item['id'], additional_types=('track',))
#    print(playlist_songs)
#    print("\n\n")
    for song in playlist_songs['tracks']['items']:
#        print(song['track']['name'],"\n")
#        print(song['track']['uri'],"\n")
        uri = song['track']['uri']
        if uri not in skip_songs and uri not in recent_songs:
            todays_songs.append(song['track']['uri'])
        elif uri in recent_songs:
            filler.append(song['track']['uri'])
        else:
            print("Skipping ", song['track']['name'])
#print(todays_songs)
todays_songs=list(set(todays_songs))
random.shuffle(todays_songs)
if len(todays_songs)<100:
    todays_songs=todays_songs+filler

#print(skip_songs)
#print("THIS IS ME!!!: ")
#print(sp.current_user())
#print(playlist_id)
todays100=todays_songs[0:99]


if st.button("Create Today's mix!"):
#    sp.user_playlist_create(sp.current_user()['id'])
    sp.playlist_replace_items(playlist_id, todays100)
#    sp.playlist_remove_all_occurrences_of_items(playlist_id, skip_songs)

    st.write("done! Go check it out")