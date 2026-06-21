from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

CLIENT_SECRET_FILE = "client_secret_787218201261-0v090qqnhjc4ceo934tbgqrpvt6q48fc.apps.googleusercontent.com.json"
TOKEN_FILE = "google_oauth_token.json"



flow = InstalledAppFlow.from_client_secrets_file(
    CLIENT_SECRET_FILE,
    SCOPES
)


creds = flow.run_local_server(
    port=8080,
    open_browser=False
)


with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())


print("DONE")