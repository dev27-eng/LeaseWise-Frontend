import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from multiprocessing import Process
from leasecheck.app import app

def run_flask():
    app.run(host='0.0.0.0', port=5000)

@pytest.fixture(scope="session", autouse=True)
def start_flask():
    # Start Flask in a separate process
    flask_process = Process(target=run_flask)
    flask_process.start()
    time.sleep(2)  # Give Flask time to start
    yield
    flask_process.terminate()

@pytest.fixture(scope="session")
def driver():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--ignore-certificate-errors')
    
    # Initialize the driver without specifying paths (let Selenium find them)
    driver = webdriver.Chrome(options=chrome_options)
    
    driver.implicitly_wait(10)
    yield driver
    driver.quit()
