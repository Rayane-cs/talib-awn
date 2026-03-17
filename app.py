import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from models import db


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:Kslrayane2006@localhost/club_chlef'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY',
        'talib-awn-super-secret-2026'
    )
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}})

    try:
        from routes import auth
        app.register_blueprint(auth)
        print('[routes] routes.py loaded successfully.')
    except ImportError:
        print('[routes] WARNING: routes.py not found.')

        from flask import Blueprint
        fallback = Blueprint('fallback', __name__)

        @fallback.route('/api/v1/<path:any>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        def missing_routes(any):
            return jsonify({
                'error': 'routes.py is missing',
                'fix': 'Place routes.py in the same folder as app.py and restart.'
            }), 503

        app.register_blueprint(fallback)

    with app.app_context():
        db.create_all()
        print('[db] Tables checked / created.')

    return app


# Required for gunicorn: Procfile should say -> web: gunicorn app:app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)