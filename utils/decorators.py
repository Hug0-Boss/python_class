from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt


def instructor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):

        claims = get_jwt()
        role = claims.get("role")
        if role != "INSTRUCTOR":
            return jsonify({
                "sucess": False,
                "message": "Instructor access required."
            }), 403
        return fn(*args, **kwargs)

    return wrapper

def student_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):

        claims = det_jwt()
        role = claims.get("role")
        if role != "USER":
            return jsonify({
                "success": False,
                "message": "Student access required."
            }), 403
        return fn(*args, **kwargs)

    return wrapper