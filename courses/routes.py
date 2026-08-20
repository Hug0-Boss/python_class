from flask import Blueprint, jsonify, request
from slugify import slugify
from flask_jwt_extended import, jwt_required, get_jwt_identity
from db import get_connection

course_bp = Blueprint("courses", __name__)

@course_bp.route("/course", methods=["POST"])
@jwt_required()

def course():

    user_id = get_jwt_identity()
    print(user_id)
    data = request.get_json()

    title = data.get('title')
    price = data.get('price', 0)
    currency = data.get('currency', 'NGN')
    free_count = data.get('free_count', 1)
    slug = slugify(title)


    if not title:
        return jsonify({"success": False, "message": "Course title must not be empty"}), 400
    
    if not currency:
        return jsonify({"success": False, "message": "Course title must not be empty"}), 400
    
    if price <= 0:
        return jsonify({"success": False, "message": "Price must be greater than zero"}), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print(get_jwt_identity)
        cursor.execute("SELECT * FROM Users WHERE id = %s", (get_jwt_identity()))
    except Exception as e:
        return jsonify({"error": e})

    print(data)
    return jsonify({"message": "Welcome to courses."})

    # Python Slugify