import requests
import json
from requests.auth import HTTPBasicAuth
from django.conf import settings
import base64
import pathlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os


def get_access_token():
    client_id = settings.SAFARICOM_AUTH_KEY
    client_secret = settings.SAFARICOM_AUTH_CONSUMER_SECRET

    token_endpoint = settings.SAFARICOM_AUTH_ENDPOINT



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
            print("Token endpoint:", token_endpoint)
            print("Response:", response.text)
            print("Check your SAFARICOM_AUTH_KEY and SAFARICOM_AUTH_CONSUMER_SECRET in .env")
            return False
    except Exception as error:
        print('TOKEN ERROR:', str(error))
        return False
    


def get_b2c_access_token():
    client_id = settings.SAFARICOM_BC2_AUTH_KEY
    client_secret = settings.SAFARICOM_B2C_CONSUMER_TIME
    
    token_endpoint = settings.SAFARICOM_AUTH_ENDPOINT

    

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
    

def encrypt_initiator_password_with_certificate_file(initiator_password, certificate_filename):
    # Read the certificate from the project base directory
    certificate_path = pathlib.Path(settings.BASE_DIR) / certificate_filename
    with open(certificate_path, 'r') as cert_file:
        certificate = cert_file.read()

    # Concatenate Initiator Password and Certificate
    data = (initiator_password + certificate).encode()

    # Use a key derivation function (KDF) to generate a key for encryption
    salt = os.urandom(16)  # Generate a random salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(initiator_password.encode())  # Derive key from the password

    # Initialize Cipher for AES encryption in CBC mode
    iv = os.urandom(16)  # Initialization vector
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the data before encryption
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt the padded data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Concatenate salt, IV, and encrypted data
    encrypted_message = salt + iv + encrypted_data

    # Base64 encode the encrypted message
    base64_encoded = base64.b64encode(encrypted_message).decode('utf-8')

    return base64_encoded