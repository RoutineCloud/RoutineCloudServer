from typing import Dict, Any

from authlib.oauth2.rfc6749 import OAuth2Request
from authlib.oauth2.rfc6749.requests import BasicOAuth2Payload
from authlib.oauth2.rfc6749.requests import JsonPayload, JsonRequest
from fastapi import Request


class FastAPIOAuth2Request(OAuth2Request):
    """
    Concrete OAuth2Request implementation for FastAPI/Starlette.

    - args: query parameters (?a=1&b=2)
    - form: POST form data (grant_type, code, refresh_token, ...)
    - payload: BasicOAuth2Payload wrapping form data
    """
    def __init__(
        self,
        method: str,
        uri: str,
        headers: Dict[str, str],
        query_args: Dict[str, str],
        form_data: Dict[str, str],
    ) -> None:
        super().__init__(method=method, uri=uri, headers=headers)
        self._args = query_args
        self._form = form_data
        self.payload = BasicOAuth2Payload(form_data)

    @property
    def args(self) -> Dict[str, str]:
        return self._args

    @property
    def form(self) -> Dict[str, str]:
        return self._form




def form_to_oauth2_request(
    request: Request,
    token_form: object,
) -> OAuth2Request:
    """
    Build an OAuth2Request from FastAPI Request + your OAuth2TokenForm.
    This is what Authlib's grants will see.
    """
    # Map your form fields into a payload dict (only non-None values)
    form_data: Dict[str, str] = {}

    def add_if_not_none(key: str, value: Any):
        if value is not None:
            form_data[key] = value

    add_if_not_none("grant_type", getattr(token_form, "grant_type", None))
    # common
    scope_val = getattr(token_form, "scope", None)
    add_if_not_none("scope", scope_val or None)
    add_if_not_none("client_id", getattr(token_form, "client_id", None))
    add_if_not_none("client_secret", getattr(token_form, "client_secret", None))

    # password
    add_if_not_none("username", getattr(token_form, "username", None))
    add_if_not_none("password", getattr(token_form, "password", None))

    # authorization_code / PKCE
    add_if_not_none("code", getattr(token_form, "code", None))
    add_if_not_none("redirect_uri", getattr(token_form, "redirect_uri", None))
    add_if_not_none("code_verifier", getattr(token_form, "code_verifier", None))

    # refresh
    add_if_not_none("refresh_token", getattr(token_form, "refresh_token", None))

    # device flow
    add_if_not_none("device_code", getattr(token_form, "device_code", None))
    # device specific identifier for device authorization endpoint
    add_if_not_none("device_uuid", getattr(token_form, "device_uuid", None))

    query_args = dict(request.query_params)

    return FastAPIOAuth2Request(
        method=request.method,
        uri=str(request.url),
        headers=dict(request.headers),
        query_args=query_args,
        form_data=form_data,
    )

class BasicJsonPayload(JsonPayload):
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def data(self) -> Dict[str, Any]:
        return self._data


class FastAPIJsonRequest(JsonRequest):
    def __init__(
        self,
        method: str,
        uri: str,
        headers: Dict[str, str],
        json_data: Dict[str, Any],
    ) -> None:
        super().__init__(method, uri, headers)
        self.payload = BasicJsonPayload(json_data)


def json_to_json_request(request: Request, data: Dict[str, Any]) -> JsonRequest:
    return FastAPIJsonRequest(
        method=request.method,
        uri=str(request.url),
        headers=dict(request.headers),
        json_data=data,
    )