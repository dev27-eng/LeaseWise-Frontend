from flask import Flask, render_template
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

@app.route('/')
def index():
    content = """
    <p>This is a simple screen component with white background.</p>
    """
    return render_template('screen.html', content=content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
