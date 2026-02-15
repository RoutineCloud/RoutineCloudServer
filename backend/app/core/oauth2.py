import time
import uuid

from authlib.common.security import generate_token
from authlib.jose import jwt
from authlib.oauth2.rfc6749 import AuthorizationServer as _AuthorizationServer
from authlib.oauth2.rfc6749 import OAuth2Request
from authlib.oauth2.rfc6749.requests import JsonRequest
from authlib.oauth2.rfc6750 import BearerToken
from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.endpoints import DeviceAuthorizationEndpoint
from app.core.grants import RefreshTokenGrant, PasswordGrant, AuthorizationCodeGrant, DeviceCodeGrant
from app.core.requests import form_to_oauth2_request, json_to_json_request
from app.core.security import OAuth2TokenForm
from app.db.session import get_db
from app.models.oauth2 import OAuth2Client, OAuth2Token


class AuthorizationServer(_AuthorizationServer):
    '''AuthorizationServer class'''

    def __init__(self, app=None, query_client=None, save_token=None):
        super().__init__()
        self._query_client = query_client
        self._save_token = save_token
        self._error_uris = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app, query_client=None, save_token=None):
        """Initialize later with Flask app instance."""
        if query_client is not None:
            self._query_client = query_client
        if save_token is not None:
            self._save_token = save_token

        self.generate_token = create_bearer_token_generator()

        #TODO use settings for OAUTH2_SCOPES_SUPPORTED and OAUTH2_ERROR_URIS

    def query_client(self, client_id):
        return self._query_client(client_id)

    def save_token(self, token, request):
        return self._save_token(token, request)

    def create_oauth2_request(self, request: Request) -> OAuth2Request:
        # If someone already passed an OAuth2Request, just use it
        if isinstance(request, OAuth2Request):
            return request

        token_form: OAuth2TokenForm = getattr(request.state, "oauth2_form")
        return form_to_oauth2_request(request, token_form)

    def create_json_request(self, request: Request) -> JsonRequest:
        if isinstance(request, JsonRequest):
            return request

        json_data = getattr(request.state, "json_body")
        return json_to_json_request(request, json_data)

    def send_signal(self, name, *args, **kwargs):
        pass
        #if name == "after_authenticate_client":
        #    client_authenticated.send(self, *args, **kwargs)
        #elif name == "after_revoke_token":
        #    token_revoked.send(self, *args, **kwargs)

    def handle_response(self, status, body, headers):
        """Return HTTP response. Framework MUST implement this function."""
        return status, body, headers

    def handle_error_response(self, request, error):
        """Return HTTP response. Framework MUST implement this function."""
        raise HTTPException(status_code=error.status_code, detail=error.description)


def create_query_client_func(client_model):
    def query_client(client_id):
        session = next(get_db())
        q = session.query(client_model)
        return q.filter_by(client_id=client_id).first()

    return query_client


def create_save_token_func(token_model):
    def save_token(token, request):
        session = next(get_db())
        if request.user:
            user_id = request.user.id
        else:
            user_id = None
        client = request.client
        item = token_model(client_id=client.client_id, user_id=user_id, **token)
        session.add(item)
        session.commit()
    return save_token

def create_bearer_token_generator():
    """Create a generator function for generating ``token`` value. This
    method will create a Bearer Token generator with
    :class:`authlib.oauth2.rfc6750.BearerToken`.
    """

    def jwt_access_token_generator(*, client, grant_type, user=None, scope=None):
        """Generate a JWT formatted access token (RFC 9068 style payload).

        Claims included:
        - iss: issuer from settings
        - sub: user id if available
        - aud: client_id
        - iat, exp: issued-at and expiry
        - scope: space-delimited scope string if any
        - jti: unique token id
        - client_id, grant_type: informational
        """
        # Determine expiration to align JWT "exp" with response "expires_in"
        expires_in_func = create_token_expires_in_generator()
        try:
            expires_in = expires_in_func(client, grant_type)
        except Exception:
            # Fallback to default 3600 if anything goes wrong
            expires_in = BearerToken.DEFAULT_EXPIRES_IN

        now = int(time.time())
        exp = now + int(expires_in or 0)

        client_id = client.get_client_id() if hasattr(client, "get_client_id") else getattr(client, "client_id", None)
        sub = None
        if user is not None:
            sub = user.id

        claims = {
            "iss": settings.OAUTH2_ISSUER,
            "iat": now,
            "exp": exp,
            "aud": client_id,
            "jti": uuid.uuid4().hex,
            "client_id": client_id,
            "grant_type": grant_type,
        }
        if sub is not None:
            claims["sub"] = str(sub)
        if scope:
            claims["scope"] = scope

        key = settings.OAUTH2_JWT_KEY
        alg = settings.OAUTH2_JWT_ALG
        return jwt.encode({"alg": alg}, claims, key).decode()

    def refresh_token_generator(*args, **kwargs):  # pylint: disable=W0613
        return generate_token(48)

    expires_generator = create_token_expires_in_generator()

    return BearerToken(
        jwt_access_token_generator, refresh_token_generator, expires_generator
    )


def create_token_expires_in_generator():
    """Create a generator function for generating ``expires_in`` value.
    Developers can re-implement this method with a subclass if other means
    required. The default expires_in value is defined by ``grant_type``,
    different ``grant_type`` has different value. It can be configured
    with::

        OAUTH2_TOKEN_EXPIRES_IN = {
            'authorization_code': 864000
        }
    """
    data = {}
    data.update(BearerToken.GRANT_TYPES_EXPIRES_IN)

    expires_in_conf = settings.OAUTH2_TOKEN_EXPIRES_IN
    if expires_in_conf:
        data.update(expires_in_conf)

    def expires_in(client, grant_type):
        return data.get(grant_type, BearerToken.DEFAULT_EXPIRES_IN)

    return expires_in


authorization = AuthorizationServer()

def config_oauth(app):
    '''Setup the application configuration'''
    query_client = create_query_client_func(OAuth2Client)
    save_token = create_save_token_func(OAuth2Token)
    authorization.init_app(
        app,
        query_client=query_client,
        save_token=save_token
    )

    authorization.register_grant(RefreshTokenGrant)
    authorization.register_grant(PasswordGrant)
    # RFC8628 device code grant and endpoint
    authorization.register_endpoint(DeviceAuthorizationEndpoint)
    authorization.register_grant(DeviceCodeGrant)
    authorization.register_grant(AuthorizationCodeGrant)

    #revocation_cls = create_revocation_endpoint(db, OAuth2Token)
    #authorization.register_endpoint(revocation_cls)

    #bearer_cls = create_bearer_token_validator(db, OAuth2Token)
    #require_oauth.register_token_validator(bearer_cls())