"""
Run script for Node Engine POC Flask server.
Usage: python run.py
"""

from views import run_server

if __name__ == '__main__':
    print("Starting Node Engine POC server...")
    print("Open http://localhost:5000 in your browser")
    run_server(host='0.0.0.0', port=5000, debug=True)
