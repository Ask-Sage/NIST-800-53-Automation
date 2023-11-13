import pandas as pd
import requests

# Read the CSV file
df = pd.read_csv('data/sp800-53r5-controls.csv')

# Constants for API URLs
GET_TOKEN_URL = "https://api.asksage.ai/user/get-token-with-api-key"
QUERY_URL = "https://api.asksage.ai/server/query"

# Function to get the access token
def get_access_token_with_api_key(username, api_key):
    data = {"email": username, "api_key": api_key}
    response = requests.post(GET_TOKEN_URL, json=data)
    response.raise_for_status()
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
    response.raise_for_status()
    return response.json()["message"]

# Get the access token
username = 'EMAIL HERE'
api_key = 'API KEY HERE'

access_token = get_access_token_with_api_key(username, api_key)

# Iterate through the DataFrame and update the Implementation column
for index, row in df.iterrows():
    combined_nist = format(row['Combined'])
    introduction_context = """I am Nic Chaillan the CEO of Ask Sage.
    We are creating the implementation details for each of the NIST 800-53 controls based on our cybersecurity posture context for our Ask Sage application.
    """

    security_context = """WRITE YOUR SECURITY CONTEXT HERE. RECOMMEND YOU FILL NIST 800 171 BY HAND AND COPY THE IMPLEMENTATION DETAILS HERE. 
    THIS IS WHAT WE DID FOR ASK SAGE.
    EXAMPLE (SMALL CUT FROM REAL THING):We are hosted on Azure Government and our backups are stored in the Azure Backup vault on a daily basis for all our resources and hourly basis for SQL backups.
    Our vector database which hosts our CUI customer data is backup every day.
    Our Azure OpenAI APIs runs on dedicated enclaves on Azure commercial FedRAMP high regions with two redundant APIs on East Coast and Central US.
    For end users, Ask Sage allows username/pw but this does NOT enable access to CUI. Only CAC authenticated users get access to datasets with CUI with MANUAL assignment from our team after verification of their eligibility. For cloud administrative access on our side, Ask Sage leverages MFA with Azure MFA one time password options. For Ask Sage administrative access Ask Sage leverage either CAC or MFA one time password options.
    Ask Sage has a full RBAC stack for all our cloud security/services but Ask Sage also brings a full Label Based Access Control to assign datasets to users based on need to know with MANUAL verification of CUI need to know by our team.
    Ask Sage is hosted on Azure Government at IL5. It runs on Kubernetes using AKS. CUI information is stored in our vector database in a container inside of AKS on Azure Government at IL5. The datasets are labels and datasets that has CUI data are labeled with "CUI" in the name. Those CANNOT be accessed without CAC authentication and are MANUALLY assigned by our administrators to users based on need to know. When Ask Sage end users ingest data, they are NOT allowed Saged to create a dataset with CUI in it UNLESS they authenticated with a CAC. Our Web Application Firewall prevents all access from foreign nations and only whitelisted NATO countries can access Ask Sage. Only users with CAC can access CUI.
    Ask Sage is a very lean team and only one person has access to administrative access at this time alongside our Microsoft selected partners. 
    """

    action = """Without introductary phrases, write the Ask Sage implementation details for this control with relevant information for our auditor and fill the blank values:
    """

    prompt_template = f"""{introduction_context}
    SECURITY CONTEXT ABOUT OUR PRODUCT:
    {security_context}
    END OF SECURITY CONTEXT.

    NIST CONTROL:
    {combined_nist}

    {action}"""

    prompt = prompt_template.format(introduction_context=introduction_context, security_context=security_context, combined_nist=combined_nist, action=action)

    if pd.isna(row['Implementation']):
        try:
            response = query_sage(access_token, prompt, 0, "all", "gpt4")
            df.at[index, 'Implementation'] = response
            print(row['Control Identifier'])
            print(response)

            # Save the updated DataFrame to a new CSV file
            df.to_csv('updated_sp800-53r5-controls.csv', index=False)

            # Do not remove or your API key might get banned
            print('Sleeping for 30s')
            time.sleep(30)
        except Exception as e:
            print(f"Error querying Ask Sage Server: {str(e)}")
            # Add error logging here

# End of code