OUTPUT_FILE_NAME = "auto_pl_bigdataset_29mar.csv"
OUTPUT_PICKLE_TEMP = "auto_pl_bigdataset_29mar.pkl"
OUTPUT_PICKLE_FULL = "auto_pl_bigdataset_29mar_v2.pkl"


# query names to search for playlists
happyqueries = ["happy", "positive", "ecstasy", "euphoric", "upbeat", "bliss"]
sadqueries = ["sad", "negative", "depress", "crying", "unhappy", "angry"]
energeticqueries = ["energetic", "lively", "dynamic", "aggressive", "high energy", "hard"]
chillqueries = ["chill", "relax", "mellow", "calm", "easy", "soft"]

# number of playlists returned with each search
limit = 3

# max playlists output for each query
max_playlists_per_query = 20

# time to sleep between API calls to avoid hitting rate limit
sleep_time = 0.25

# instantiate counters
pl_counter = 0
pl_per_query_counter = 0
querycounter = 0


import csv
import os
import re
import pandas as pd
import time
import joblib

import spotipy
import spotipy.util as util
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

import sys
import spotipy

import pprint as pp
import joblib
import atexit
import os

# keep track of running time
start_time = time.time()

## function to output the required variables given a Spotify playlist URI

def playlist_URI_features_to_csv(pl_uri, playlist_name, playlist_mood, query):  

    # Spotifiy API call is limited at 100 tracks
    # Add while loop to keep adding songs to 'tracks' until there are no more
    try:               
        results = sp.playlist_tracks(pl_uri)
        time.sleep(sleep_time)
        tracks = results["items"]
        while results['next'] and len(tracks) < 400:
            results = sp.next(results)
            time.sleep(sleep_time)
            tracks.extend(results['items'])
        
        pl_track_counter=0
        pl_length = len(tracks)

        if pl_length > 3:
            # extract name and artist
            if tracks is not None:
                for track in tracks:
                    if track["track"] is not None:
                        track_id = track["track"]["id"]

                        # add mood to dictionary to keep track
                        if playlist_mood not in data['tracks']:
                            data['tracks'][playlist_mood] = {}

                        # add track id to dictionary so we can avoid writing duplicates
                        if track_id not in data['tracks'][playlist_mood]:
                            track_name = track["track"]["name"]
                            artists = ", ".join(
                                [artist["name"] for artist in track["track"]["artists"]]
                            )
                            data['tracks'][playlist_mood][track_id] = {
                                'artist' : artists,
                                'track' : track_name,
                                'count' : 1}

                            popularity = track["track"]["popularity"]
                            explicit = track["track"]["explicit"]

                            #section to grab genre of each artist from separate API call
                            try:
                                artist_url = sp.artist(track["track"]["artists"][0]["external_urls"]["spotify"])
                                time.sleep(sleep_time)
                                artist_genre = artist_url["genres"] 
                            except:
                                artist_url= ""
                                artist_genre=""
                                
                            # get a dictionary for the audio features to add these to our csv output
                            if track["track"]["id"] is not None:

                                features = sp.audio_features(track["track"]["id"])
                                time.sleep(sleep_time)
                                
                                if features is not None:
                                    for feature in features:
                                        if feature is not None:

                                            danceability = feature.get("danceability", "NaN")
                                            energy = feature.get("energy", "NaN")
                                            key = feature.get("key", "NaN")
                                            loudness = feature.get("loudness", "NaN")
                                            mode = feature.get("mode", "NaN")
                                            speechiness = feature.get("speechiness", "NaN")
                                            acousticness = feature.get("acousticness", "NaN")
                                            instrumentalness = feature.get("instrumentalness", "NaN")
                                            liveness = feature.get("liveness", "NaN")
                                            valence = feature.get("valence", "NaN")
                                            tempo = feature.get("tempo", "NaN")
                                            duration_ms = feature.get("duration_ms", "NaN")
                                            time_signature = feature.get("time_signature", "NaN")

                                    # write to csv
                                    writer.writerow([track_id, track_name, artists, artist_genre, popularity, danceability, energy, \
                                                key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, \
                                                valence, tempo, duration_ms, time_signature, explicit, playlist_mood, query, playlist_name])
                                    
                                    pl_track_counter +=1
                                    data['ntracks'] += 1
                                    sum_playlists = data['playlists']
                                    sum_tracks = data['ntracks']
                                    
                                    print(f"Mood: {playlist_mood} | Query: {query} ({pl_per_query_counter}) | ({querycounter}/{totalqueries})  |  Playlist total: {sum_playlists}")
                                    print(f"Track total: {sum_tracks} | '{playlist_name}' | Track {pl_track_counter}/{pl_length} | {track_name} by {artists}")

                                    if sum_tracks % 200==0:
                                        print("--- Time elapsed ---")
                                        print("--- %s seconds ---" % round((time.time() - start_time), 2))
                                        print("--- %s minutes ---" % round((time.time() - start_time) / 60,2))
                                        print("--- %s hours ---" % round((time.time() - start_time) / 3600,2))                

                                else:
                                    print(f"No features found for the '{playlist_name}' track IDs.")
                            else:
                                print("Track ID not found")


                        else:
                            # if track already exists in the dictionary then we don't write it and we add to the counter
                            data['tracks'][playlist_mood][track_id]['count'] += 1
                            track_name = track["track"]["name"]
                            artists = ", ".join(
                                [artist["name"] for artist in track["track"]["artists"]]
                            )
                            print(f"{track_name} by {artists} added previously, no need to re-write")
                            pl_track_counter +=1


                    else:
                        print(f"Track not found")

            else:
                print(f"Playlist '{playlist_name}' not found")
        else:
            print(f"skipping playlist {playlist_name} as it contains less than 3 songs")
    except spotipy.SpotifyException:
        print('error so skipping this playlist')

#save function in case the script exits part way through
def save():
    joblib.dump(data, OUTPUT_PICKLE_TEMP)

# load the data if it has previously exited part way through, else instantiate an empty dict
def load():
    if os.path.exists(OUTPUT_PICKLE_TEMP):
        data = joblib.load(OUTPUT_PICKLE_TEMP)
    else:
        data = {
            'playlists': 0,
            'ntracks': 0,
            'offset': -1,
            'tracks': {}
        }
    return data

# load credentials from .env file
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")

# authenticate
client_credentials_manager = SpotifyClientCredentials(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET
)

# create spotify session object
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, status_retries=0)

scope = 'user-library-read'


# save the current output in case of error
atexit.register(save)

# load or instantiate (depending on if starting afresh or not)

data = load()
# data = joblib.load(OUTPUT_PICKLE_TEMP)

# if code has failed part way, load last mood and query to a variable
if os.path.isfile(OUTPUT_FILE_NAME):
    print(f"Resuming from {OUTPUT_FILE_NAME}")
    df = pd.read_csv(OUTPUT_FILE_NAME)
    # if file exists but with nothing written to it, start from beginning
    if len(df) == 0:
        start_from = 'beginning'
    else:
        last_row_index = len(df) - 1
        last_row_values = df.iloc[last_row_index].tolist()
        mood_of_last_output = last_row_values[-3]
        query_of_last_output = last_row_values[-2]
        # reset pl_per_query_counter 
        pl_per_query_counter = len(df[df['query']==query_of_last_output]['playlist_name'].unique())
        start_from = 'most_recent_query'
# if file doesn't exist, then start from the beginning
else:
    start_from = 'beginning'

# create query list to iterate over
fullquerylist = sadqueries + happyqueries + chillqueries + energeticqueries
totalqueries = len(fullquerylist)

# if continuing
if start_from == 'most_recent_query':
    # reset queries to start from the most recent, if we are continuing the script
    if query_of_last_output in fullquerylist:
        index_of_last_query = fullquerylist.index(query_of_last_output)
        newquerylist = fullquerylist[index_of_last_query:]
        #reset query counter
        querycounter = index_of_last_query
    # if we are adding new queries, loop over the full list
    else:
        newquerylist = fullquerylist
        querycounter = 0
        data['offset'] = -1
        pl_per_query_counter = 0

    # append to existing csv file
    with open(OUTPUT_FILE_NAME, "a", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        for query in newquerylist:
            querycounter += 1
            if query in happyqueries: # set the playlist_mood
                playlist_mood = 'happy'
            elif query in sadqueries:
                playlist_mood = 'sad'
            elif query in energeticqueries:
                playlist_mood = 'energetic'
            elif query in chillqueries:
                playlist_mood = 'chill'
            else:
                print("not in query list")
            
            # continue until a certain number of playlists per query has been reached
            while pl_per_query_counter <= max_playlists_per_query:
                # offset scrolls the search results along to the next set
                offset = 0 if data['offset'] < 0 else data['offset'] + limit
                # search playlists using query
                results = sp.search(query, limit=limit, offset=offset, type='playlist')
                playlist = results['playlists']
                # update offset
                data['offset'] = playlist['offset'] + playlist['limit']
                time.sleep(sleep_time)
                playlist = results['playlists']
                if playlist is not None:
                    for item in playlist['items']:
                        playlist_name = item['name']
                        pl_uri = item['id']
                        # function that reads features from every track in playlist
                        playlist_URI_features_to_csv(pl_uri, playlist_name, playlist_mood, query)
                        pl_counter += 1
                        pl_per_query_counter += 1
                        data['playlists']+=1             

                    if playlist['next']:
                        results = sp.next(playlist)
                        playlist = results['playlists']
                    else:
                        playlist = None

                else:
                    print("playlist empty")
            
            #reset data['offset'] back to -1 and playlist counter to 0 for the new query
            pl_per_query_counter = 0
            data['offset'] = -1

else:
    # if start_from == 'beginning'
    # create csv file
    with open(OUTPUT_FILE_NAME, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # write header column names
        writer.writerow(["track_id", "track_name", "artists", "artist_genre", "popularity", 'danceability', 'energy', 'key',\
                    'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness',\
                    'valence', 'tempo', 'duration_ms', 'time_signature', 'explicit', 'playlist_mood', 'query', 'playlist_name'])

        for query in fullquerylist:
            querycounter += 1
            if query in happyqueries:
                playlist_mood = 'happy'
            elif query in sadqueries:
                playlist_mood = 'sad'
            elif query in energeticqueries:
                playlist_mood = 'energetic'
            elif query in chillqueries:
                playlist_mood = 'chill'
            else:
                print("not in query list")
            
            while pl_per_query_counter <= max_playlists_per_query:
                offset = 0 if data['offset'] < 0 else data['offset'] + limit
                results = sp.search(query, limit=limit, offset=offset, type='playlist')
                playlist = results['playlists']
                data['offset'] = playlist['offset'] + playlist['limit']
                time.sleep(sleep_time)
                playlist = results['playlists']
                if playlist is not None:
                    for item in playlist['items']:
                        playlist_name = item['name']
                        pl_uri = item['id']
                        playlist_URI_features_to_csv(pl_uri, playlist_name, playlist_mood, query)
                        pl_counter += 1
                        pl_per_query_counter += 1
                        data['playlists']+=1             

                    if playlist['next']:
                        results = sp.next(playlist)
                        playlist = results['playlists']
                    else:
                        playlist = None

                else:
                    print("playlist empty")
            
            #reset data['offset'] back to -1 and playlist counter to 0 for the new query
            pl_per_query_counter = 0
            data['offset'] = -1
        

print("--- Time elapsed ---")
print("--- %s seconds ---" % round((time.time() - start_time), 2))
print("--- %s minutes ---" % round((time.time() - start_time) / 60,2))
print("--- %s hours ---" % round((time.time() - start_time) / 3600,2))

joblib.dump(data, OUTPUT_PICKLE_FULL)