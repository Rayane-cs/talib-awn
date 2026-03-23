# ══════════════════════════════════════════════════════════════════════════════
#  app.py  —  Talib-Awn · طالب عون
#  Main Flask application. Run this file to start the server.
#
#  Install dependencies first:
#    python -m pip install flask flask-sqlalchemy flask-jwt-extended flask-cors pymysql python-dotenv
#
#  Then run:
#    python app.py
# ══════════════════════════════════════════════════════════════════════════════

import os
from dotenv import load_dotenv
load_dotenv()   # reads .env from the same folder

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

from models import db
from routes import bp
from middleware import log_request, log_response


def create_app():
    app = Flask(__name__)

    # ── MySQL ──────────────────────────────────────────────────────────────────
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'talibawn')

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
    }

    # ── JWT ────────────────────────────────────────────────────────────────────
    jwt_secret = os.environ.get('JWT_SECRET', 'change-me')
    if jwt_secret == 'change-me':
        print('⚠️  WARNING: Using default JWT secret. Set JWT_SECRET in .env for production!')
    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES']  = timedelta(days=7)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    JWTManager(app)
    
    # CORS - Allow all origins for development
    CORS(app, 
         resources={r'/api/*': {
             'origins': '*',
             'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
             'allow_headers': ['Content-Type', 'Authorization'],
             'expose_headers': ['Content-Type', 'Authorization'],
             'supports_credentials': True,
             'max_age': 3600
         }})

    # ── Request/Response Logging ───────────────────────────────────────────────
    app.before_request(log_request)
    app.after_request(log_response)

    # ── Blueprint ──────────────────────────────────────────────────────────────
    app.register_blueprint(bp, url_prefix='/api')

    # ── Create all tables on first run ─────────────────────────────────────────
    with app.app_context():
        db.create_all()
        print('✅  Database tables ready.')
        
        # Log database initialization
        try:
            from db_logger import DatabaseLogger
            DatabaseLogger.log_custom_change(
                'Database Initialized',
                'All tables created and database ready for use',
                'System'
            )
        except Exception:
            pass  # Don't fail if logging fails

    return app


app = create_app()

if __name__ == '__main__':
    print('🚀  Starting Talib-Awn API on http://localhost:5000')
    app.run(debug=True, port=5000, host='0.0.0.0')
