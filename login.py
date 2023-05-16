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

env_path = pathlib.Path('.') / '.env'
dotenv.load_dotenv(dotenv_path=env_path)
client_id = os.getenv('AUTH0_CLIENT_ID')
tenant = os.getenv('AUTH0_TENANT')
host = os.getenv('HOST', "127.0.0.1")
port = os.getenv('PORT', "5000")
callback_url = os.getenv('CALLBACK_URL', "/callback")
redirect_uri = f"http://{host}:{port}{callback_url}"
audience = os.getenv('AUTH0_AUDIENCE', "https://gateley-empire-life.auth0.com/api/v2/")
scope = os.getenv('AUTH0_SCOPE',"profile openid email read:clients create:clients read:client_keys")

app = Flask(__name__)

@app.route(callback_url)
def callback():
    """
    The callback is invoked after a completed login attempt (succesful or otherwise).
    It sets global variables with the auth code or error messages, then sets the
    polling flag received_callback.
    :return:
    """
    global received_callback, code, error_message, received_state
    error_message = None
    code = None
    if 'error' in request.args:
        error_message = request.args['error'] + ': ' + request.args['error_description']
    else:
        code = request.args['code']
    received_state = request.args['state']
    received_callback = True
    return "Please return to your application now."


class ServerThread(threading.Thread):
    """
    The Flask server is done this way to allow shutting down after a single request has been received.
    """

    def __init__(self, app, host, port):
        threading.Thread.__init__(self)
        self.srv = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print('starting server')
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


def auth0_url_encode(byte_data):
    """
    Safe encoding handles + and /, and also replace = with nothing
    :param byte_data:
    :return:
    """
    return base64.urlsafe_b64encode(byte_data).decode('utf-8').replace('=', '')


def generate_challenge(a_verifier):
    return auth0_url_encode(hashlib.sha256(a_verifier.encode()).digest())

verifier = auth0_url_encode(secrets.token_bytes(32))
challenge = generate_challenge(verifier)
state = auth0_url_encode(secrets.token_bytes(32))

# We generate a nonce (state) that is used to protect against attackers invoking the callback
base_url = 'https://%s.us.auth0.com/authorize?' % tenant
url_parameters = {
    'audience': audience,
    'scope': scope,
    'response_type': 'code',
    'redirect_uri': redirect_uri,
    'client_id': client_id,
    'code_challenge': challenge.replace('=', ''),
    'code_challenge_method': 'S256',
    'state': state
}
url = base_url + urllib.parse.urlencode(url_parameters)

# Open the browser window to the login url
# Start the server
# Poll til the callback has been invoked
received_callback = False
webbrowser.open_new(url)
server = ServerThread(app, host, port)
server.start()
while not received_callback:
    sleep(1)
server.shutdown()

if state != received_state:
    print("Error: session replay or similar attack in progress. Please log out of all connections.")
    exit(-1)

if error_message:
    print("An error occurred:")
    print(error_message)
    exit(-1)

# Exchange the code for a token
url = 'https://%s.us.auth0.com/oauth/token' % tenant
headers = {'Content-Type': 'application/json'}
body = {'grant_type': 'authorization_code',
        'client_id': client_id,
        'code_verifier': verifier,
        'code': code,
        'audience': audience,
        'redirect_uri': redirect_uri}
r = requests.post(url, headers=headers, data=json.dumps(body))
r.raise_for_status()
data = r.json()
# Use the token to list the clients
url = 'https://%s.us.auth0.com/userinfo' % tenant
headers = {'Authorization': 'Bearer %s' % data['access_token']}
r = requests.get(url, headers=headers)
r.raise_for_status()
data = r.json()
print(data)
