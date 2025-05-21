from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def watch_video():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    video_url = "https://www.facebook.com/share/v/1YApvEgoWx/"

    try:
        driver.get(video_url)
        time.sleep(30)  # durée de la vidéo
    finally:
        driver.quit()

if __name__ == "__main__":
    while True:
        watch_video()
        time.sleep(300)  # attends 5 minutes avant la prochaine vue