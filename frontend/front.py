import requests
from flask import Flask

BACKEND_LINK = "http://backend:5000/nhl/v1"

app = Flask(__name__)

def get_link():
  return BACKEND_LINK + "/get"

def update_link():
  return BACKEND_LINK + "/update"

@app.route("/")
def hello():
  return "<h1 style='color:blue'>Hello There!</h1>"

@app.route("/get")
def get():
  res = requests.get(get_link())
  return res.text

@app.route("/update")
def update():
  res = requests.get(update_link())
  return res.text

if __name__ == "__main__":
  app.run(host='0.0.0.0')
