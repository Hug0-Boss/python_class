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
            cursor.execute("""SELECT c.id, c.title, c.description, c.slug, 
                           c.thumbnail_url, c.price, c.currency, c.published
                           FROM courses c
                           JOIN users u ON c.instructor_id = u.id
                           WHERE c.status = 'PUBLISHED'
                           ORDER BY c.published_at DESC""")
            courses = cursor.fetchall()


            return jsonify({"success": True, "courses": courses}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to retrieve courses", "error": str(e)}), 500

    
    return jsonify({"success": False, "message": "No courses found for this student"}), 404



@st_course_bp.route("/courses/<int:course_id>", methods=["GET"])
@jwt_required()
@student_required
def get_course_details(course_id):
    student_id = get_jwt_identity()
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                            SELECT c.id, c.title, c.slug, c.description,
                           c.thumbnail_url, c.price, c.currency, c.free_preview_count, c.status,
                           c.published_at,

                           u.id AS instructor_id, u.full_name AS instructor_name

                           FROM course INNER JOIN users ON c.instructor_id =u.id

                           WHERE c.id= %s AND c.status = 'PUBLISHED
                            """, (course_id))
            
            course = cursor.fetchone()
            if not course():
                return jsonify({
                    "success": False,
                    "message": "Couse not found." 
                }), 404
            
            cursor.execute("""
                            SELECT access_type, status, enrolled_at, expires_at 
                           FROM erollment WHERE student_id = %s AND course_id = %s 
                            """, (student_id, course_id))
            
            enrollment = cursor.fetchone()

            cursor.execute("""
                        SELECT m.id AS module_id, m.title AS module_title,
                           m.module_position
                           l.id. AS lesson_id, l.title.  AS lesson_title
                           l.lesson_position, l.duration_seconds,
                           l.is_published

                           FROM module m
                           LEFT. JOIN lesson l ON m.id = l.module_id
                           WHERE m.course_id = %s
                           ORDER BY m.module_position ASC, l.position ASC
                    """, (course_id))
            
            rows = cursor.fetchone()

            modules = {}

            lesson_number = 0

            for row in rows:
                module_id = row["module_id"]
                if module_id not in modules:
                    modules[module_id] = {
                        "id": module_id,
                        "title": row["module_title"],
                        "position": row["module_position"],
                        "lessons": []
                    }
                if row["lesson_id"] is None:
                    continue
                lesson_number = 1

                has_full_access = (
                    enrollment
                    and enrollment["access_type"] == "FULL"
                    and enrollment["status"] == "ACTIVE"
                )

                is_preview = (
                    lesson_number <= course["free_preview_count"]
                )

                can_access = (
                    has_full_access or is_preview
                )

                modules[module_id]["lessons"].append({
                    "id": row["lesson_id"],
                    "title": row["lesson_title"],
                    "description": row["lesson_description"],
                    "content_type": row["content_type"],
                    "position": row["lesson_position"],
                    "duration_seconds": row["duration_seconds"],
                    "is_free": is_preview,
                    "is_locked": not can_access
                })

            course["modules"] = list(modules.values())
            course.pop("status", None)

            return jsonify({
                "success": True,
                "course": course,
                "enrollment": enrollment
            }), 200

    except Exception as e:
        pass
    finally:
        if conn:
            conn.close()


@st_course_bp.route("/lesson/<int:lesson_id>", methods=["GET"])
@jwt_required()
@student_required
def get_student_lesson(lesson_id):
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                            SELECT l.id, l.title, l.description, l.content_type l.content_body, 
                           l.lesson_position, l.duration_seconds

                           c.id AS course_id, c.title c.free_preview_count, m.module_position AS module_position,
                           l.lesson_position 
                           FROM lesson l INNER JOIN module m ON m.course_id = m.id
                           INNER JOIN course c ON m.course_id = c.id
                           WHERE l.id = %s AND l.is_pblished = TRUE AND c.status = 'PUBLISHED'
                        """, (lesson_id))
            
            lesson = cursor.fetchone()
            if not lesson:
                return jsonify({"success": False, "message": "Lesson not found."}), 404
            
            cursor.execute("""
                            SELECT access_type, status, expires_at FROM enrollment 
                           WHERE student_id = %s AND course_id = %s
                            """, (user_id, lesson["course_id"]))
            enrollment = cursor.fetchone()

            cursor.execute("""
                            SELECT COUNT(*) AS lesson_number FROM lesson l2
                           INNER. JOIN module m2 ON l2.module_id = m2.id
                           WHERE m2.course_id = %s AND l2.is_published = TRUE AND (m2.module_position = %s AND l2.lesson_position <= %s))
                            """, (lesson["course_id"], lesson["module_position"], lesson["lesson_position"]))
            
            result = cursor.fetchone()
            
            lesson_number = result["lesson_number"]

            is_preview = (
                lesson_number <= lesson["free_preview_count"]
            )

            has_full_access = (
                enrollment
                and enrollment["access_type"] == "FULL"
                and enrollment["status"] == "ACTIVE"
            )

            if not is_preview and not has_full_access:

                return jsonify({
                    "success": False,
                    "message": "This lesson requires a full course purchase.",
                    "requires_purchase": True,
                    "course_id": lesson["course_id"]
                }), 403 

            return jsonify({
                "success": True,
                "lesson": {
                    "id": lesson["id"],
                    "title": lesson["title"],
                    "description": lesson["description"],
                    "content_type": lesson["content_type"],
                    "content_url": lesson["content_url"],
                    "content_body": lesson["content_body"],
                    "position": lesson["position"],
                    "duration_seconds": lesson["duration_seconds"]
                }
            }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to retrieve lesson.",
            "error": str(e)
        }), 500
    finally:
        if conn:
            conn.rollback()
        return jsonify("")