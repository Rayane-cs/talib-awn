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
    }

    # ── JWT ────────────────────────────────────────────────────────────────────
    app.config['JWT_SECRET_KEY']           = os.environ.get('JWT_SECRET', 'change-me')
    app.config['JWT_ACCESS_TOKEN_EXPIRES']  = timedelta(days=7)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}}, supports_credentials=True)

    # ── Blueprint ──────────────────────────────────────────────────────────────
    app.register_blueprint(bp, url_prefix='/api')

    # ── Create all tables on first run ─────────────────────────────────────────
    with app.app_context():
        db.create_all()
        print('✅  Database tables ready.')

    return app


app = create_app()

if __name__ == '__main__':
    print('🚀  Starting Talib-Awn API on http://localhost:5000')
    app.run(debug=True, port=5000, host='0.0.0.0')
