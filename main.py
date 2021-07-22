import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def create_label(name: str) -> str:
    """
    Creates label with given name
    :param name: name of label to be created
    :return id of created label
    """
    label = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show"
    }
    result = service.users().labels().create(userId='me', body=label).execute()
    print(f"Created label with name {name}")
    return result['id']


def get_college_emails():
    # search for unread messages from an admissions team that has no label yet
    search_query = '{from:admission*@*.edu from:admissions*@*.edu} has:nouserlabels'
    # call api
    results = service.users().messages().list(userId='me', q=search_query).execute()
    for resource in results['messages']:
        # get names of all labels
        labels = service.users().labels().list(userId='me').execute()['labels']
        label_names = [label['name'] for label in labels]

        message = service.users().messages().get(userId='me', id=resource['id']).execute()
        headers = message['payload']['headers']
        # get "from" header
        from_header = next(header for header in headers if header['name'] == 'From')
        # get college name
        name = from_header['value'][:from_header['value'].find('<') - 1]
        print(f"Reading email from {name}")
        # label for specific school should be nested under the College label
        nested_name = f'College/{name}'

        if nested_name not in label_names:
            label_id = create_label(nested_name)
        else:
            label_id = next(item['id'] for item in labels if item['name'] == nested_name)

        body = {
            "addLabelIds": label_id
        }
        service.users().messages().modify(userId='me', id=resource['id'], body=body).execute()



def authenticate() -> Credentials:
    """
    Authenticates Gmail API session
    :return: credentials object
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    print("Authenticated!")
    return creds


if __name__ == '__main__':
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    get_college_emails()
