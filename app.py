from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from threading import Thread
from flask import Flask

app = Flask(__name__)

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

def run_watcher():
    while True:
        watch_video()
        time.sleep(300)  # pause 5 minutes

@app.route("/")
def home():
    return "Bienvenue sur le robot de visionnage automatique de ta vidéo Facebook !"

if __name__ == "__main__":
    # Lancer le robot en thread séparé pour ne pas bloquer Flask
    watcher_thread = Thread(target=run_watcher, daemon=True)
    watcher_thread.start()

    # Lancer le serveur Flask
    app.run(host="0.0.0.0", port=8000)