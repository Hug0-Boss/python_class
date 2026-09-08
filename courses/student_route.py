from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_connection
from utils.decorators import student_required
from extension import jwt


st_course_bp = Blueprint("st_course_bp", __name__)

@st_course_bp.route("/courses", methods=["GET"])
@jwt_required()
@student_required

def get_student_courses():
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Example query to retrieve student courses
            cursor.execute("""SELECT c.id, c.title, c.description, c.slug, c.thumbnail_url, c.price,
                            c.currency, c.published 
                            FROM courses c
                            JOIN users u ON c.instructor_id = u.id
                            WHERE c.status = 'PUBLISHED'
                            ORDER BY c.published_at DESC
                            """)
            courses = cursor.fetchall()
            return jsonify({"courses": courses}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"message": "Database connection error", "error": str(e)}), 500
    
    # Logic to retrieve student courses
    return jsonify({"message": "List of student courses"}), 200