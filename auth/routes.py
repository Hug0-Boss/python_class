from flask_bcrypt import Bcrypt
import secrets

bcrypt = Bcrypt()

# print(bcrypt.generate_password_hash("Admin123").decode('utf-8'))

print(secrets.token_hex(32))
# print(secrets.token_hex(32))