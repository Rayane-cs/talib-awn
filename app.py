import os
import sys
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from models import db


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'mysql://avnadmin:AVNS_9zHa37lXSab5oRi7FxC@talib-awn-talibawn.l.aivencloud.com:27349/defaultdb?ssl-mode=REQUIRED'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY',
        'talib-awn-secret-change-in-production'
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
        print('[routes] Make sure routes.py is in the same folder as app.py.')
        print('[routes] The server will start but all /api/ endpoints will return 503.')

        from flask import Blueprint

        fallback = Blueprint('fallback', __name__)

        @fallback.route('/api/v1/<path:any>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        def missing_routes(any):
            return jsonify({
                'error': 'routes.py is missing',
                'fix':   'Place routes.py in the same folder as app.py and restart the server.'
            }), 503

        app.register_blueprint(fallback)

    with app.app_context():
        db.create_all()
        print('[db] Tables checked / created.')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

2. Open `Procfile`, change it to:
```
web: gunicorn app:app