# LeaseCheck Flask Application

A Flask application for analyzing lease agreements and providing legal compliance information.

## Installation

```bash
pip install .
```

## Usage

After installation, you can run the application using:

```python
from leasecheck.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

## Features

- Terms of Service display
- Account setup
- Plan selection
- Legal documentation
- Onboarding process

## Configuration

The application requires the following environment variables:
- FLASK_SECRET_KEY: Secret key for Flask session management

## Development

To run the application in development mode:

1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Run the application: `python -m leasecheck.app`
