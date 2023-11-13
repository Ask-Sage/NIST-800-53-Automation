import os
import pandas as pd
import requests
import time
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

# Set up logging
logging.basicConfig(level=logging.INFO)

# Read the CSV file
df = pd.read_csv('data/sp800-53r5-controls.csv')

# Get the username and API key from environment variables
username = os.getenv('USERNAME')
api_key = os.getenv('API_KEY')

@retry(stop=stop_after_attempt(3), wait=wait_fixed(20))
def make_request(url, headers=None, json=None):
    try:
        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error making request to {url}: {e}")
        raise

def get_access_token_with_api_key(username, api_key):
    url = "https://api.asksage.ai/user/get-token-with-api-key"
    data = {"email": username, "api_key": api_key}
    response = make_request(url, json=data)
    return response["response"]["access_token"]

def query_sage(token, prompt, temperature, dataset, model):
    url = "https://api.asksage.ai/server/query"
    headers = {"x-access-tokens": token}
    data = {
        "message": prompt,
        "temperature": temperature,
        "dataset": dataset,
        "model": model
    }
    response = make_request(url, headers=headers, json=data)
    return response["message"]

access_token = get_access_token_with_api_key(username, api_key)

# Rest of the code remains the same