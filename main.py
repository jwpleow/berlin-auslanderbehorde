import yaml

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select

import playsound
import os

import time
import datetime
import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def LoadConfig(filename : str):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    logging.info(f"Config: {config}")
        
    if not all(keys in config for keys in ("appt_link", "nationality", "employment_section", "chrome_driver_path")):
        logging.error(f"Missing keys in yaml config!")
        exit()

    return config

def LaunchChrome():
    options = webdriver.ChromeOptions()
    # If you have a non-default chrome install
    # options.binary_location = r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe"
    service = Service(os.path.normpath(config["chrome_driver_path"]))

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    # Idky but firefox/edge both get autologged out instantly by the auslanderberhorde page
    driver = webdriver.Chrome(options=options, service=service)
    return driver

def InitialiseSession(driver, config) -> bool:
    try:
        # Open main appointment page
        driver.get(config["appt_link"])

        time.sleep(20)

        # Click the accept terms and conditions checkbox
        driver.find_element(By.ID, "xi-cb-1").click()

        # Click on next button
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
        time.sleep(15)

        # Set nationality
        nationality_select = Select(driver.find_element(By.ID, 'xi-sel-400'))
        nationality_select.select_by_visible_text(config["nationality"])
        time.sleep(2)

        # Set number of people
        people_select = Select(driver.find_element(By.ID, 'xi-sel-422'))
        people_select.select_by_visible_text("eine Person") # "eine Person", "zwei Personen", "drei Personen", ...
        time.sleep(2)

        # Family select
        family_select = Select(driver.find_element(By.ID, 'xi-sel-427'))
        family_select.select_by_visible_text("nein") # "ja" / "nein"
        time.sleep(2)

        # Click apply for residence permit
        driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[4]/div[2]/form/div[2]/div/div[2]/div[8]/div[2]/div[2]/div[1]/fieldset/div[8]/div[1]/div[1]/div[1]/div[1]/label").click()
        time.sleep(2)

        # Drop down Erwerbstätigkeit
        driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[4]/div[2]/form/div[2]/div/div[2]/div[8]/div[2]/div[2]/div[1]/fieldset/div[8]/div[1]/div[1]/div[1]/div[6]/div/div[3]").click()
        time.sleep(2)

        # Click employment section
        driver.find_element(By.XPATH, f"//*[contains(text(), '{config['employment_section']}')]").click()
        time.sleep(5)

        # Click Proceed (first time)
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
        time.sleep(20)

        logging.info("Session initialised.")
        return True
    except Exception as e:
        logging.warn(f"InitialiseSession threw exception: {e}")
        return False

def NoSlotsAvailableMessageBoxIsPresent(driver) -> bool:
    messageBoxes = driver.find_elements(By.ID, "messagesBox")
    return any("Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte" in boxes.text for boxes in messageBoxes)
    
config = LoadConfig("config.yaml")
driver = LaunchChrome()

start_time = time.time()
appt_available : bool = False
initialised : bool = False
ctr : int = 0

while (not appt_available):
    session_start_time = time.time()
    logging.info("Initialising session...")
    initialised = InitialiseSession(driver, config)
    ctr += 1
    if not initialised:
        continue
    while (not appt_available):
        try:
            # No free slots, try again...
            if NoSlotsAvailableMessageBoxIsPresent(driver):
                if (time.time() - session_start_time > 20 * 60): # Reset ourselves after 20 minutes, so we don't get possibly get a slot with too little time left
                    break
                driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
                time.sleep(20)
                ctr += 1
                logging.info(f"Button pressed {ctr} times.")
            else:
                curr_url = driver.current_url
                if "TerminBuchen/logout" in curr_url: # we've timed out, restart
                    logging.info("Session timed out. Restarting...")
                    break
                else: # the thing disappeared?
                    # Double check that the page has fully loaded
                    print(f"{datetime.datetime.now()} - We got a slot ?!?!?!?!")
                    logging.info("We got a slot ?!?!?!?!")
                    time.sleep(30) # Sleep some more just to double check that the page has loaded (TODO: think of better method)
                    if NoSlotsAvailableMessageBoxIsPresent(driver):
                        logging.info("Oh its a false positive")
                        continue
                    playsound.playsound(f"{os.path.dirname(__file__)}/ringtone-126505.mp3")
                    appt_available = True
        except Exception as e:
            logging.warn(f"Loop threw exception: {e}")
            pass

print(f"Got an appointment after only {time.time() - start_time} seconds! ({ctr} tries).")
           
