from flask import Blueprint, request, jsonify
from email_validator import validate_email, EmailNotValidError
from extension import bcrypt
from db import get_connection
import secrets
from email_service import send_verification_mail

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "USER").upper()

    if role not in ["USER", "INSTRUCTOR"]:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if not fullname or not email or not password or not role:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        validate_email(email)
    except EmailNotValidError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    conn = None
    cursor = None

    cursor.execute(
            "SELECT id FROM Users WHERE email = %s",
            (email, ),
    )

    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Email already exists"}), 409
        

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters long"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    verification_token = secrets.token_urlsafe(32)
     
    # conn = None
    # cursor = None

    try:
       conn = get_connection()
       cursor = conn.cursor()

       cursor.execute(
             "INSERT INTO Users (fullname, email, password, role, verification_token) VALUES (%s, %s, %s, %s, %s)",
              (fullname, email, hashed_password, role, verification_token),
            )

       conn.commit()
       cursor.close()

       verification_link = (f"https://python-class-4k2p.onrender.com/api/auth/verify-email/{verification_token}")
       send_verification_mail(email, fullname, verification_link)
       return jsonify({
            "success": True,
            "message": "User registered successfully."
        }), 201

    except Exception as e:
         return jsonify({
            "success": False, 
            "message": "db connection failed"
        }), 500

    finally:
       if cursor:
        cursor.close()
       if conn:
        conn.close()
    
    # print(data)
    # return jsonify({"message": "User registered successfully"}), 201



@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    cursor = None
    # conn = None
    cursor = get_connection().cursor()

    cursor.execute(
        """
        SELECT id FROM Users WHERE verification_token=%s
        """, (token)
    )

    user = cursor.fetchone()
    if not user:
        cursor.close()
        return jsonify({
            "success": False,
            "message": "Invalid verification link."
        }), 400

    cursor.execute(
        """
        UPDATE users
        SET 
            is_verified = TRUE,
            verification_token = NULL
        WHERE id=%s
        """, (user[0],)
    )
    get_connection().commit()
    cursor.close()

    return jsonify({
        "success": True,
        "message": "Email verified successfully."
    })
