import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from config import Config

if __name__ == '__main__':
    port = getattr(Config, 'FLASK_PORT', 5000)
    print("=" * 60)
    print(f" 🚀 School Management System Backend Server")
    print(f" 🌐 Access at: http://localhost:{port}")
    print(f" 📂 Serving Frontend & REST APIs on port {port}")
    print("=" * 60)
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
