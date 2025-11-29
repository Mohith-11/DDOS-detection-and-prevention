# Gevent monkey-patching must happen BEFORE other imports (e.g., before importing Flask, socketio, etc.)
from gevent import monkey
monkey.patch_all()

# Now import the Flask app (adjust the import path if your app is in a different module)
# This assumes your Flask app object is named `app` in app.py
from app import app

# If you need any additional initialization, do it here.