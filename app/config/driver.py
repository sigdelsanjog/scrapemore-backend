from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Chrome Driver
def get_chrome_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Disable sandboxing for headless environments
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Set up ChromeDriver
    driver = webdriver.Chrome(options=options)
    return driver

""" Add other drivers if necessary.
In future you can make it configurable 
to select the desired driver"""