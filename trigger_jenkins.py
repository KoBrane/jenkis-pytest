import requests
from requests.auth import HTTPBasicAuth

# Jenkins server URL
JENKINS_URL = 'http://localhost:8080'
# Jenkins job name
JOB_NAME = 'keyjobpython'
# Jenkins user credentials
USERNAME = 'wils'
API_TOKEN = '1137b5ee4ff4648ea9f7db3a92c5054c4a'

def trigger_jenkins_job():
    # Jenkins job URL
    job_url = f"{JENKINS_URL}/job/{JOB_NAME}/build"
    
    # Make the HTTP POST request to trigger the job
    response = requests.post(job_url, auth=HTTPBasicAuth(USERNAME, API_TOKEN))
    
    if response.status_code == 201:
        print(f"Job '{JOB_NAME}' triggered successfully.")
    else:
        print(f"Failed to trigger job '{JOB_NAME}'. Status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    trigger_jenkins_job()
