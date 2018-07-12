import base64
import hashlib
import json
import os
import pathlib
import requests
import secrets
import threading
import urllib
import webbrowser
from time import sleep

from werkzeug.serving import make_server

import dotenv
from flask import Flask, request

app = Flask(__name__)


@app.route("/callback")
def callback():
    global received_callback, code, received_state
    received_callback = True
    code = request.args['code']
    received_state = request.args['state']
    return "Please return to your application now."


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


def auth0_url_encode(byte_data):
    return base64.urlsafe_b64encode(byte_data).decode('utf-8').replace('=', '')


def generate_challenge(a_verifier):
    return auth0_url_encode(hashlib.sha256(a_verifier.encode()).digest())


env_path = pathlib.Path('.') / '.env'
dotenv.load_dotenv(dotenv_path=env_path)

verifier = auth0_url_encode(secrets.token_bytes(32))
challenge = generate_challenge(verifier)
state = auth0_url_encode(secrets.token_bytes(32))
client_id = os.getenv('AUTH0_CLIENT_ID')
tenant = os.getenv('AUTH0_TENANT')
redirect_uri = 'http://127.0.0.1:5000/callback'

base_url = 'https://%s.auth0.com/authorize?' % tenant
url_parameters = {
    'audience': 'https://gateley-empire-life.auth0.com/api/v2/',
    'scope': 'profile openid email read:clients create:clients read:client_keys',
    'response_type': 'code',
    'redirect_uri': redirect_uri,
    'client_id': client_id,
    'code_challenge': challenge.replace('=', ''),
    'code_challenge_method': 'S256',
    'state': state
}
url = base_url + urllib.parse.urlencode(url_parameters)

received_callback = False
webbrowser.open_new(url)
server = ServerThread(app)
server.start()
while not received_callback:
    sleep(1)
server.shutdown()

if state != received_state:
    print("Error: session replay or similar attack in progress. Please log out of all connections.")
    exit(-1)


url = 'https://%s.auth0.com/oauth/token' % tenant
headers = {'Content-Type': 'application/json'}
body = {'grant_type': 'authorization_code',
        'client_id': client_id,
        'code_verifier': verifier,
        'code': code,
        'audience': 'https://gateley-empire-life.auth0.com/api/v2/',
        'redirect_uri': redirect_uri}
r = requests.post(url, headers=headers, data=json.dumps(body))
data = r.json()

url = 'https://%s.auth0.com/api/v2/clients' % tenant
headers = {'Authorization': 'Bearer %s' % data['access_token']}
r = requests.get(url, headers=headers)
data = r.json()

for client in data:
    print("Client: " + client['name'])
