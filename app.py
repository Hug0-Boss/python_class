from flask import Flask, render_template #type: ignore
import os
from extension import (bcrypt, mail, oauth)
from auth.auth import auth_bp
from config import Config
from extension import jwt
from flask_cors import CORS


app = Flask(__name__)
app.config.from_object(Config)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt.init_app(app)
bcrypt.init_app(app)
oauth.init_app(app)
CORS(app)

mail.init_app(app)
app.register_blueprint(auth_bp, url_prefix="/api/auth")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

    # create a react register page that accepts the infos from our db in table! Asides verification_token!!