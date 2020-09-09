from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import requests
import schedule
import time
import os
import pickle
import os.path
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/script.external_request', 'https://www.googleapis.com/auth/spreadsheets']
API_ID = 'MNV0ou4t1szLTbfCq3FJmptwti6VF2dMb' 
i = '15:19'
    
def get_scripts_service():
    """Calls the Apps Script API.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Credentials path from the credentials .json file 
            # from step 3 from Google Cloud Platform section
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_id.json', SCOPES) 
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('script', 'v1', credentials=creds)

def trigger_script():
    service = get_scripts_service()
    request = {'function': 'scrapeData'} 

    try:
        response = service.scripts().run(body=request, scriptId=API_ID).execute()
        print('Running scraper')
        return 1
    except errors.HttpError as error:
        print(error.content)
        return 0

def get_current_html():
    r = requests.get('https://renewal.missouri.edu/student-cases/')
    r.raise_for_status()

    return r.content

def compare_html():
    current_html = str(get_current_html())

    if os.path.exists('cache.txt'):
        cached_file = open('cache.txt','r')
        cached_html = cached_file.read()
        cached_file.close()
        if current_html != cached_html:
            print('Website update detected')
            cached_file = open('cache.txt','w')
            cached_file.write(current_html)
            return 1   
        else:
            print('No changes to website')
        cached_file.close()
    else:
        cached_file = open('cache.txt','w')
        cached_file.write(current_html)
        cached_file.close()
    return 0

def refresh_tableau():
    url = 'https://public.tableau.com/profile/jacob.lagesse#!/vizhome/MizzouCovid-19/Dashboard1'
    driver = webdriver.Chrome(os.path.join(os.getcwd(), 'chromedriver'))
    driver.get(url)
    time.sleep(3)

    assert "Tableau Public" in driver.title

    try:
        driver.find_element_by_class_name('login-link').click()

        username = driver.find_element_by_id('login-email')
        username.clear()
        username.send_keys('jacoblagesse@gmail.com')

        password = driver.find_element_by_id('login-password')
        password.clear()
        password.send_keys('Wolfwar_1492')

        driver.find_element_by_id('signin-submit').click()

        time.sleep(5)

        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(5)
        button = driver.find_element_by_xpath('/html/body/div[1]/div[2]/section/div/div[2]/section[3]/div/figcaption/div[2]/div/div[2]/dl/div[1]/dd/button')
        button.click()

        time.sleep(10)
        print('Data Refreshed')
    finally:
        driver.quit()

def job():
    while compare_html() == 0:
        time.sleep(60)

    if trigger_script() == 1:
        time.sleep(30)
        refresh_tableau()

schedule.every().monday.at(i).do(job)
schedule.every().tuesday.at(i).do(job)
schedule.every().wednesday.at(i).do(job)
schedule.every().thursday.at(i).do(job)
schedule.every().friday.at(i).do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
