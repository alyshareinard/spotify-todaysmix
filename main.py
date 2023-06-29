from typing import Optional
import logging
import streamlit as st
import spotipy
from bottle import route, run, request
from spotipy import oauth2
import random
from flask import Flask
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

cid = st.secrets["cid"]
secret = st.secrets["secret"]
redirect_URI = 'https://alyshareinard-spotify-todaysmix-main-j0043u.streamlit.app/'

scope = 'user-library-read user-read-private user-read-email playlist-read-private playlist-read-collaborative user-library-modify playlist-modify-private playlist-modify-public user-read-recently-played '

sp_oauth = oauth2.SpotifyOAuth(cid, secret,redirect_URI,scope=scope)#,cache_path=CACHE )
sp = spotipy.Spotify(auth_manager=sp_oauth)

#sp=get_user_information(get_access_token())

playlists = sp.current_user_playlists()
# the following code authenticates the user with spotify
def get_access_token() -> Optional[str]:
    try:
        token_info = sp_oauth.get_cached_token()

        if token_info:
            logging.info("Found cached token!")
            return token_info['access_token']
        else:
            url = request.url
            code = sp_oauth.parse_response_code(url)
            if code != url:
                logging.info("Found Spotify auth code in Request URL! Trying to get valid access token...")
                token_info = sp_oauth.get_access_token(code)
                return token_info['access_token']
    except Exception as e:
        logging.error(f"Error getting access token: {str(e)}")

    return None


def get_user_information(access_token: str):
    try:
        sp = spotipy.Spotify(access_token)
        # Rest of the code to get user information
        return sp
    except Exception as e:
        print(f"Error getting user information: {str(e)}")
        return None

# the following code is the streamlit app
st.title("Create today's mix")
addfavorites = st.checkbox("include all favorites")
playlists2combine = st.multiselect(
    'Which playlists do you want to hear',
    playlists['items'], [], format_func=lambda x:x['name'],
    )

excludefavorites = st.checkbox("exclude all favorites")
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

def create_from_playlists(playlists2combine, skip_songs, recent_songs, addfavorites):
    print("in create from playlists")
    print(len(playlists2combine))
    if addfavorites:
        includeSongs = sp.current_user_saved_tracks(limit=50)['items']
        includeSongs = includeSongs + sp.current_user_saved_tracks(limit=50, offset=50)['items']
    else:
        includeSongs = []


    todays_songs=[]
    filler=[]
    for item in playlists2combine:
    #    print(item['id'])
#        print(item)
        moreitems=True
        offset=0
        while moreitems: 
            playlist_songs = sp.playlist_tracks(item['id'], limit=100, offset=offset)
            n_items=len(playlist_songs)  
            print("here is next:") 
            print(playlist_songs['next']) 
            includeSongs = includeSongs + playlist_songs['items']
            if playlist_songs['next']:
                offset=offset+100
                moreitems=True
                print("getting more items")
            else:
                moreitems=False
                print("That's it for that playlist")

    #    print("\n\n")
    
    random.shuffle(includeSongs)
    for song in includeSongs:

        print(song['track']['name'],"\n")
#        print(song['track']['uri'],"\n")
        uri = song['track']['uri']
        if uri not in skip_songs and uri not in recent_songs:
            todays_songs.append(song['track']['uri'])
        elif uri in recent_songs:
            filler.append(song['track']['uri'])
        if len(todays_songs)>=100:
            break
    #        else:
    #            print("Skipping ", song['track']['name'])
    print("Today's songs", len(todays_songs))
    todays_songs=list(set(todays_songs))

    if len(todays_songs)<100:
        todays_songs=todays_songs+filler
    return(todays_songs[0:100])

#print(skip_songs)
#print("THIS IS ME!!!: ")
#print(sp.current_user())
#print(playlist_id)


print("before create today's mix")
print(len(playlists2combine))
if st.button("Create Today's mix!"):
    print("in create today's mix")
    print(len(playlists2combine))
    
    skip_songs=[]
    if excludefavorites:
        favorites = sp.current_user_saved_tracks()
        playlists2exclude.append(favorites)
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
    print("before create from playlists")
    print(len(playlists2combine))
    todays100=create_from_playlists(playlists2combine, skip_songs, recent_songs, addfavorites)
    print("Today's songs", len(todays100))
    sp.playlist_replace_items(playlist_id, todays100)
    st.write('added', len(todays100), 'songs to', playlist_today['name'])
    st.write("done! Go check it out")