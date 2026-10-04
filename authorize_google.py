from google_auth_oauthlib.flow import InstalledAppFlow

from google_workspace import SCOPES

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)
open("token.json", "w").write(creds.to_json())
print("saved token.json")
