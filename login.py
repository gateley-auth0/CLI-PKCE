import base64
import hashlib
import os
import pathlib
import secrets
import threading
import urllib
import webbrowser

from werkzeug.serving import make_server

import dotenv
from flask import Flask, request

app = Flask(__name__)


@app.route("/callback")
def callback():
    code = request.args['code']
    received_state = request.args['state']
    if received_state != state:
        return "Booo hiss"
    return "Hello World!"


class ServerThread(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print('starting server')
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


def stop_server():
    global server
    server.shutdown()


def auth0_url_encode(byte_data):
    return base64.urlsafe_b64encode(byte_data).replace(b'=', b'').decode('utf-8')


def generate_challenge(a_verifier):
    return auth0_url_encode(hashlib.sha256(a_verifier).digest())


env_path = pathlib.Path('.') / '.env'
dotenv.load_dotenv(dotenv_path=env_path)

verifier = secrets.token_bytes(32)
challenge = generate_challenge(verifier)
state = auth0_url_encode(secrets.token_bytes(32))

client_id = os.getenv('AUTH0_CLIENT_ID')
tenant = os.getenv('AUTH0_TENANT')

base_url = 'https://%s.auth0.com/authorize?' % tenant
url_parameters = {}
url_parameters['audience'] = 'urn:cli-sample:api'
url_parameters['scope'] = 'profile'
url_parameters['response_type'] = 'code'
url_parameters['redirect_uri'] = 'http://127.0.0.1:5000/callback'
url_parameters['client_id'] = client_id
url_parameters['code_challenge'] = challenge
url_parameters['code_challenge_method'] = 'S256'
url_parameters['state'] = state
url = base_url + urllib.parse.urlencode(url_parameters)

webbrowser.open_new(url)
server = ServerThread(app)
server.start()
print('server started')

