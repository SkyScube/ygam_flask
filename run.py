#!/usr/bin/env python3
"""
Main entry point for running the Ygam Flask application.
"""
from src import create_app

# Create the Flask application using factory pattern
# create_tables=True will attempt to create tables on startup
app = create_app(create_tables=True)

if __name__ == '__main__':
    # Run the development server
    app.run(debug=True, host='0.0.0.0', port=5000)
