from selenium import webdriver
from selenium.webdriver.support import expected_conditions as when
from selenium.webdriver.common.by import By as by
from selenium.webdriver.support.ui import WebDriverWait
import time; import os; import subprocess;
import requests; import discord;
from dotenv import load_dotenv

load_dotenv()

# credentials
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
discordUserId = os.getenv("DISCORD_USER_ID")

# configuration
mutualThresholdMale = 80
mutualThresholdFemale = 30
dailyConnectionThreshold = 15

# driver
driverPath = ''
if os.name == 'nt':
    driverPath = 'ChromeDrivers/win32/chromedriver'
else:
    driverPath = 'ChromeDrivers/linux64/chromedriver'

# xpaths
signInCheckPath = "//p[@class='main__sign-in-container']"
emailFieldPath = "//input[@aria-label='Email or Phone']"
passwordFieldPath = "//input[@type='password']"
loginButtonPath = "//button[@aria-label='Sign in']"
seeMoreButtonPath = "//Button[@aria-label='See all People you may know with similar roles']"
moreSuggestionsPath = "//h2[contains(., 'More suggestions for you')]"
moreSectionPath = "//section[@class='relative pb2']"
cardDivPath = "//div[@class='scaffold-finite-scroll__content']"
card1Path = "//li[@class='ember-view display-flex ']"
card2Path = "//li[@class='discover-fluid-entity-list--item']"
personNamePath = ".//span[@class='discover-person-card__name t-16 t-black t-bold']"
personLinkPath = ""
personMutualConnectionsPath = ".//span[@class='member-insights__reason pl1 text-align-center t-12']"
personConnectButtonPath = ".//li-icon[@type='connect']"
chatDownIconPath = "//li-icon[@type='chevron-down']"

# urls
connectionUrl = 'https://www.linkedin.com/mynetwork/'
loginUrl = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'

# port
port = 9000

# current directory
curDir = os.getcwd()

# commands
runBrowserCmd = f'"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  --remote-debugging-port={port} --user-data-dir="{curDir}\\cache"'

# Send Id's
ids = ''


def initBrowser():
    # subprocess.Popen(runBrowserCmd, shell=True, creationflags=subprocess.DETACHED_PROCESS)
    chromeOptions = webdriver.chrome.options.Options()
    chromeOptions.add_argument("--disable-infobars")
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument("--disable-extensions")
    # chromeOptions.add_argument("--window-size=800,800")
    chromeOptions.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36")
    # chromeOptions.add_argument("--incognito")
    chromeOptions.add_argument("use-fake-device-for-media-stream")
    chromeOptions.add_argument("use-fake-ui-for-media-stream")
    chromeOptions.add_argument("start-maximized")
    chromeOptions.add_argument(f"user-data-dir={curDir}\\cache")
    chromeOptions.add_experimental_option('excludeSwitches', ['enable-logging'])
    # chromeOptions.add_experimental_option("debuggerAddress", f"localhost:{port}")
    chromeOptions.add_argument("--headless=true")
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(driverPath), options=chromeOptions)
    return driver

def loginLinkedin(driver):
    driver.get(loginUrl)
    wait = WebDriverWait(driver, timeout=600)
    emailField = wait.until(when.element_to_be_clickable((by.XPATH, emailFieldPath)))
    emailField.send_keys(email)
    passwordField = wait.until(when.element_to_be_clickable((by.XPATH, passwordFieldPath)))
    passwordField.send_keys(password)
    loginButton = wait.until(when.element_to_be_clickable((by.XPATH, loginButtonPath)))
    loginButton.click()

def getConnectionPage(driver):
    driver.get(connectionUrl)
    if len(driver.find_elements(by.XPATH, signInCheckPath)) > 0:
        loginLinkedin(driver)
        driver.get(connectionUrl)

def openSeeMore(driver):
    wait = WebDriverWait(driver, timeout=600)
    seeMoreButton = wait.until(when.element_to_be_clickable((by.XPATH, seeMoreButtonPath)))
    driver.execute_script("arguments[0].scrollIntoView();", seeMoreButton)
    driver.execute_script("window.scrollBy(0, -250)")
    seeMoreButton.click()

def sendConnectionRequests(driver):
    global ids
    wait = WebDriverWait(driver, timeout=600)

    # Preload many cards
    # TODO Still it gets stuck on show more button
    wait.until(when.presence_of_element_located((by.XPATH, card1Path)))
    i = 0
    while i < 20:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        cards1 = driver.find_elements(by.XPATH, card1Path)
        cards2 = driver.find_elements(by.XPATH, card2Path)
        total = len(cards1)+len(cards2)
        if(total >= 200):
            break
        time.sleep(1)
        i += 1

    cnt = 0

    cards1 = driver.find_elements(by.XPATH, card1Path)
    cards2 = driver.find_elements(by.XPATH, card2Path)

    chatDownIcon = driver.find_elements(by.XPATH, chatDownIconPath)
    if len(chatDownIcon) > 0:
        chatDownIcon[0].click()

    cards1.extend(cards2)
    
    for card in cards1:
        if cnt == dailyConnectionThreshold:
            break;

        try:
            connectButton = WebDriverWait(card, timeout=2).until(when.visibility_of_element_located((by.XPATH, personConnectButtonPath)))
        except Exception:
            print("No connect button, continuing...")
            continue

        try:
            mutuals = WebDriverWait(card, timeout=2).until(when.visibility_of_element_located((by.XPATH, personMutualConnectionsPath))).text
        except Exception:
            print("No mutuals, continuing...")
            continue

        name = WebDriverWait(card, timeout=2).until(when.visibility_of_element_located((by.XPATH, personNamePath))).text
        link = card.find_element(by.TAG_NAME, 'a').get_attribute('href')

        r = requests.get(f"https://api.genderize.io/?name={name.split()[0]}")
        d = r.json()
        mutualThreshold = 0
        if d['gender'] == "female":
            mutualThreshold = mutualThresholdFemale
        else:
            mutualThreshold = mutualThresholdMale

        num = int(mutuals.split()[0])
        if num >= mutualThreshold:
            print(f"{name}: {link}")
            ids += f'{name}: {link}\n'
            driver.execute_script("arguments[0].scrollIntoView();", connectButton)
            driver.execute_script("window.scrollBy(0, -150)")
            connectButton.click()
            time.sleep(2)
            cnt += 1
        else:
            print("Low mutual count")

async def send_message(message, ids):
    try:
        await message.author.send(ids)
    except Exception as e:
        print(e)

def sendMessage():
    global ids
    TOKEN = os.getenv("DISCORD_TOKEN")
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        user = await client.fetch_user(discordUserId)
        await user.send(ids)
        await client.close()

    client.run(TOKEN)

if __name__ == '__main__':
    driver = initBrowser()
    getConnectionPage(driver)
    sendConnectionRequests(driver)
    sendMessage()