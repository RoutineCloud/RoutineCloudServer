from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc8628 import DeviceCodeGrant as _DeviceCodeGrant

from app.core.security import verify_password
from app.db.session import get_db
from app.models.oauth2 import OAuth2Token, OAuth2AuthorizationCode, OAuth2DeviceCodes
from app.models.user import User


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    #TODO go back to only client_secret_basic -> Use PKCE/authcode and a own auth webside
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "none"]

    def authenticate_user(self, username, password):
        session = next(get_db())
        user = session.query(User).filter_by(username=username).first()
        if user and verify_password(password, user.hashed_password):
            return user
        return None

class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    def authenticate_user(self, authorization_code):
        session = next(get_db())
        item = session.query(OAuth2AuthorizationCode).filter_by(code=authorization_code).first()
        if item and not item.is_expired():
            user = session.query(User).filter_by(id=item.user_id).first()
            if user:
                return user

    def save_authorization_code(self, code, request):
        session = next(get_db())
        item = OAuth2AuthorizationCode(
            client_id=request.client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
            code=code,
        )
        session.add(item)
        session.commit()
        return item

    def query_authorization_code(self, code, client):
        session = next(get_db())
        item = session.query(OAuth2AuthorizationCode).filter_by(code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        session = next(get_db())
        session.delete(authorization_code)
        session.commit()


class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token):
        session = next(get_db())
        item = session.query(OAuth2Token).filter_by(refresh_token=refresh_token).first()
        # define is_refresh_token_valid by yourself
        # usually, you should check if refresh token is expired and revoked
        if item and item.is_refresh_token_valid():
            return item
        return None

    def authenticate_user(self, credential):
        session = next(get_db())
        return session.query(User).get(credential.user_id)

    def revoke_old_credential(self, credential):
        credential.revoked = True
        session = next(get_db())
        session.add(credential)
        session.commit()

class DeviceCodeGrant(_DeviceCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]

    def query_device_credential(self, device_code):
        session = next(get_db())
        return (
            session.query(OAuth2DeviceCodes)
            .filter_by(device_code=device_code)
            .first()
        )

    def query_user_grant(self, user_code):
        session = next(get_db())
        cred = (
            session.query(OAuth2DeviceCodes)
            .filter_by(user_code=user_code)
            .first()
        )
        if not cred:
            return None
        if cred.is_expired():
            session.delete(cred)
            session.commit()
            return None

        if cred.status == "granted" and cred.user_id:
            user = session.query(User).get(cred.user_id)
            return user, True
        if cred.status == "denied":
            user = session.query(User).get(cred.user_id) if cred.user_id else None
            return user, False
        return None

    def should_slow_down(self, credential, now):
        return False