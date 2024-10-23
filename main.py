from flask import Flask, render_template
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

@app.route('/')
def index():
    content = """
    <div class="alert alert-info" role="alert">
        Welcome to the Flask Screen Component!
    </div>
    <p class="lead">
        This is a sample content area that demonstrates the screen component styling.
    </p>
    <div class="d-grid gap-2">
        <button class="btn btn-secondary">Sample Button</button>
    </div>
    """
    return render_template('screen.html', content=content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
