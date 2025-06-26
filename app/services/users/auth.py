from fastapi import Request, Depends
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from app.utils.errors.exceptions import CustomError
from app.utils.helpers.token import validate_access_token
from app.utils.keys import verify_jwt

load_dotenv()

JWT_ACCESS_SECRET = os.getenv('JWT_ACCESS_SECRET')
JWT_REFRESH_SECRET = os.getenv('JWT_REFRESH_SECRET')
JWT_RECOVERY_SECRET = os.getenv('JWT_RECOVERY_SECRET')
SERVICE_HANDSHAKE_TOKEN = os.getenv('HANDSHAKE_SECRET')
SERVICE_HANDSHAKE_ISSUER = os.getenv('SERVICE_HANDSHAKE_ISSUER')
SERVICE_HANDSHAKE_AUDIENCE = os.getenv('SERVICE_HANDSHAKE_AUDIENCE')
GATEWAY_HANDSHAKE_SECRET = os.getenv('GATEWAY_HANDSHAKE_SECRET')
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 5
RECOVERY_TOKEN_EXPIRE_HOURS = 1

async def create_token(data: dict, token_type: str = 'access'):
  to_encode = data
  if token_type == 'access':
    expire_time = { "minutes": ACCESS_TOKEN_EXPIRE_MINUTES }
    secret = JWT_ACCESS_SECRET
  elif token_type == 'refresh': 
    expire_time = { "days": REFRESH_TOKEN_EXPIRE_DAYS }
    secret = JWT_REFRESH_SECRET
  else:
    expire_time = { "hours": RECOVERY_TOKEN_EXPIRE_HOURS }
    secret = JWT_RECOVERY_SECRET
  expire = datetime.now(timezone.utc) + timedelta(**expire_time)
  to_encode["exp"] = expire
  encoded_jwt = jwt.encode(to_encode, secret, algorithm='HS256')
  return encoded_jwt

async def create_service_token(data: dict):
  to_encode = data
  expire_time = { "minutes": 1 }
  secret = GATEWAY_HANDSHAKE_SECRET
  expire = datetime.now(timezone.utc) + timedelta(**expire_time)
  to_encode["exp"] = expire
  encoded_jwt = jwt.encode(to_encode, secret, algorithm='HS256')
  return encoded_jwt

def require_permission(required_permission_name: str):
  async def _permission_checker(
    request: Request,
    user_info: dict = Depends(validate_access_token)
  ):
    try:
      user_info = request.state.user
      
      has_permission = any(
        permission['display_name'].lower() == required_permission_name.lower()
        for permission in user_info['permissions']
      )
      
      if not has_permission:
        raise CustomError(
          403,
          "Não tem permissões para aceder a esta área",
          f"Não tem permissões. É necessária a permissão '{required_permission_name}'."
        )
        
      return user_info

    except CustomError as e:
      raise e
    except Exception as e:
      raise CustomError(
        500,
        "Ocorreu um erro ao verificar as permissões",
      )

  # Return the dependency function created by the factory
  return _permission_checker


async def _services_handshake(request: Request):
  """
  Validates the service handshake token from the request headers.
  This function is intended to be used as a dependency or called by a middleware.
  Raises CustomError if validation fails.
  """
  try:
    service_token_received = request.headers.get("X-Service-Token")
    if not service_token_received:
      raise CustomError(
        401,
        "Handshake token required.",
        "Missing X-Handshake-Token header."
      )
    try:
      jwt_token = verify_jwt(request)
      user_id: int | None = jwt_token.get("sub")
      if user_id:
        request.state.user_id = user_id

    except ExpiredSignatureError:
      raise CustomError(
        401,
        "Handshake token has expired.",
        "The provided X-Handshake-Token has expired."
      )
    except JWTClaimsError as e:
      raise CustomError(
        401,
        "Invalid handshake token claims.",
        f"Token claims validation failed: {str(e)}"
      )
    except JWTError as e:
      raise CustomError(
        401,
        "Invalid handshake token.",
        f"The provided X-Handshake-Token is not valid or malformed: {str(e)}"
      )

  except CustomError:
    raise 
  except Exception as e:
    print(f"Unexpected error during service handshake: {e}")
    raise CustomError(
      500,
      "Handshake validation failed.",
      "An unexpected error occurred during token validation."
    )