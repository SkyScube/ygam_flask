#!/usr/bin/env python3
from src import create_app
from src.extensions import socketio

app = create_app(create_tables=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
