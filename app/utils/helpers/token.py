import os
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv

from app.database.models.helpdesk import Employees
from app.utils.errors.exceptions import CustomError

load_dotenv()

bearer_scheme = HTTPBearer(
  scheme_name="Bearer",
  description="Enter your Bearer token in the format 'Bearer <token>'",
  bearerFormat="JWT"
)

JWT_ACCESS_SECRET = os.getenv('JWT_ACCESS_SECRET')
JWT_REFRESH_SECRET = os.getenv('JWT_REFRESH_SECRET')

async def validate_access_token(
  request: Request,
  token: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> (dict | None):
  
  if not token:
    return None
  
  try:
    # Decode the JWT
    payload = jwt.decode(
      token.credentials,
      JWT_ACCESS_SECRET,
      algorithms=['HS256']
    )

    expiration_timestamp = payload.get("exp")
    if expiration_timestamp is None:
      raise CustomError(
        403,
        "Could not validate credentials"
      )
    # Compare with current UTC time
    if datetime.now(timezone.utc).timestamp() > expiration_timestamp:
      raise CustomError(
        403,
        "Invalid token",
        "The token has expired"
      )

    # 3. Extract User ID (assuming it's stored under 'sub' or 'id' claim)
    user_id: int | None = payload.get("sub") # Standard 'subject' claim
    if user_id is None:
      user_id = payload.get("id") # Or check 'id' if you use that

    if user_id is None:
      # Token payload is missing the user identifier
      raise CustomError(
      404,
      "Could not validate credentials"
      )

    # 4. Fetch User from Database
    # Use get_or_none for cleaner handling if user might not exist
    db_user = await Employees.get_or_none(id=user_id, deactivated_at__isnull=True, deleted_at__isnull=True)

    if db_user is None:
      raise CustomError(
        404,
        "Colaborador associado ao token não encontrado",
        "O colaborador pode estar desativo ou eliminado"
      )

    # 5. Verify User Status (adjust checks as needed)
    if db_user.deactivated_at is not None or db_user.deleted_at is not None:
      raise CustomError(
        403,
        "Colaborador associado ao token não encontrado",
        "O colaborador pode estar desativo ou eliminado"
      )

    user_info = await db_user.to_dict()
    
    request.state.user = user_info

    return user_info

  except JWTError as e:
    raise CustomError(
      401,
      "Could not validate credentials"
    ) from e
  
  except HTTPException as e:
    raise e
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="An internal error occurred during authentication.",
    ) from e

async def validate_optional_access_token(
  request: Request
) -> (dict | None):
  try:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
      return None
    
    token = auth_header.split(" ")[1]
    user = await validate_access_token(request, f"Bearer {token}") # Pass the full header for consistency? Or just token?
    return user

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="An internal error occurred during authentication.",
    ) from e
    
async def validate_refresh_token(
  request: Request,
  x_refresh_token: str | None = Header(None, description="Your refresh token")
) -> dict:
  if x_refresh_token is None:
    raise CustomError(
      401,
      "Refresh token missing in X-Refresh-Token header",
    )

  try:
    payload = jwt.decode(
      x_refresh_token,
      JWT_REFRESH_SECRET,
      algorithms=['HS256']
    )

    expiration_timestamp = payload.get("exp")
    if expiration_timestamp is None or datetime.now(timezone.utc).timestamp() > expiration_timestamp:
      raise CustomError(
        401,
        "Não foi possível validar o refresh token"
      )

    user_id: int | None = payload.get("id")
    if user_id is None:
      raise CustomError(
        401,
        "Não foi possível validar o refresh token"
      )

    db_user = await Employees.get_or_none(id=user_id)
    if not db_user:
      raise CustomError(
        401,
        "Não foi possível validar o refresh token"
      )

    if db_user.deactivated_at is not None or db_user.deleted_at is not None:
      raise CustomError(
        403,
        "O colaborador associado ao token está desativo ou eliminado"
      )

    user_info = await db_user.to_dict()

    request.state.refreshed_user = user_info

    return user_info

  except JWTError:
    raise CustomError(
      401,
      "Não foi possível validar o refresh token"
    )
    
  except HTTPException as e:
    raise e
  
  except Exception as e:
    raise CustomError(
      500,
      "An internal error occurred during token refresh validation."
    ) from e

    
    
    