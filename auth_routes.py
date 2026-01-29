from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt

from db import query_one, execute, commit, rollback

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def _pw_bytes(pw: str) -> bytes:
    if not isinstance(pw, str):
        raise ValueError("password must be a string")
    return pw.encode("utf-8")

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    firstname = data.get("firstname")
    lastname = data.get("lastname")

    if not email or not password:
        return jsonify({"success": False, "message": "email and password are required"}), 400

    if not isinstance(password, str):
        return jsonify({"success": False, "message": "password must be a string"}), 400

    existing = query_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({"success": False, "message": "Email already registered"}), 409

    try:
        pw_hash = bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode("utf-8")

        affected, user_id = execute(
            """
            INSERT INTO users (email, firstname, lastname, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (email, firstname, lastname, pw_hash),
        )
        if affected == 0:
            rollback()
            return jsonify({"success": False, "message": "Failed to create user"}), 500

        commit()
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "data": {"id": user_id, "email": email}
        }), 201

    except Exception as e:
        rollback()
        return jsonify({"success": False, "message": "Registration failed", "error": str(e)}), 500


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "email and password are required"}), 400

    if not isinstance(password, str):
        return jsonify({"success": False, "message": "password must be a string"}), 400

    user = query_one(
        "SELECT id, password_hash FROM users WHERE email = %s",
        (email,)
    )

    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    ok = bcrypt.checkpw(_pw_bytes(password), user["password_hash"].encode("utf-8"))
    if not ok:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user["id"]))
    return jsonify({"access_token": token, "token_type": "bearer"}), 200
