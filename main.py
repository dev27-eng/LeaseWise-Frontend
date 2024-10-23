from flask import Flask, render_template
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

@app.route('/')
def index():
    return render_template('screen.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome_screen.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
