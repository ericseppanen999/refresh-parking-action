import os,time,re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


PARKING_URL   = os.environ["PARKING_URL"]
LICENSE_PLATE = os.environ["LICENSE_PLATE"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]


def create_driver():
    opts = ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    return driver


def click_get_quote(driver):
    wait = WebDriverWait(driver, 30)

    # 1) Open the page
    driver.get(PARKING_URL)

    # 2) Wait for the Length of Stay panel to exist
    wait.until(
        EC.presence_of_element_located(
            (By.ID, "panel-LengthofStay")
        )
    )

    # 3) Find and open the HOURS dropdown inside Length of Stay
    #    We key off the "Hours" label so we don't depend on dynamic IDs.
    hours_dropdown = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@id='panel-LengthofStay']"
                "//p[contains(., 'Hours')]/ancestor::div[@role='button']"
            )
        )
    )
    hours_dropdown.click()

    # 4) Wait for the listbox of options to appear
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//ul[@role='listbox']")
        )
    )

    # 5) Click the "4" / "4 Hours" option (covers both cases)
    hours_option = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//ul[@role='listbox']"
                "//li[(contains(., '4') and contains(., 'Hour')) or normalize-space(.)='4']"
            )
        )
    )
    # JS click is often more reliable with MUI menus
    driver.execute_script("arguments[0].click();", hours_option)

    # 6) Click "Get Quote"
    get_quote_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[.//div//div[contains(text(), 'Get Quote')]]")
        )
    )
    get_quote_button.click()


def add_vehicle(driver):
    wait = WebDriverWait(driver, 20)
    vehicle_add_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//p[text()='Vehicle']"
                "/ancestor::div[contains(@class,'MuiAccordionSummary-root')]"
                "//button[normalize-space()='Add' and not(@disabled)]"
            )
        )
    )
    vehicle_add_button.click()
    plate_input = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@id='panel-Vehicle']//input[@placeholder='e.g. WDS4562']"
            )
        )
    )
    plate_input.clear()
    plate_input.send_keys(LICENSE_PLATE)
    vehicle_add_confirm = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@id='panel-Vehicle']//button[normalize-space()='Add']"
            )
        )
    )
    vehicle_add_confirm.click()


def add_receipt_email(driver):
    wait = WebDriverWait(driver, 20)
    receipt_add_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//p[text()='Receipt']"
                "/ancestor::div[contains(@class,'MuiAccordionSummary-root')]"
                "//button[normalize-space()='Add' and not(@disabled)]"
            )
        )
    )
    receipt_add_button.click()
    email_input = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@id='panel-Receipt']//input[@type='email']"
            )
        )
    )
    email_input.clear()
    email_input.send_keys(EMAIL_ADDRESS)
    receipt_add_confirm = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@id='panel-Receipt']//button[normalize-space()='Add']"
            )
        )
    )
    receipt_add_confirm.click()


def open_payment_and_start_session(driver):
    wait = WebDriverWait(driver, 20)
    payment_add_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//p[text()='Payment']"
                "/ancestor::div[contains(@class,'MuiAccordionSummary-root')]"
                "//button[normalize-space()='Add' and not(@disabled)]"
            )
        )
    )
    payment_add_button.click()
    start_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[.//div[contains(@class,'MuiTypography-h6') and "
                "(contains(., 'Start Session') or contains(., 'Pay and start session'))]]"
            )
        )
    )
    start_button.click()

def verify_session_remaining(driver, expected_hours: int = 4):
    wait = WebDriverWait(driver, 20)
    remaining_el = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//p[contains(., 'Remaining')]")
        )
    )
    text = remaining_el.text.strip()
    m = re.search(r"(\d+)\s*h\s+(\d+)\s*m", text)
    if not m:
        raise RuntimeError(f"Could not parse remaining time from text: {text!r}")

    hours = int(m.group(1))
    minutes = int(m.group(2))

    if not (expected_hours - 1 <= hours <= expected_hours and 0 <= minutes < 60):
        raise RuntimeError(
            f"Unexpected remaining time: {hours}h {minutes}m "
            f"(expected around {expected_hours}h, got banner {text!r})"
        )
    print(f"[OK] Parking session remaining: {hours}h {minutes}m ({text})")



def main():
    driver = create_driver()
    try:
        click_get_quote(driver)
        time.sleep(3)
        add_vehicle(driver)
        time.sleep(5)
        add_receipt_email(driver)
        time.sleep(5)
        open_payment_and_start_session(driver)
        time.sleep(5)
        verify_session_remaining(driver,expected_hours=4)
        time.sleep(1)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
