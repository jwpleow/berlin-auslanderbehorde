from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def WaitForElementID(webDriver, elemID : str, timeoutS: float):
    try:
        return WebDriverWait(webDriver, timeoutS).until(
            EC.presence_of_element_located((By.ID, elemID))
        )
    finally:
        return None