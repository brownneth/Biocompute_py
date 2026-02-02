import os
import pymysql
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from db import close_conn
from auth_routes import auth_bp
from sequence_routes import seq_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    JWTManager(app)
    CORS(
        app,
        origins=["https://helixlabs-app.vercel.app", "http://localhost:3000"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    with app.app_context():
        try:
            print("Checking database tables...")
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                cursorclass=pymysql.cursors.DictCursor
            )
            cursor = conn.cursor()
            
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            statements = schema_sql.split(';')
            for stmt in statements:
                if stmt.strip():
                    cursor.execute(stmt)
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Database tables verified/created successfully.")
            
        except Exception as e:
            print(f"Table creation warning: {e}")

    app.register_blueprint(auth_bp)
    app.register_blueprint(seq_bp)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    # Close DB connection after request
    app.teardown_appcontext(close_conn)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)