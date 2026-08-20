from extension import oauth
from config import Config

google = oauth.register(
    name='google',
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid email profile'
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)