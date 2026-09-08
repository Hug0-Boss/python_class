from flask import Flask, render_template
import os
from extension import bcrypt, mail, oauth, jwt
from auth.auth import auth_bp
from courses.routes import course_bp
from courses.student_route import st_course_bp
from config import Config
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt.init_app(app)
bcrypt.init_app(app)
oauth.init_app(app)
mail.init_app(app)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(course_bp, url_prefix="/api/instructor")
app.register_blueprint(st_course_bp, url_prefix="/api/student")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)