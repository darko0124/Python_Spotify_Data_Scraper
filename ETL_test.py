import os
import io
import pandas as pd
import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


#Read the credentials for Spotify and GCLOUD from the JSON file
with open('spotify_credentials.json', 'r') as f:
    credentials = json.load(f)

client_id = credentials['client_id']
client_secret = credentials['client_secret']
redirect_uri = credentials['redirect_uri']
username = credentials['username']

file_name = 'data_CSV.csv'

#Set environment vars
os.environ["SPOTIPY_CLIENT_ID"] = client_id
os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri #"https://localhost:8080"

#Define scope
scope = 'user-library-read'
username = username
auth_manager = SpotifyOAuth(client_id = client_id, client_secret= client_secret, redirect_uri= redirect_uri, scope=scope, show_dialog=True, cache_path='.cache')

#Create Spotify client
sp = spotipy.Spotify(auth_manager = auth_manager)

#Scrape current user saved tracks
limit = 50 #max tracks in one bach
offset = 0
favourite_tracks = [] #The list of the tracks

#Retrieve tracks in batches of 50:
while offset <500:
    try:
        response = sp.current_user_saved_tracks(limit = limit, offset=offset)
        favourite_tracks.extend(response['items'])
        offset += limit
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error: {e}")
        break

#Get the retrieved tracks in a list (it combines all batches in a full list, that's why it is not paginated):
track_data = []
for idx, item in enumerate(favourite_tracks):
    track = item['track']
    track_data.append({
        'Index': idx + 1,
        'Artist': track['artists'][0]['name'],
        'Track Name': track["name"]
    })

#Create a df
df_of_data = pd.DataFrame(track_data)

#Convert DF to csv in memory
buffer = io.BytesIO()
df_of_data.to_csv(buffer, index = False)
buffer.seek(0)

#Auth and upload
#Initialize GCLOUD Storage

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'G_Drive_Credentials.json'

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
drive_service = build('drive', 'v3', credentials=creds)


# Upload the CSV file to Google Drive
file_metadata = {
    'name': file_name,
    'mimeType': 'application/vnd.ms-excel'
}
media = MediaIoBaseUpload(buffer, mimetype='text/csv')

try:
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print("File uploaded successfully")
    print(f"File ID: {file.get('id')}")
    print(f"File URL: https://drive.google.com/file/d/{file.get('id')}/view")
except Exception as e:
    print(f"Upload failed: {e}")