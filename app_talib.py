# ══════════════════════════════════════════════════════════════════════════════
#  app_talib.py  —  Talib-Awn · طالب عون
#  Flask application factory.
#  Merge with your existing app.py, or use as a standalone starter.
#
#  Install:
#    pip install flask flask-sqlalchemy flask-jwt-extended flask-cors pymysql
#
#  .env (copy next to this file):
#    DB_USER=root
#    DB_PASS=yourpassword
#    DB_HOST=localhost
#    DB_NAME=talibawn
#    JWT_SECRET=change-me-in-production
#    GMAIL_ADDRESS=...
#    GMAIL_APP_PASS=...
# ══════════════════════════════════════════════════════════════════════════════

import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

from models_talib import db
from routes_talib  import talib_bp

def create_app():
    app = Flask(__name__)

    # ── Database (MySQL via PyMySQL) ──────────────────────────────────────────
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'talibawn')

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
        '?charset=utf8mb4'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # ── JWT ───────────────────────────────────────────────────────────────────
    app.config['JWT_SECRET_KEY']          = os.environ.get('JWT_SECRET', 'dev-secret-change-me')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    app.config['JWT_REFRESH_TOKEN_EXPIRES']= timedelta(days=30)

    # ── Extensions ───────────────────────────────────────────────────────────
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}},
         supports_credentials=True)

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(talib_bp, url_prefix='/api')

    # ── Create tables on first run ────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return {"message": "Talib-Awn API running"}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
