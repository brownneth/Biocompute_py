from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from config import Config
from db import close_conn
from auth_routes import auth_bp
from sequence_routes import seq_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(seq_bp)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    # close DB connection after request
    app.teardown_appcontext(close_conn)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
