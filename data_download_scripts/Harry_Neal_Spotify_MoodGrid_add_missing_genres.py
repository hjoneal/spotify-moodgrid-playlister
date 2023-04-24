import csv
import os
import re
import pandas as pd
import time
import joblib
from urllib.error import HTTPError


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

TEMP_PICKLE = "genre_retry_grouped_temp.pkl"
FULL_PICKLE = "genre_retry_grouped_full.pkl"

# load raw dataframe
df = pd.read_csv("./dataset_copy/1864pl_output.csv")

# select only nans
df_genre_nan = df[
    df['artist_genre'].isna()
]

#list of unique artists required
df_genre_nanlist = list(df_genre_nan['artists'].unique())


sleep_time = 0.2

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


# load the data if it has previously exited part way through, else instantiate an empty list
if os.path.exists(TEMP_PICKLE):
    data = joblib.load(TEMP_PICKLE)
    counter = len(data)
    # start from the index of most recent artist
    start_index = df_genre_nanlist.index(data[-1]['artist']) + 1
else:
    data = []
    counter = 0
    start_index = 0


for artist in df_genre_nanlist[start_index:]:
    if sleep_time < 10:
        try:    
            result = sp.search(artist)
            time.sleep(sleep_time)
            if result['tracks'] is not None:
                try:
                    artist_id = result['tracks']['items'][0]['artists'][0]['id']
                    try:
                        artist_url = sp.artist(artist_id)
                        time.sleep(sleep_time)
                        genre = artist_url['genres']

                        data_feature = {}
                        data_feature['artist'] = artist
                        data_feature['genre'] = genre
                        data.append(data_feature)
                        

                        print(f"Wrote genre for '{artist}' ({counter}/{len(df_genre_nanlist)})")
                    except:
                        print("Genre API exception, adding to sleep time")
                        sleep_time *= 1.2
                        print(f"sleep time is now {sleep_time}")
                except:
                    print("artist ID exception")

            else:
                print("result is None")

        except:
            print("Search GET error")

        counter += 1
        if counter % 200 == 0:
                joblib.dump(data, TEMP_PICKLE)        
    else:
        break             

joblib.dump(data, FULL_PICKLE)