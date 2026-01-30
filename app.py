from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from config import Config
from db import close_conn
from auth_routes import auth_bp
from sequence_routes import seq_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    JWTManager(app)

    CORS(
        app,
        origins=["http://localhost:3000", "https://helixpace.vercel.app/"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

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
