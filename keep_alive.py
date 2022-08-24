from flask import Flask
from threading import Thread
# this file was made to keep the bot running even when the tab is closed, this is allowed from replit themselves

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello"

def run():
  app.run(host='0.0.0.0',port=8042)

def keep_alive():
    t = Thread(target=run)
    t.start()
