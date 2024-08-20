import os
import io
import pandas as pd
import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Set up logging
import logging

logging.basicConfig(level=logging.DEBUG)

# Read the credentials for Spotify and GCLOUD from the JSON file
with open('/usr/src/app/spotify_credentials.json', 'r') as f:
    credentials = json.load(f)

client_id = credentials['client_id']
client_secret = credentials['client_secret']
redirect_uri = credentials['redirect_uri']
username = credentials['username']

file_name = 'data_CSV.csv'

# Set environment vars
os.environ["SPOTIPY_CLIENT_ID"] = client_id
os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri

# Define scope
scope = 'user-library-read'
auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope,
                            show_dialog=True, cache_path='.cache')

# Create Spotify client
sp = spotipy.Spotify(auth_manager=auth_manager)

# Scrape current user saved tracks
limit = 50
offset = 0
favourite_tracks = []

# Retrieve tracks in batches of 50
while offset < 600:
    try:
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        favourite_tracks.extend(response['items'])
        offset += limit
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error: {e}")
        break

# Extract relevant track data
track_data = []
for idx, item in enumerate(favourite_tracks):
    track = item['track']
    track_data.append({
        'Index': idx + 1,
        'Artist': track['artists'][0]['name'],
        'Track Name': track["name"],
        'Album': track['album']['name'],
        'Release Date': track['album']['release_date'],
        'Duration (ms)': track['duration_ms'],
        'Popularity': track['popularity'],
        'Preview URL': track.get('preview_url', 'N/A')  # Handle cases where preview_url might be missing
    })

# Create a DataFrame
df_of_data = pd.DataFrame(track_data)

# Convert DataFrame to CSV in memory
buffer = io.BytesIO()
df_of_data.to_csv(buffer, index=False)
buffer.seek(0)

# Initialize Google Cloud Storage
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = '/usr/src/app/G_Drive_Credentials.json'

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)


# Check if the file already exists
def find_file_id(file_name):
    query = f"name='{file_name}'"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return None


# Find file ID or create a new one
file_id = find_file_id(file_name)

if file_id:
    # Update existing file
    request = drive_service.files().update(fileId=file_id, media_body=MediaIoBaseUpload(buffer, mimetype='text/csv'))
else:
    # Create new file
    file_metadata = {
        'name': file_name,
        'mimeType': 'text/csv'
    }
    request = drive_service.files().create(body=file_metadata,
                                           media_body=MediaIoBaseUpload(buffer, mimetype='text/csv'), fields='id')

try:
    file = request.execute()
    print("File uploaded successfully")
    print(f"File ID: {file.get('id')}")
    print(f"File URL: https://drive.google.com/file/d/{file.get('id')}/view")

    # Set permissions to make the file accessible
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(fileId=file.get('id'), body=permission).execute()
    print("File permissions updated successfully.")

except Exception as e:
    print(f"Upload failed: {e}")
