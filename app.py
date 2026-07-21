from flask import Flask, render_template #type: ignore
from extension import (bcrypt, mail)
from auth.auth import auth_bp
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


bcrypt.init_app(app)
app.config['MAIL_SERVER'] = Config.MAIL_SERVER
app.config['MAIL_PORT'] = Config.MAIL_PORT
app.config['MAIL_USE_TLS'] = Config.MAIL_USE_TLS
app.config['MAIL_USERNAME'] = Config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = Config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = Config.MAIL_DEFAULT_SENDER

mail.init_app(app)
app.register_blueprint(auth_bp, url_prefix="/api/auth")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

    # create a react register page that accepts the infos from our db in table! Asides verification_token!!