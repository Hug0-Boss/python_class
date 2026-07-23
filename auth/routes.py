from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

print(bcrypt.generate_password_hash("Admin123").decode('utf-8'))