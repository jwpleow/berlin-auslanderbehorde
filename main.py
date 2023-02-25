import yaml

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from selenium.common.exceptions import TimeoutException
import time

import utilities

with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

print(f"Config: {config}")

if not all(keys in config for keys in ("appt_link", )):
    print(f"Missing keys in yaml config!")
    exit()

# options = webdriver.FirefoxOptions()
options = webdriver.ChromeOptions()
options.binary_location = r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe"
service = Service(r"D:\Downloads\chromedriver_win32\chromedriver.exe")

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=options, service=service)

# Open main appointment page
driver.get(config["appt_link"])

time.sleep(15)
# # Click the checkbox
driver.find_element(By.ID, "xi-cb-1").click()
print("Clicked checkbox")


# elem = utilities.WaitForElementID(driver, "xi-cb-1", 20)



# time.sleep(10000)
