from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from config import Config

bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    app = Flask(__name__, static_folder=frontend_path, static_url_path='')

    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    app.url_map.strict_slashes = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    bcrypt.init_app(app)
    jwt.init_app(app)

    from database.db import init_db
    init_db(app)

    from routes.auth_routes import auth_bp
    from routes.teacher_routes import teacher_bp
    from routes.student_routes import student_bp
    from routes.attendance_routes import attendance_bp
    from routes.result_routes import result_bp
    from routes.notice_routes import notice_bp
    from routes.homework_routes import homework_bp
    from routes.timetable_routes import timetable_bp
    from routes.leave_routes import leave_bp
    from routes.notification_routes import notification_bp
    from routes.fee_routes import fee_bp
    from routes.report_routes import report_bp
    from routes.note_routes import note_bp
    from routes.settings_routes import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(student_bp, url_prefix='/api/students')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(result_bp, url_prefix='/api/results')
    app.register_blueprint(notice_bp, url_prefix='/api/notices')
    app.register_blueprint(homework_bp, url_prefix='/api/homework')
    app.register_blueprint(timetable_bp, url_prefix='/api/timetable')
    app.register_blueprint(leave_bp, url_prefix='/api/leaves')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(fee_bp, url_prefix='/api/fees')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(note_bp, url_prefix='/api/notes')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/teacher/<path:filename>')
    def teacher_pages(filename):
        return send_from_directory(os.path.join(app.static_folder, 'teacher'), filename)

    @app.route('/student/<path:filename>')
    def student_pages(filename):
        return send_from_directory(os.path.join(app.static_folder, 'student'), filename)

    @app.route('/css/<path:filename>')
    def css_files(filename):
        return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

    @app.route('/js/<path:filename>')
    def js_files(filename):
        return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

    @app.route('/api/health')
    def health_check():
        from database.db import get_db
        try:
            get_db().command('ping')
            return jsonify({'status': 'ok', 'database': 'connected'}), 200
        except Exception:
            return jsonify({'status': 'ok', 'database': 'connecting'}), 200

    @app.after_request
    def add_header(response):
        from flask import request
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        elif request.path.startswith('/css/') or request.path.startswith('/js/') or any(request.path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.ico', '.svg']):
            response.headers['Cache-Control'] = 'public, max-age=86400'
        return response

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({'success': False, 'error': 'Token has expired. Please login again.'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'success': False, 'error': 'Invalid token.'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'success': False, 'error': 'Authorization token required.'}), 401

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=Config.FLASK_PORT, debug=Config.DEBUG, use_reloader=False)
