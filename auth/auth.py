from flask import Blueprint, request, jsonify, url_for
from email_validator import validate_email, EmailNotValidError
from extension import bcrypt
from db import get_connection
import secrets
from email_service import send_verification_mail
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
from oauth import google


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
        return jsonify({"error": "All fields are required "}), 400

    try:
        validate_email(email)
    except EmailNotValidError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM Users WHERE email = %s",
            (email,),
        )

        if cursor.fetchone():
            return jsonify({"success": False, "message": "Email already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        verification_token = secrets.token_urlsafe(32)

        cursor.execute(
            "INSERT INTO Users (fullname, email, password, role, verification_token) VALUES (%s, %s, %s, %s, %s)",
            (fullname, email, hashed_password, role, verification_token),
        )

        conn.commit()

        verification_link = f"https://python-class-4k2p.onrender.com/api/auth/verify-email/{verification_token}"
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

@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM Users
            WHERE verification_token = %s
            """, (token,)
        )

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid verification link."
            }), 400

        cursor.execute(
            """
            UPDATE Users
            SET 
                is_verified = TRUE,
                verification_token = NULL
            WHERE id=%s
            """, (user["id"],)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Email verified successfully."
        }), 200

    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/home", methods=["GET"])
def home():
    return "Flask is running!"

@auth_bp.route("/user", methods=["GET"])
def user():
    return jsonify({"success": True, "name": "HY Devinton", "skill": "Software Engineer"}), 200

# from flask import request, jsonify
from flask_jwt_extended import create_access_token

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    print(f"{email} - {password}")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fullname, email, password, role, is_verified FROM Users WHERE email=%s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

        if not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

        if not user["is_verified"]:
            return jsonify({"success": False, "message": "Please verify your email before logging in."}), 403

        access_token = create_access_token(identity=str(user["id"]), additional_claims={"role": user["role"], "email": user["email"]})

        
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "access_token": access_token,
            "user": {
                "id": user["id"],
                "fullname": user["fullname"],
                "email": user["email"],
                "role": user["role"]
            }
        }), 200

    finally:
        cursor.close()
        conn.close()



@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fullname, email
            FROM Users
            WHERE email=%s
        """, (email,))

        user = cursor.fetchone()
        if not user:
            return jsonify({
                "success": False,
                "message": "Email not found."
            }), 404
        
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(minutes=30)

        cursor.execute("""
            UPDATE Users
            SET reset_token = %s, expires_date = %s
            WHERE id = %s
        """, (reset_token, expires_at, user["id"]))



        reset_link = f"http://localhost:5173/reset-password/{reset_token}"

        html = f"""
        <h2>Password Reset Request</h2>
        <p>Hello {user['fullname']},</p>
        <p>We received a request to reset your password.</p>
        <p>
            <a href="{reset_link}"
               style="
                    background:#2563eb;
                    color:white;
                    padding:12px 20px;
                    text-decoration:none;
                    border-radius:6px;">
                Reset Password
            </a>
        </p>
        <p>This link will expire in <strong>30 minutes</strong>.</p>
        <p>If you didn't request a password reset, you can safely ignore this email.</p>
        <br>
        <p>Learning Platform Team</p>
        """

        send_verification_email(
            email,
            "Password Reset",
            html
        )

        return jsonify({
            "success": True,
            "message": "Password reset link sent to your email."
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()



@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    data = request.get_json()
    new_password = data.get("new_password")

    if not new_password:
        return jsonify({
            "success": False,
            "message": "New password is required."
        }), 400

    if new_password < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters long."
        }), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id
            FROM Users
            WHERE reset_token = %s AND expires_date > NOW()
        """, (token,))

        user = cursor.fetchone()
        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid or expired token."
            }), 400

        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

        cursor.execute("""
            UPDATE Users
            SET password = %s, reset_token = NULL, expires_date = NULL
            WHERE id = %s
        """, (hashed_password, user["id"]))

        return jsonify({
            "success": True,
            "message": "Password reset successful."
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/google", methods=["GET"])
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    print(f"Redirect URI: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)



@auth_bp.route('/google/callback', methods=["GET"])
def google_callback():

    try: 
        token = google.authorize_access_token()
        print(f"Token:{token}")
        user_info = token.get("userinfo")
        
        if not user_info:
            return jsonify({"success": False, "message": "Unable to retrieve user information."}), 400


        email = user_info.get("email")
        fullname = user_info.get("name")
        google_id = user_info.get("sub")

        if not email or not google_id:
            return jsonify({"success": False, "message": "Incomplete user information from Google."}), 400
        
        #check if google account already exists
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, u.fullname, u.email, u.role, u.is_verified
            FROM OAuthAccount o
            JOIN Users u ON o.user_id = u.id
            WHERE o.provider = %s AND o.provider_user_id = %s
        """, ('google', google_id))

        user = cursor.fetchone()
        if user:
            user_id = user["id"]
        else:
            #check if email already exists in Users table
            cursor.execute("""
                SELECT id FROM Users WHERE email = %s
            """, (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                user_id = existing_user["id"]

                #Link the Google account to the existing user
                cursor.execute("""
                    INSERT INTO OAuthAccount (user_id, provider, provider_user_id)
                    VALUES (%s, %s, %s)
                """, (user_id, 'google', google_id))
            else:
                #Create a new user and link the Google account
                cursor.execute("""
                    INSERT INTO Users (fullname, email, password, is_verified, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (fullname, email, None, True, 'user'))
                user_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO OAuthAccount (user_id, provider, provider_user_id)
                    VALUES (%s, %s, %s)
                """, (user_id, 'google', google_id))

        conn.commit()

        #Generate JWT token for the user
        access_token = create_access_token(
            identity=str(user_id),)
        
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Google authentication successful.",
            "access_token": access_token
        }), 200

    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"success": False, "message": f"Error during Google OAuth: {str(e)}"}), 500