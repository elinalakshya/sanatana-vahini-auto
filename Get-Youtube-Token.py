
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)
print(f"\nYT_CLIENT_ID={creds.client_id}\nYT_CLIENT_SECRET={creds.client_secret}\nYT_REFRESH_TOKEN={creds.refresh_token}")
