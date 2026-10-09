# This software is designed to automate the renewal process of books at the Regina Public Library.
# It uses Selenium WebDriver to interact with the library's website and perform actions such as logging in, navigating to the 'Due Soon' materials, and clicking the 'Renew' button for each book.
# The software also includes error handling to manage cases where no books are found to be renewed.
#
# Runs both locally (credentials from a .env file) and on GitHub Actions
# (credentials from repository secrets exposed as environment variables).

import os
import sys
import smtplib
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from email.message import EmailMessage

# Locally this loads .env; on GitHub Actions there is no .env, so it does nothing
# and the values come from the workflow's environment (GitHub Secrets).
load_dotenv()

# GitHub Actions always sets CI=true. Locally it is unset, so the browser opens
# visibly exactly as before.
IS_CI = os.getenv("CI", "").lower() == "true"

RPL_url = "https://www.reginalibrary.ca/myaccount/currently-borrowed/overdue-soon"

barcode = os.getenv("BARCODE")
password = os.getenv("PASSWORD")
SMTP_server = "smtp.gmail.com"
sender_email = os.getenv("EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
receiver_email = sender_email

# Fail fast with a clear message if a secret is missing or misnamed
missing = [
    name
    for name, value in (
        ("BARCODE", barcode),
        ("PASSWORD", password),
        ("EMAIL", sender_email),
        ("SENDER_PASSWORD", sender_password),
    )
    if not value
]
if missing:
    sys.exit(f"❌ Missing required environment variables / secrets: {', '.join(missing)}")

elements_to_be_scraped = {
    "Go to Login": "/html/body/div[1]/div[3]/a[1]",
    "Username Input": "/html/body/div[1]/header/div[2]/div/div[2]/div[2]/div/div/li/div/form/div[1]/input",
    "Password Input": "/html/body/div[1]/header/div[2]/div/div[2]/div[2]/div/div/li/div/form/div[2]/input",
    "Login Button": "/html/body/div[1]/header/div[2]/div/div[2]/div[2]/div/div/li/div/form/input[1]",
    "Book Name": "/html/body/div[1]/div[1]/main/div[2]/div/div/div[2]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/a",
    "'Renew' Button": "/html/body/div[1]/div[1]/main/div[2]/div/div/div[2]/div/div[2]/div[2]/div/div/div/div[3]/div[2]/form/input[1]"
}


def build_driver():
    options = webdriver.ChromeOptions()
    if IS_CI:
        # A CI runner has no display, so Chrome must run headless.
        # No window-size / resolution flags are set on purpose.
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")  # required in the runner's container-like environment
        options.add_argument("--disable-dev-shm-usage")  # /dev/shm is small on runners
    drv = webdriver.Chrome(options=options)
    if IS_CI:
        # Headless Chrome announces itself as "HeadlessChrome" in its user agent,
        # which some sites reject. Report it as regular Chrome instead.
        ua = drv.execute_cdp_cmd("Browser.getVersion", {})["userAgent"]
        drv.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua.replace("HeadlessChrome", "Chrome")})
    return drv


driver = build_driver()
exit_code = 0

try:
    driver.get(RPL_url)
    wait = WebDriverWait(driver, 20 if IS_CI else 10)  # runners are a bit slower than a laptop

    # Try to log in
    target_1 = wait.until(
        EC.element_to_be_clickable((By.XPATH, elements_to_be_scraped["Go to Login"]))
    )
    target_1.click()

    # Type your uname and password
    target_2 = wait.until(
        EC.visibility_of_element_located((By.XPATH, elements_to_be_scraped["Username Input"]))
    )
    target_2.send_keys(barcode)
    target_3 = driver.find_element(By.XPATH, elements_to_be_scraped["Password Input"])
    target_3.send_keys(password)
    # Click login
    target_4 = driver.find_element(By.XPATH, elements_to_be_scraped["Login Button"])
    target_4.click()

    # Create email message
    msg = EmailMessage()
    msg["Subject"] = "Hello from Python!"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content("A book from RPL renewed successfully.")

    # Send that message
    with smtplib.SMTP(SMTP_server, 587) as server:
        server.ehlo()  # Identify yourself to the server
        server.starttls()  # Secure the connection
        server.ehlo()  # Re-identify as an encrypted connection

        server.login(sender_email, sender_password)
        # Click 'Renew' button
        while True:
            try:
                book_name = driver.find_element(By.XPATH, elements_to_be_scraped["Book Name"]).text
                msg.set_content(f"Book '{book_name}' renewed successfully.")
                target_5 = wait.until(
                    EC.element_to_be_clickable((By.XPATH, elements_to_be_scraped["'Renew' Button"]))
                )
                target_5.click()
                server.send_message(msg)
                # Book titles are deliberately not printed: workflow logs can be public.
                print("🚀 Email sent successfully!")
            except (TimeoutException, NoSuchElementException):
                msg.set_content("No more books to be renewed today")
                server.send_message(msg)
                print("❌ No more books to renew.")
                break

except Exception as e:
    # Fail the workflow run so GitHub shows a red X (and emails you) instead of a false green check.
    exit_code = 1
    print(f"❌ An error occurred: {type(e).__name__}: {e}")
    try:
        # URL and title only. Screenshots / page source are not saved because
        # they would contain your account page and logs/artifacts may be public.
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
    except Exception:
        pass

finally:
    driver.quit()

print("Task completed")
sys.exit(exit_code)
