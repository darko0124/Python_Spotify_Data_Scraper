
🔍 Goal of the project :

- Make an ETL process to obtain data from Spotify using the Spotify API. After obtaining the data puts it into a CSV file and saves it into a Google drive storage. 
- The script is scheduled using a cron expression and a docker container to run it into a certain time everyday so it can obtain the latest changes and update the csv file.

⚙️ Tech Stack:
- Python
- Google Drive
- Docker

🖊️ User Guide:
 - Download all the files and add your Client ID, Client Secret and Username in spotify_credentials.json
 - For the G_Drive_Credentials.json the script you have to obtain it manually from GCloud Console -> API and Services -> Credentials -> Download Auth Client -> Download JSON
