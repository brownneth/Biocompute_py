import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import query_one, query_all, execute, commit, rollback

seq_bp = Blueprint("sequences", __name__, url_prefix="/sequences")

def is_valid_sequence(sequence: str) -> bool:
    return re.fullmatch(r"[ATGC]+", sequence or "", flags=re.IGNORECASE) is not None

def analyze_sequence(sequence: str):
    seq = (sequence or "").upper()
    length = len(seq)

    gc_count = len(re.findall(r"[GC]", seq))
    gc_content = round((gc_count / length) * 100, 2) if length else 0.00

    complement = {"A": "T", "T": "A", "G": "C", "C": "G"}
    reverse_complement = "".join(complement[b] for b in reversed(seq)) if length else ""

    return {"length": length, "gc_content": gc_content, "reverse_complement": reverse_complement}

def get_current_user_row():
    uid = get_jwt_identity()
    if not uid:
        return None
    return query_one("SELECT id, email, firstname, lastname, is_admin FROM users WHERE id = %s", (int(uid),))

@seq_bp.post("")
@jwt_required()
def create_sequence():
    user = get_current_user_row()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 401

    data = request.get_json(silent=True) or {}
    sequence = data.get("sequence", "")
    description = data.get("description")

    if not is_valid_sequence(sequence):
        return jsonify({"success": False, "message": "Invalid DNA sequence. Only A, T, G, C allowed."}), 400

    analysis = analyze_sequence(sequence)

    try:
        affected, seq_id = execute(
            """
            INSERT INTO sequences (user_id, sequence, description, length, gc_content, reverse_complement)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                sequence,
                description,
                analysis["length"],
                analysis["gc_content"],
                analysis["reverse_complement"],
            ),
        )

        if affected == 0:
            rollback()
            return jsonify({"success": False, "message": "Failed to save sequence."}), 500

        commit()

        created = query_one(
            """
            SELECT id, user_id, sequence, description, length, gc_content, reverse_complement, created_at
            FROM sequences
            WHERE id = %s
            """,
            (seq_id,),
        )

        return jsonify({"success": True, "message": "Sequence saved successfully.", "data": created}), 201

    except Exception as e:
        rollback()
        return jsonify({"success": False, "message": "Failed to save sequence", "error": str(e)}), 500


@seq_bp.get("/search")
@jwt_required()
def search_sequences():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"success": False, "message": "Provide query param q"}), 400

    # id search
    if q.isdigit():
        rows = query_all(
            "SELECT * FROM sequences WHERE id = %s",
            (int(q),)
        )
        return jsonify(rows), 200

    keyword = f"%{q}%"
    rows = query_all(
        """
        SELECT * FROM sequences
        WHERE description LIKE %s OR sequence LIKE %s
        """,
        (keyword, keyword),
    )
    return jsonify(rows), 200


@seq_bp.get("/me")
@jwt_required()
def get_user_sequences():
    user = get_current_user_row()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 401

    rows = query_all(
        """
        SELECT id, sequence, description, length, gc_content, reverse_complement, created_at
        FROM sequences
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user["id"],),
    )

    return jsonify({
        "success": len(rows) > 0,
        "message": "User sequences fetched successfully" if rows else "No sequences found",
        "data": rows,
    }), 200


@seq_bp.get("")
@jwt_required()
def get_all_sequences():
    user = get_current_user_row()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 401

    if not user["is_admin"]:
        return jsonify({"success": False, "message": "Admin access required"}), 403

    rows = query_all(
        """
        SELECT
          s.id,
          s.user_id,
          s.sequence,
          s.description,
          s.length,
          s.gc_content,
          s.reverse_complement,
          s.created_at,
          u.email,
          u.firstname,
          u.lastname
        FROM sequences s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
        """
    )

    if not rows:
        return jsonify({"success": False, "message": "No sequences found"}), 404

    return jsonify({"success": True, "message": "Sequences fetched successfully", "data": rows}), 200
