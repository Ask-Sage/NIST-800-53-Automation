import pandas as pd
import requests
import time
import os

# Constants
API_URL = "https://api.asksage.ai"
GET_TOKEN_URL = f"{API_URL}/user/get-token-with-api-key"
QUERY_URL = f"{API_URL}/server/query"

# Read the CSV file
df = pd.read_csv('data/sp800-53r5-controls.csv')

# Function to get the access token
def get_access_token_with_api_key(username, api_key):
    data = {"email": username, "api_key": api_key}
    response = requests.post(GET_TOKEN_URL, json=data)
    if response.status_code != 200:
        print(f"Error getting access token: {response.status_code} - {response.reason}")
        print(response.json())
        raise Exception("Error getting access token")
     
    return response.json()["response"]["access_token"]

# Function to query the Ask Sage Server Query API
def query_sage(token, prompt, temperature, dataset, model, count=0):
    headers = {"x-access-tokens": token}
    data = {
        "message": prompt,
        "temperature": temperature,
        "dataset": dataset,
        "model": model
    }
    response = requests.post(QUERY_URL, json=data, headers=headers)
    if response.status_code != 200:
        print(f"Error querying Ask Sage Server: {response.status_code} - {response.reason}")
        print(response.json())
        if count >= 3:
            raise Exception("Error querying Ask Sage Server")
        
        print('Sleeping for 20s')
        time.sleep(20)
        
        return query_sage(token, prompt, temperature, dataset, model, count+1)
    return response.json()["message"]

# Get the access token
username = os.getenv('ASK_SAGE_USERNAME')
api_key = os.getenv('ASK_SAGE_API_KEY')

access_token = get_access_token_with_api_key(username, api_key)

# Iterate through the DataFrame and update the Implementation column
for index, row in df.iterrows():
    combined_nist = row['Combined']
    prompt = f"""{introduction_context}
SECURITY CONTEXT ABOUT OUR PRODUCT:
{security_context}
END OF SECURITY CONTEXT.

NIST CONTROL:
{combined_nist}

{action}"""

    if pd.isna(row['Implementation']):
        response = query_sage(access_token, prompt, 0, "all", "gpt4")
        df.at[index, 'Implementation'] = response
    
        print(row['Control Identifier'])
        print(response)

        # Save the updated DataFrame to a new CSV file
        df.to_csv('updated_sp800-53r5-controls.csv', index=False)

        # Do not remove or your API key might get banned
        print('Sleeping for 30s')
        time.sleep(30)