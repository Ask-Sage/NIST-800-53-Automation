# Import necessary libraries
import pandas as pd
import requests
import time
import os
from pathlib import Path

# Function to get the access token from Ask Sage API
def get_access_token_with_api_key(username, api_key):
    # Define the URL for the get-token endpoint
    url = "https://api.asksage.ai/user/get-token-with-api-key"
    # Prepare the data to be sent in the request
    data = {"email": username, "api_key": api_key}
    # Send a POST request to the URL with the data
    response = requests.post(url, json=data)
    # If the response status is not 200, print the response and raise an exception
    if int(response.json()["status"]) != 200:
        print(response.json())
        raise Exception("Error getting access token")
    # Return the access token from the response
    return response.json()["response"]["access_token"]

# Function to query the Ask Sage Server Query API
def query_sage(token, prompt, temperature, dataset, model, count=0):
    # Define the URL for the query endpoint
    url = "https://api.asksage.ai/server/query"
    # Prepare the headers for the request
    headers = {"x-access-tokens": token}
    # Prepare the data to be sent in the request
    data = {
        "message": prompt,
        "temperature": temperature,
        "dataset": dataset,
        "model": model
    }
    # Send a POST request to the URL with the data and headers
    response = requests.post(url, json=data, headers=headers)
    # If the response status is not 200, print the response and retry up to 3 times with a 20s delay between each attempt
    if int(response.json()["status"]) != 200:
        print(response.json())
        if count >= 3:
            raise Exception("Error querying Ask Sage Server")
        
        print('Sleeping for 20s')
        time.sleep(20)
        
        return query_sage(token, prompt, temperature, dataset, model, count+1)
    # Return the message from the response
    return response.json()["message"]

# Function to fill in a CSV file with NIST controls using the Ask Sage API
def fill_in_nist_csv(csv_path, username, api_key, introduction_context, security_context, action):
    # Get the access token
    access_token = get_access_token_with_api_key(username, api_key)

    # Check if the application is already in progress
    file_path = "in_progress.file"
    if os.path.exists(file_path):
        csv_file_path = 'updated_' + csv_path
    else:
        csv_file_path = 'data/' + csv_path
        # Create a file to indicate that the application is in progress
        with open('in_progress.file', 'w') as f:
            f.write('app is in progress')

    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)
    
    # Iterate through the DataFrame and update the Implementation column
    for index, row in df.iterrows():
        # Format the Combined column
        combined_nist = format(row['Combined'])
        # Prepare the prompt for the Ask Sage API
        prompt_template = """{introduction_context}
    SECURITY CONTEXT ABOUT OUR PRODUCT:
    {security_context}
    END OF SECURITY CONTEXT.

    NIST CONTROL:
    {combined_nist}

    {action}"""

        prompt = prompt_template.format(introduction_context=introduction_context, security_context=security_context, combined_nist=combined_nist, action=action)

        # If the Implementation column is empty, query the Ask Sage API and update the column with the response
        if pd.isna(row['Implementation']):
            response = query_sage(access_token, prompt, 0, "all", "gpt4")
            df.at[index, 'Implementation'] = response
        
            print(row['Control Identifier'])
            print(response)

            # Save the updated DataFrame to a new CSV file
            df.to_csv('updated_' + csv_path, index=False)

            # Sleep for 30s to avoid overloading the API
            print('Sleeping for 30s')
            time.sleep(30)
    
    # Remove the in progress file
    os.remove(file_path)
    
    print('COMPLETE!')

# Main function
if __name__ == "__main__":
    # Get the path to the CSV file from the environment variables or use a default value
    base_csv_path = os.environ.get('CSV_PATH', 'sp800-53r5-controls.csv')

    # Get the username and API key from the environment variables or use default values
    username = os.environ.get('ASKSAGE_USERNAME', 'PUT_USERNAME_HERE_IF_NOT_USING_ENVIRONMENT_VARIABLES')
    api_key = os.environ.get('ASKSAGE_API_KEY', 'PUT_API_KEY_HERE_IF_NOT_USING_ENVIRONMENT_VARIABLES')

    # Get the paths to the context files from the environment variables or use default values
    introduction_context_file = os.environ.get('INTRODUCTION_CONTEXT_FILE', 'data/introduction_context.txt')
    security_context_file = os.environ.get('SECURITY_CONTEXT_FILE', 'data/security_context.txt')
    action_file = os.environ.get('ACTION_FILE', 'data/action.txt')

    # Read the context files
    introduction_context = Path(introduction_context_file).read_text()
    security_context = Path(security_context_file).read_text()
    action = Path(action_file).read_text()

    # Call the function to fill in the CSV file
    fill_in_nist_csv(base_csv_path, username, api_key, introduction_context, security_context, action)
