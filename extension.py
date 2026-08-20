from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

bcrypt = Bcrypt()
mail = Mail()
jwt = JWTManager()
oauth = OAuth()