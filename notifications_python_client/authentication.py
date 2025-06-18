import calendar
import time

import jwt

from notifications_python_client.errors import (
    TokenAlgorithmError,
    TokenDecodeError,
    TokenError,
    TokenExpiredError,
    TokenIssuedAtError,
    TokenIssuerError,
)

__algorithm__ = "HS256"
__type__ = "JWT"
__bound__ = 30

INVALID_FUTURE_TOKEN_ERROR_MESSAGE = "Token can not be in the future"


def create_jwt_token(secret, client_id):
    """
    Create JWT token for GOV.UK Notify

    Tokens have standard header:
    {
        "typ": "JWT",
        "alg": "HS256"
    }

    Claims consist of:
    iss: identifier for the client
    iat: issued at in epoch seconds (UTC)

    :param secret: Application signing secret
    :param client_id: Identifier for the client
    :return: JWT token for this request
    """
    assert secret, "Missing secret key"
    assert client_id, "Missing client id"

    headers = {"typ": __type__, "alg": __algorithm__}

    claims = {"iss": client_id, "iat": epoch_seconds()}
    t = jwt.encode(payload=claims, key=secret, headers=headers)
    if isinstance(t, str):
        return t
    else:
        return t.decode()


def get_token_issuer(token):
    """
    Issuer of a token is the identifier used to recover the secret
    Need to extract this from token to ensure we can proceed to the signature validation stage
    Does not check validity of the token
    :param token: signed JWT token
    :return issuer: iss field of the JWT token
    :raises TokenIssuerError: if iss field not present
    :raises TokenDecodeError: if token does not conform to JWT spec
    """
    try:
        unverified = decode_token(token)

        if "iss" not in unverified:
            raise TokenIssuerError

        return unverified.get("iss")
    except jwt.DecodeError as e:
        raise TokenDecodeError from e


def decode_jwt_token(token, secret):
    """
    Validates and decodes the JWT token
    Token checked for
        - signature of JWT token
        - token issued date is valid

    :param token: jwt token
    :param secret: client specific secret
    :return boolean: True if valid token, False otherwise
    :raises TokenIssuerError: if iss field not present
    :raises TokenIssuedAtError: if iat field not present
    :raises TokenExpiredError: If the iat value expires this token
    :raises TokenDecodeError: If the token cannot be decoded because it failed validation
    :raises TokenAlgorithmError: If the algorithm is not recognised
    :raises TokenError: If any other type of jwt exception is raised when trying jwt.decode
    """
    try:
        # check signature of the token
        decoded_token = jwt.decode(
            token,
            key=secret,
            options={"verify_signature": True},
            algorithms=[__algorithm__],
            leeway=__bound__,
        )
        return validate_jwt_token(decoded_token)
    except jwt.InvalidIssuedAtError as e:
        raise TokenExpiredError(
            "Token has invalid iat field", decode_token(token)
        ) from e
    except jwt.ImmatureSignatureError as e:
        raise TokenExpiredError(
            INVALID_FUTURE_TOKEN_ERROR_MESSAGE, decode_token(token)
        ) from e
    except jwt.DecodeError as e:
        raise TokenDecodeError from e
    except jwt.InvalidAlgorithmError as e:
        raise TokenAlgorithmError from e
    except jwt.InvalidTokenError as e:
        # At this point, we have not caught a specific exception we care about enough to show
        # a precise error message (ie something to do with the iat, iss or alg fields).
        # If there is a different reason our token is invalid we will throw a generic error as we
        # don't wish to provide exact messages for every type of error that jwt might encounter.
        # https://github.com/jpadilla/pyjwt/blob/master/jwt/exceptions.py
        # https://pyjwt.readthedocs.io/en/latest/api.html#exceptions
        raise TokenError from e


def validate_jwt_token(decoded_token):
    # token has all the required fields
    if "iss" not in decoded_token:
        raise TokenIssuerError
    if "iat" not in decoded_token:
        raise TokenIssuedAtError

    # check iat time is within bounds
    now = epoch_seconds()
    iat = int(decoded_token["iat"])
    if now > (iat + __bound__):
        raise TokenExpiredError("Token has expired", decoded_token)
    if iat > (now + __bound__):
        raise TokenExpiredError(INVALID_FUTURE_TOKEN_ERROR_MESSAGE, decoded_token)

    return True


def decode_token(token):
    """
    Decode token but don;t check the signature
    :param token:
    :return decoded token:
    """
    return jwt.decode(
        token, options={"verify_signature": False}, algorithms=[__algorithm__]
    )


def epoch_seconds():
    return calendar.timegm(time.gmtime())
