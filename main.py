import yaml

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions

import playsound
import os

import time
import datetime
import logging

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

def BypassAlerts(driver: webdriver.Chrome):
    try: 
        alert = driver.switch_to.alert # will throw if no alert
        alert.accept()
    except:
        pass

def CheckForInternalServerError(driver: webdriver.Chrome) -> bool:
    # Internal server error?
    errorMsgs = driver.find_elements(By.XPATH, f"//*[contains(text(), 'Internal Server Error')]")
    return len(errorMsgs) > 0

# Returns false if timeout hit
# Checks every 1s
def WaitForText(driver: webdriver.Chrome, elementPartialText : str, timeoutSecs : float) -> bool:
    startTime = time.time()
    while (time.time() - startTime) < timeoutSecs:
        foundElems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{elementPartialText}')]")
        if len(foundElems) > 0:
            logging.info(f"Found element of {elementPartialText}")
            return True
        time.sleep(1)

    return False

# Uses find_element
# Returns false if timed out
def WaitForElement(driver: webdriver.Chrome, searchBy, searchValue, timeoutSecs: float) -> bool:
    startTime = time.time()
    while (time.time() - startTime) < timeoutSecs:
        try:
            driver.find_element(searchBy, searchValue)
            return True
        except:
            pass
        time.sleep(1)
    return False

# Returns false if timed out
def WaitAndClickElement(driver: webdriver.Chrome, searchBy, searchValue, timeoutSecs: float) -> bool:
    startTime = time.time()
    while (time.time() - startTime) < timeoutSecs:
        try:
            # Internal server error?
            if CheckForInternalServerError(driver):
                logging.error("Internal server error during WaitAndClickElement!")
                return False
        
            driver.find_element(searchBy, searchValue).click()
            return True
        except:
            pass
        time.sleep(0.5)
    return False

def WaitAndSelectByVisibleText(driver: webdriver.Chrome, searchBy, searchValue: str, selectText: str, timeoutSecs: float) -> bool:
    startTime = time.time()
    while (time.time() - startTime) < timeoutSecs:
        try:
            selector = Select(driver.find_element(searchBy, searchValue))
            selector.select_by_visible_text(selectText)
            return True
        except:
            pass
        time.sleep(0.5)
    return False

def SelectFirstAppt(driver: webdriver.Chrome, timeoutSecs: float) -> bool:
    startTime = time.time()
    while (time.time() - startTime) < timeoutSecs:
        try:
            
            dateForm = driver.find_element(By.CSS_SELECTOR, "[data-handler=selectDay]")
            day = dateForm.text
            month = dateForm.get_attribute("data-month")
            year = dateForm.get_attribute("data-year")
            logging.info(f"Apptmt available on {day}-{month}-{year}")
            dateForm.click()
            time.sleep(1)

            selector = Select(driver.find_element(By.ID, "xi-sel-3"))
            alloptions = selector.options
            for option in alloptions:
                print(f"OPTIONS AVAILABLE IN APPT: {option.text}") 
            selector.select_by_index(0)
            time.sleep(0.5)
            driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
            # selector.select_by_visible_text(selectText)
            return True
        except:
            pass
        time.sleep(0.5)
    return False
        

def InitialiseSession(driver: webdriver.Chrome, config) -> bool:
    try:
        # Open main appointment page
        driver.get(config["appt_link"])
        time.sleep(1)
        BypassAlerts(driver)

        # Click the accept terms and conditions checkbox
        if not WaitAndClickElement(driver, By.ID, "xi-cb-1", 60):
            logging.warning("Timed out waiting for start page")
            return False
        # driver.find_element(By.ID, "xi-cb-1").click()

        # Click on next button
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
        
        # Set nationality
        if not WaitAndSelectByVisibleText(driver, By.ID, 'xi-sel-400', config["nationality"], 60):
            logging.warning("Timed out waiting for nationality dialogue")
            return False

        time.sleep(2) # if we don't sleep in between these calls a million boxes will spawn for some reason

        # number of people select
        if not WaitAndSelectByVisibleText(driver, By.ID, 'xi-sel-422', "eine Person", 10):
            logging.warning("Timed out waiting for number of people dialogue")
            return False
        
        time.sleep(2)

        # Family select
        if not WaitAndSelectByVisibleText(driver, By.ID, 'xi-sel-427', "nein", 10): # "ja" / "nein"
            logging.warning("Timed out waiting for family dialogue")
            return False

        time.sleep(3) 

        # Click apply for residence permit
        if not WaitAndClickElement(driver, By.XPATH, "/html/body/div[2]/div[2]/div[4]/div[2]/form/div[2]/div/div[2]/div[8]/div[2]/div[2]/div[1]/fieldset/div[8]/div[1]/div[1]/div[1]/div[1]/label", 20):
            logging.warning("Timed out waiting for residence permit boxes")
            return False
        
        time.sleep(2)

        # Drop down Erwerbstätigkeit
        if not WaitAndClickElement(driver, By.XPATH, f"//*[contains(text(), 'Erwerbstätigkeit')]", 20):
            logging.warning("Timed out waiting for Drop down Erwerbstätigkeit")
            return False

        # Click employment section
        if not WaitAndClickElement(driver, By.XPATH, f"//*[contains(text(), '{config['employment_section']}')]", 20):
            logging.warning("Timed out waiting to click the section for employment reason thing")
            return False
        
        time.sleep(5)

        # Click Proceed (first time)
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()

        logging.info("Session initialised.")
        return True
    except Exception as e:
        logging.warning(f"InitialiseSession threw exception: {e}")
        return False


# Returns true if we've loaded onto the appt page 
# Returns false when we get the no appt message OR timeout
def OnApptPage(driver: webdriver.Chrome, timeoutSecs: float) -> bool:
    startTime = time.time()

    while (time.time() - startTime) < timeoutSecs:
        try:
            # appt page has "Ausgewählte Dienstleistung" at the top
            apptPageElem = driver.find_elements(By.XPATH, f"//*[contains(text(), 'Ausgewählte Dienstleistung')]")
            if len(apptPageElem) > 0:
                logging.info(f"Found Ausgewählte Dienstleistung - There's an appointment?!")
                return True
            
            # Internal server error?
            if CheckForInternalServerError(driver):
                logging.error("Internal server error during OnApptPage!")
                return False
            
            # Check if we've got the no appt available message
            noApptMessageBoxes = driver.find_elements(By.ID, "messagesBox")
            noSlotsAvailable : bool = any("Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte" in boxes.text for boxes in noApptMessageBoxes)
            if noSlotsAvailable:
                return False
        except:
            pass
        time.sleep(0.5)
    return False
   

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

for mediapath in ["media/success_alarm.mp3", "media/error.mp3"]:
    if not os.path.isfile(os.path.abspath(mediapath)):
        raise RuntimeError(f"Cannot find {mediapath}. Are you running from the root folder?")

config = LoadConfig("config.yaml")
driver = LaunchChrome()

start_time = time.time()
appt_available : bool = False
initialised : bool = False
ctr : int = 0
failCtr : int = 0

while (not appt_available):
    session_start_time = time.time()
    logging.info("Initialising session...")
    initialised = InitialiseSession(driver, config)
    failCtr += 1
    ctr += 1
    if not initialised:
        continue

    if failCtr > 100:
        logging.error("We've failed too often... please feedback")
        try:
            # This may fail and throw an exception
            # play a sound in case we fail too much
            for i in range(5):
                playsound.playsound(os.path.abspath("media/error.mp3"))
        except Exception as e:
            logging.warn(f"{str(e)}")
            pass
        exit()

    while (not appt_available):
        try:
            if OnApptPage(driver, 60):
                logging.info(f"We got a slot ?!?!?!?!")
                try:
                    # Bring window to foreground
                    driver.switch_to.window(driver.current_window_handle)
                    SelectFirstAppt(driver, 20)
                    # This may fail and throw an exception
                    playsound.playsound(os.path.abspath("media/success_alarm.mp3"))
                except Exception as e:
                    exit()
                appt_available = True
            else:
                if (time.time() - session_start_time > 20 * 60): # Reset ourselves after 20 minutes, so we don't get possibly get a slot with too little time left
                    break

                curr_url = driver.current_url
                if "TerminBuchen/logout" in curr_url: # we've timed out, restart
                    logging.info("Session timed out. Restarting...")
                    break

                if not WaitAndClickElement(driver, By.ID, "applicationForm:managedForm:proceed", 60):
                    logging.warning("Timed out waiting for Weiter button in main loop")
                    initialised = False
                ctr += 1
                logging.info(f"Button pressed {ctr} times.")

        except Exception as e:
            logging.warn(f"Loop threw exception: {e}")
            break

print(f"Got an appointment after only {time.time() - start_time} seconds! ({ctr} tries).")
           
