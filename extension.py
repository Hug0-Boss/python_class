from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_jwt_extended import JWTManager

bcrypt = Bcrypt()
mail = Mail()
jwt = JWTManager()