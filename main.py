from leasecheck.app import app

if __name__ == "__main__":
    # Enable external access and proper host handling
    app.config['SERVER_NAME'] = None  # Allow all host headers
    app.run(host='0.0.0.0', port=5000, debug=True)
