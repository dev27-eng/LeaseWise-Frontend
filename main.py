from leasecheck.app import app

if __name__ == "__main__":
    app.config['SERVER_NAME'] = None
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
