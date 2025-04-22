from fastapi import Request, Depends
from app.database.models.helpdesk import Employees
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from jose import jwt
from jose.exceptions import JWSError
from app.utils.errors.exceptions import CustomError
from app.utils.helpers.token import validate_access_token

load_dotenv()

JWT_ACCESS_SECRET = os.getenv('JWT_ACCESS_SECRET')
JWT_REFRESH_SECRET = os.getenv('JWT_REFRESH_SECRET')
JWT_RECOVERY_SECRET = os.getenv('JWT_RECOVERY_SECRET')
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
  expire = datetime.now() + timedelta(**expire_time)
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

# async def validate_access_token(token: dict):
#   try:
#     bearer = token.scheme
#     token = token.credentials
#     if bearer != 'Bearer':
#       raise CustomError(
#         401,
#         "Invalid token",
#         "The token format is invalid"
#       )
#     payload = jwt.decode(token, JWT_ACCESS_SECRET, algorithms='HS256')
    
#     id: int = payload.get("id", None)
#     if not id:
#       raise CustomError(
#         401,
#         "Invalid token",
#         "The token payload is missing information"
#       )
    
#     if payload.get('exp', None) < datetime.now().timestamp():
#       raise CustomError(
#         401,
#         "Invalid token",
#         "The token has expired"
#       )

#   except CustomError as e:
#     raise e
  
#   except Exception as e:
#     raise CustomError(
#       401,
#       "Tenta outra vez",
#       str(e)
#     )

#   user = await Employees().filter(id=id, deactivated_at=None, deleted_at=None).first()
#   if not user:
#     raise CustomError(
#       401,
#       "Invalid token",
#       "The user either is deactivated or deleted"
#     )
#   return await user.to_dict_details()
