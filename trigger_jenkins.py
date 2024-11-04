import requests
from requests.auth import HTTPBasicAuth

# Jenkins server URL
JENKINS_URL = 'http://localhost:8080'
# Jenkins job name
JOB_NAME = 'wedeymove'
# Jenkins user credentials
USERNAME = 'wils'
API_TOKEN = '1137b5ee4ff4648ea9f7db3a92c5054c4a' //will have to remove this token in the future 

def trigger_jenkins_job():
    # Jenkins job URL
    job_url = f"{JENKINS_URL}/job/{JOB_NAME}/build"
    
    print(f"Triggering job '{JOB_NAME}' at URL: {job_url}")
    
    # Make the HTTP POST request to trigger the job
    response = requests.post(job_url, auth=HTTPBasicAuth(USERNAME, API_TOKEN))
    
    if response.status_code == 201:
        print(f"Job '{JOB_NAME}' triggered successfully.")
    else:
        print(f"Failed to trigger job '{JOB_NAME}'. Status code: {response.status_code}")
        print(response.text)

def write_love_letter():
    love_letter = """
    My Dearest Beloved,

    Words cannot express the depth of my affection for you. From the moment I met you, my heart knew that it had found its true home. Your presence in my life has brought me immense joy and happiness, and I am forever grateful for your love.

    Your kindness, compassion, and unwavering support mean the world to me. You are the light that brightens my darkest days and the strength that carries me through life's challenges. In your arms, I find solace and comfort, knowing that I am loved and cherished beyond measure.

    Every moment spent with you is a treasure, a precious memory that I hold dear to my heart. Your laughter is music to my ears, your smile is a ray of sunshine that warms my soul. With you by my side, I feel invincible, ready to face whatever life throws our way.

    My love for you knows no bounds, for you are my everything, my rock, my soulmate. I promise to cherish and adore you for all eternity, to stand by your side through thick and thin, to love and support you unconditionally.

    Forever yours,
    [Your Name]
    """

    # Print the love letter to the console
    print(love_letter)

if __name__ == "__main__":
    print("Starting Jenkins job trigger...")
    trigger_jenkins_job()
    print("Jenkins job trigger completed.")

    print("\nWriting a love letter...")
    write_love_letter()
    print("Love letter written.")
