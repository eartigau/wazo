

# Define your login credentials
username = "eartigau"
password = "simp0136"

import requests


# Define the hotspot and construct the URL with parameters
#hotspot = 'L2093687'
#url = 'https://ebird.org/barchartData?r={}&bmo=1&emo=12&byr=1900&eyr=2099&fmt=tsv'.format(hotspot)

# osascript -e 'tell application "Safari" to open location  "https://ebird.org/barchartData?r=L2093687&bmo=1&emo=12&byr=1900&eyr=2099&fmt=tsv" '

#osascript -e 'tell application "Safari" to tell window 1 to set current tab to (make new tab with properties {URL:"https://ebird.org/barchartData?r=L2093687&bmo=1&emo=12&byr=1900&eyr=2099&fmt=tsv"})'


# Create a session to persist the login session
session = requests.Session()


headers = {
    'User-Agent': 'Safari/605.1.15',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://ebird.org/'
}

# Perform login
login_url = "https://ebird.org"  # Replace with the actual login URL
login_data = {
    "username": username,
    "password": password
}

# Send a POST request to the login URL with the login data
response = session.post(login_url, data=login_data, headers=headers)

# Check if login was successful (you need to customize this based on the response you get)
if response.status_code == 200:
    print("Login successful")
else:
    print("Login failed")
    exit()


url = 'https://ebird.org/barchartData?r=L2093687&bmo=1&emo=12&byr=1900&eyr=2099&fmt=tsv'
# Now, you can retrieve the content of the URL as an authenticated user
response = session.get(url, headers = headers)

# Check if the request was successful
if response.status_code == 200:
    # Print or save the content to a local file
    print(response.text)
else:
    print("Failed to retrieve content")








username = 'eartigau'
password = 'simp0136'


# Now, you can navigate to the desired URL after login
url = 'https://ebird.org/barchartData?r=L2093687&bmo=1&emo=12&byr=1900&eyr=2099&fmt=tsv'



from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time

# Set Chrome options to run in headless mode (without opening a browser window)
chrome_options = Options()
chrome_options.add_argument('--headless')

# Initialize the Chrome driver with the specified options
driver = webdriver.Chrome(options=chrome_options)

# Navigate to the login page
login_url = 'https://ebird.org'  # Replace with the actual login URL
driver.get(login_url)

# Find the username and password input fields and fill them with your credentials
username_input = driver.find_element_by_id(username)  # Replace 'username' with the actual ID of the username input field
password_input = driver.find_element_by_id(password)  # Replace 'password' with the actual ID of the password input field


username_input.send_keys(username)
password_input.send_keys(password)

# Submit the login form
password_input.send_keys(Keys.RETURN)

# Wait for a few seconds to ensure the page is loaded
time.sleep(5)

# Now, you can navigate to the desired URL after login
url = 'https://example.com/protected-page'  # Replace with the URL of the protected page you want to access
driver.get(url)

# Retrieve the page source or perform other actions as needed
page_source = driver.page_source

# Print the page source for demonstration purposes
print(page_source)

# Quit the driver
driver.quit()












############################################################################################################

import requests

# Define the login URL and payload
login_url = 'https://ebird.org/'
login_data = {
    'username': 'eartigau',
    'password': 'simp0136'
}

# Define the data URL and payload
data_url = 'https://ebird.org/barchartData'
data_payload = {
    'username': 'eartigau',
    'password': 'simp0136',
    'r': 'L2093687',
    'bmo': '1',
    'emo': '12',
    'byr': '1900',
    'eyr': '2099',
    'fmt': 'tsv'
}

# Create a session to persist cookies across requests
session = requests.Session()

# Perform login
login_response = session.post(login_url, data=login_data)

# Check if login was successful
if login_response.status_code == 200:
    print("Login successful")

    # Access data after successful login
    data_response = session.post(data_url, data=data_payload)

    # Check if access to the data was successful
    if data_response.status_code == 200:
        print("Access to data successful")
        print(data_response.text)  # Print or process the content of the response
    else:
        print("Failed to access data")
else:
    print("Login failed")