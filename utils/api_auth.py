import requests
import json
from requests.auth import HTTPBasicAuth
from django.conf import settings
import base64


def get_access_token():
    client_id = settings.SAFARICOM_AUTH_KEY
    client_secret = settings.SAFARICOM_AUTH_CONSUMER_SECRET
    token_endpoint = settings.SAFARICOM_AUTH_ENDPOINT
    params = {'grant_type': 'client_credentials'}

    # Combine the client ID and client secret for Basic Authentication
    auth_header = f"{client_id}:{client_secret}"
    base64_auth_header = base64.b64encode(auth_header.encode()).decode()
    try:
        headers = {
            'Authorization': f'Basic {base64_auth_header}'
        }

        response = requests.request("GET", token_endpoint+'?grant_type=client_credentials', headers = headers)
        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')
            return access_token
        else:
            print("Token request failed with status code:", response.status_code)
            return False
    except Exception as error:
        print('TOKEN ERROR:', str(error))
        return False