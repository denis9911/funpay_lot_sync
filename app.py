from flask import Flask, render_template
import json

app = Flask(__name__)

def load_data():
    with open("merged.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_images():
    with open("games_images.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def index():
    data = load_data()
    images = load_images()  # словарь { "Game Name": "/images/file.webp" }
    return render_template("index.html", data=data, images=images)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
