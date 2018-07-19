# Auth0 Python CLI authenticating via Authorization Code + PKCE flow, then accessing the management API

This sample demonstrates how to authenticate a command line app, normally done via Client Credentials, using the
Authorization Code flow with PKCE. It is done by starting up a browser window to do the authentication. The token
is used to access the management API.

The flow is documented here: https://auth0.com/docs/api-auth/tutorials/authorization-code-grant-pkce

In addition we use the state parameter (as a nonce) to ensure against replay attack:
https://auth0.com/docs/protocols/oauth2/oauth-state

# Running the App

To run the sample, make sure you have `python` and `pip` installed.

* You will need to create your app as a Native app. Set the callback URL to:
http://127.0.0.1:5000/callback
* Populate .env with the client ID and tenant for your Auth0 app.
* Run `pip install -r requirements.txt` to install the dependencies.
* Run `python login.py`.

The python script will open up a window in your browser to log in.
* Log in

The browser window will tell you to return to your app (for technical reasons, it is difficult to kill the browser
window automatically)
* Return to your shell

The app will list the clients available in the tenant (by accessing the management API).

# Security considerations

The app should be flagged as allowed to access the management API, as well as any user allowed to use the app. These
can be enforced with a rule like 
```function (user, context, callback) {
  var audience = '';
  audience = audience ||
    (context.request && context.request.query && context.request.query.audience) ||
    (context.request && context.request.body && context.request.body.audience);
  if (audience === 'https://gateley-empire-life.auth0.com/api/v2/') {
    var client_authorized = context.clientMetadata && context.clientMetadata.ManagementAPIAccess === "True";
    user.app_metadata = user.app_metadata || {};
    var user_authorized = user.app_metadata.roles.indexOf('cli') !== -1;
    if (client_authorized && user_authorized) {
      context.accessToken.scope = "read:clients read:connections";
      callback(null, user, context);
    } else {
      callback(new UnauthorizedError('Access denied'));
    }
  } else {
    callback(null, user, context);
  }
}
```
Th app metadata should have `ManagementAPIAccess` set to true, and a user should have their app metada include `cli` in
their roles

## What is Auth0?

Auth0 helps you to:

* Add authentication with [multiple authentication sources](https://auth0.com/docs/identityproviders),
either social like **Google, Facebook, Microsoft Account, LinkedIn, GitHub, Twitter, Box, Salesforce, among others**,or 
enterprise identity systems like **Windows Azure AD, Google Apps, Active Directory, ADFS or any SAML Identity Provider**.
* Add authentication through more traditional **[username/password databases](https://docs.auth0.com/mysql-connection-tutorial)**.
* Add support for **[linking different user accounts](https://auth0.com/docs/link-accounts)** with the same user.
* Support for generating signed [JSON Web Tokens](https://auth0.com/docs/jwt) to call your APIs and
**flow the user identity** securely.
* Analytics of how, when and where users are logging in.
* Pull data from other sources and add it to the user profile, through [JavaScript rules](https://auth0.com/docs/rules).

## Create a free account in Auth0

1. Go to [Auth0](https://auth0.com) and click Sign Up.
2. Use Google, GitHub or Microsoft Account to login.

## Issue Reporting

If you have found a bug or if you have a feature request, please report them at this repository issues section.
Please do not report security vulnerabilities on the public GitHub issue tracker. 
The [Responsible Disclosure Program](https://auth0.com/whitehat) details the procedure for disclosing security issues.

## Author

[Auth0](https://auth0.com)

## License

This project is licensed under the MIT license. See the [LICENSE](LICENCE) file for more info.
