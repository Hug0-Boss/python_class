from flask import Blueprint, jsonify, request
from slugify import slugify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_connection
from utils.decorators import instructor_required
import cloudinary.uploader

course_bp = Blueprint("courses", __name__)

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}


def allowed_video_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


@course_bp.route("/course", methods=["POST"])
@jwt_required()
@instructor_required
def course():
    user_id = get_jwt_identity()
    data = request.get_json()

    title = data.get("title")
    price = data.get("price")
    currency = data.get("currency", "NGN")
    free_count = data.get("free_count", 1)
    description = data.get("description", "")
    thumbnail = data.get("thumbnail", "")
    status = data.get("status") or "DRAFT"

    allowed_statuses = {"DRAFT", "PUBLISHED", "ARCHIVED"}
    
    if status not in allowed_statuses:
    return jsonify({
        "success": False,
        "message": "Invalid course status. Must be DRAFT, PUBLISHED, or ARCHIVED."
    }), 400

    if not title:
    return jsonify({"success": False, "message": "Course title must be provided."}), 400

    title = title.strip()
    if not title:
        return jsonify({"success": False, "message": "Course title must not be empty."}), 400
    
    try:
        price = float(data.get("price"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Price must be a valid number."}), 400
    
    if price <= 0:
        return jsonify({"success": False, "message": "Price must be greater than zero."}), 400
    
    try:
        free_count = int(data.get("free_count", 1))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "free_count must be a valid whole number."}), 400

    slug = slugify(title)
    if not slug:
        return jsonify({"success": False, "message": "Unable to generate course slug."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO course
                (instructor_id, title, slug, description, thumbnail_url, price, currency, status, free_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, title, slug, description, thumbnail, price, currency, status, free_count))

            course_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                "success": True,
                "message": "Course created successfully.",
                "course": {
                    "id": course_id,
                    "instructor": user_id,
                    "title": title,
                    "slug": slug,
                    "description": description,
                    "thumbnail": thumbnail,
                    "price": price,
                    "currency": currency,
                    "status": status,
                    "free_count": free_count
                }
            }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to create course.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/<int:course_id>/modules", methods=["POST"])
@jwt_required()
@instructor_required
def create_module(course_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Request body is required."}), 400

    title = data.get("title")
    description = data.get("description")
    position = data.get("position")

    if not title:
        return jsonify({"success": False, "message": "Module title is required."}), 400

    title = title.strip()
    if not title:
        return jsonify({"success": False, "message": "Title cannot be empty."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title FROM course WHERE id = %s AND instructor_id = %s
            """, (course_id, user_id))

            course_row = cursor.fetchone()
            if not course_row:
                return jsonify({"success": False, "message": "Course not found."}), 404

            if not position:
                cursor.execute("""
                    SELECT COALESCE(MAX(module_position), 0) + 1 AS next_position
                    FROM module WHERE course_id = %s
                """, (course_id,))
                position = cursor.fetchone()["next_position"]

            cursor.execute("""
                INSERT INTO module (course_id, title, description, module_position)
                VALUES (%s, %s, %s, %s)
            """, (course_id, title, description, position))

            module_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                "success": True,
                "message": "Module created successfully.",
                "module": {
                    "id": module_id,
                    "course_id": course_id,
                    "title": title,
                    "description": description,
                    "position": position
                }
            }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to create module.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/<int:course_id>", methods=["GET"])
@jwt_required()
@instructor_required
def get_course(course_id):
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM course WHERE id = %s AND instructor_id = %s
            """, (course_id, user_id))

            course_row = cursor.fetchone()
            if not course_row:
                return jsonify({"success": False, "message": "Course not found."}), 404

            return jsonify({"success": True, "message": "Course found.", "course": course_row}), 200

    except Exception as e:
        return jsonify({"success": False, "message": "Failed to retrieve course.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/<int:course_id>/modules", methods=["GET"])
@jwt_required()
@instructor_required
def get_course_module(course_id):
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM course WHERE id = %s AND instructor_id = %s
            """, (course_id, user_id))

            course_row = cursor.fetchone()
            if not course_row:
                return jsonify({"success": False, "message": "Course not found."}), 404

            cursor.execute("""
                SELECT id, course_id, title, description, module_position
                FROM module WHERE course_id = %s ORDER BY module_position ASC
            """, (course_id,))

            modules = cursor.fetchall()

            return jsonify({
                "success": True,
                "message": "All modules.",
                "course": {
                    "course_id": course_row["id"],
                    "title": course_row["title"],
                    "modules": modules
                }
            }), 200

    except Exception as e:
        return jsonify({"success": False, "message": "Failed to retrieve modules.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/modules/<int:module_id>", methods=["PUT"])
@jwt_required()
@instructor_required
def update_module(module_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Request body is required."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.id, m.title, m.description, m.module_position
                FROM module m
                INNER JOIN course c ON m.course_id = c.id
                WHERE m.id = %s AND c.instructor_id = %s
            """, (module_id, user_id))

            module = cursor.fetchone()
            if not module:
                return jsonify({"success": False, "message": "Module not found or you do not own this module."}), 404

            title = data.get("title", module["title"])
            description = data.get("description", module["description"])
            position = data.get("position", module["module_position"])

            title = title.strip()
            if not title:
                return jsonify({"success": False, "message": "Title cannot be empty."}), 400

            cursor.execute("""
                UPDATE module SET title = %s, description = %s, module_position = %s
                WHERE id = %s
            """, (title, description, position, module_id))

            conn.commit()
            return jsonify({"success": True, "message": "Module updated successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to update module.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/modules/<int:module_id>", methods=["DELETE"])
@jwt_required()
@instructor_required
def delete_module(module_id):
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.id FROM module m
                INNER JOIN course c ON m.course_id = c.id
                WHERE m.id = %s AND c.instructor_id = %s
            """, (module_id, user_id))

            module = cursor.fetchone()
            if not module:
                return jsonify({"success": False, "message": "Module not found or you do not own this module."}), 404

            cursor.execute("DELETE FROM module WHERE id = %s", (module_id,))
            conn.commit()

            return jsonify({"success": True, "message": "Module has been deleted successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to delete module.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("course/<int:module_id>/lesson", methods=["POST"])
@jwt_required()
@instructor_required
def create_lesson(module_id):
    user_id = get_jwt_identity()

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body is required."}), 400

    title = data.get("title")
    allowed_type = ["VIDEO", "DOCUMENT", "PDF", "LINK", "CODE"]
    content_type = data.get("content_type")
    content_url = data.get("content_url")
    content_body = data.get("content_body")
    is_free = data.get("is_free", True)

    if not title:
        return jsonify({"success": False, "message": "Lesson title must be provided."}), 400

    title = title.strip()
    if not title:
        return jsonify({"success": False, "message": "Lesson title must not be empty."}), 400

    if content_type not in allowed_type:
        return jsonify({"success": False, "message": "Lesson type not valid."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.id FROM module m
                INNER JOIN course c ON m.course_id = c.id
                WHERE m.id = %s AND c.instructor_id = %s
            """, (module_id, user_id))

            module = cursor.fetchone()
            if not module:
                return jsonify({"success": False, "message": "Module not found. You do not own this module."}), 404

            cursor.execute("""
                SELECT COALESCE(MAX(lesson_position), 0) + 1 AS next_position
                FROM lesson WHERE module_id = %s
            """, (module_id,))

            next_position = cursor.fetchone()["next_position"]

            cursor.execute("""
                INSERT INTO lesson (module_id, title, content_type, content_url, content_body,
                is_free, lesson_position, is_published)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (module_id, title, content_type, content_url, content_body, is_free, next_position, False))

            lesson_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                "success": True,
                "message": "Lesson created successfully.",
                "module": {
                    "id": module_id,
                    "lesson": {
                        "id": lesson_id,
                        "title": title,
                        "content_type": content_type,
                        "content_url": content_url,
                        "is_published": False,
                        "lesson_position": next_position
                    }
                }
            }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed creating a lesson.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/modules/<int:module_id>/lessons", methods=["GET"])
@jwt_required()
@instructor_required
def get_module_lessons(module_id):
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.id, m.course_id, m.title
                FROM module m
                INNER JOIN course c ON m.course_id = c.id
                WHERE m.id = %s AND c.instructor_id = %s
            """, (module_id, user_id))

            module = cursor.fetchone()
            if not module:
                return jsonify({"success": False, "message": "Module not found or you do not own this module."}), 404

            cursor.execute("""
                SELECT id, module_id, title, description, content_type, content_url,
                content_body, is_free, lesson_position, is_published, duration_seconds,
                created_at, updated_at
                FROM lesson WHERE module_id = %s ORDER BY lesson_position ASC
            """, (module_id,))

            lessons = cursor.fetchall()

            return jsonify({
                "success": True,
                "module": {
                    "id": module["id"],
                    "course_id": module["course_id"],
                    "title": module["title"]
                },
                "lessons": lessons
            }), 200

    except Exception as e:
        return jsonify({"success": False, "message": "Failed to retrieve lessons.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/lessons/<int:lesson_id>", methods=["PUT"])
@jwt_required()
@instructor_required
def update_module_lessons(lesson_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Request body is required."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT l.id, l.title, l.description, l.content_type, l.content_url,
                l.content_body, l.is_free
                FROM lesson l
                INNER JOIN module m ON l.module_id = m.id
                INNER JOIN course c ON m.course_id = c.id
                WHERE l.id = %s AND c.instructor_id = %s
            """, (lesson_id, user_id))

            lesson = cursor.fetchone()
            if not lesson:
                return jsonify({"success": False, "message": "Lesson not found or you do not own this lesson."}), 404

            title = data.get("title", lesson["title"])
            description = data.get("description", lesson["description"])
            content_type = data.get("content_type", lesson["content_type"])
            content_url = data.get("content_url", lesson["content_url"])
            content_body = data.get("content_body", lesson["content_body"])
            is_free = data.get("is_free", lesson["is_free"])

            title = title.strip()
            if not title:
                return jsonify({"success": False, "message": "Lesson title must not be empty."}), 400

            allowed_types = ["VIDEO", "DOCUMENT", "PDF", "LINK", "CODE"]
            if content_type not in allowed_types:
                return jsonify({"success": False, "message": "Lesson type not valid."}), 400

            if not isinstance(is_free, bool):
                return jsonify({"success": False, "message": "is_free must be a boolean value."}), 400

            cursor.execute("""
                UPDATE lesson SET title = %s, description = %s, content_type = %s,
                content_url = %s, content_body = %s, is_free = %s
                WHERE id = %s
            """, (title, description, content_type, content_url, content_body, is_free, lesson_id))

            conn.commit()
            return jsonify({"success": True, "message": "Lesson updated successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to update lesson.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/lessons/<int:lesson_id>", methods=["DELETE"])
@jwt_required()
@instructor_required
def delete_module_lessons(lesson_id):
    user_id = get_jwt_identity()

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT l.id FROM lesson l
                INNER JOIN module m ON l.module_id = m.id
                INNER JOIN course c ON m.course_id = c.id
                WHERE l.id = %s AND c.instructor_id = %s
            """, (lesson_id, user_id))

            lesson = cursor.fetchone()
            if not lesson:
                return jsonify({"success": False, "message": "Lesson not found or you do not own this lesson."}), 404

            cursor.execute("DELETE FROM lesson WHERE id = %s", (lesson_id,))
            conn.commit()

            return jsonify({"success": True, "message": "Lesson deleted successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to delete lesson.", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@course_bp.route("/lessons/<int:lesson_id>/video", methods=["POST"])
@jwt_required()
@instructor_required
def upload_lesson_video(lesson_id):
    user_id = get_jwt_identity()

    if "video" not in request.files:
        return jsonify({"success": False, "message": "No video file was provided."}), 400

    video_file = request.files["video"]

    if video_file.filename == "":
        return jsonify({"success": False, "message": "No video file was selected."}), 400

    if not allowed_video_file(video_file.filename):
        return jsonify({"success": False, "message": "Unsupported format. Use mp4, mov, avi, mkv, or webm."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT l.id FROM lesson l
                INNER JOIN module m ON l.module_id = m.id
                INNER JOIN course c ON m.course_id = c.id
                WHERE l.id = %s AND c.instructor_id = %s
            """, (lesson_id, user_id))

            lesson = cursor.fetchone()
            if not lesson:
                return jsonify({"success": False, "message": "Lesson not found or you do not own this lesson."}), 404

            try:
                upload_result = cloudinary.uploader.upload_large(
                    video_file,
                    resource_type="video",
                    folder="lessons",
                    public_id=f"lesson_{lesson_id}"
                )
            except Exception:
                return jsonify({"success": False, "message": "Video upload to Cloudinary failed."}), 502

            video_url = upload_result.get("secure_url")
            duration = upload_result.get("duration")

            cursor.execute("""
                UPDATE lesson SET content_type = 'VIDEO', content_url = %s, duration_seconds = %s
                WHERE id = %s
            """, (video_url, duration, lesson_id))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Video uploaded successfully.",
                "lesson": {
                    "id": lesson_id,
                    "content_url": video_url,
                    "duration_seconds": duration
                }
            }), 200

    except Exception:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Failed to upload video."}), 500
    finally:
        if conn:
            conn.close()