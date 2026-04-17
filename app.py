from flask import Flask
from datetime import timedelta

from models.user import db
from auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp
from routes.simulation_routes import sim_bp


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY']                     = 'processinsight-secret-2026'
    app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///processinsight.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME']     = timedelta(hours=2)

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sim_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)