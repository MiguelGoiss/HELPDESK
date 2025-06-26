from fastapi import FastAPI, Request, HTTPException, Depends
from jose import jwt, JWTError
from jose.utils import base64url_decode
import requests
import time
from app.utils.errors.exceptions import CustomError
import json

JWKS_URL = "http://172.17.12.224:8000/gateway.internal/.well-known/jwks.json"
ALGORITHM = "RS256"
EXPECTED_ISSUERS = {"gateway", "equipments"}
EXPECTED_AUDIENCE = "Helpdesk_Service"

jwks_cache = {
  "keys": [],
  "expires": 0
}

def get_jwks():
  # Cache (10 min)
  if jwks_cache["expires"] < time.time():
    res = requests.get(JWKS_URL)
    res.raise_for_status()
    jwks_cache["keys"] = res.json()["keys"]
    jwks_cache["expires"] = time.time() + 600  # 10 minutes
  return jwks_cache["keys"]

def get_public_key(kid: str):
  keys = get_jwks()
  for jwk in keys:
    if jwk["kid"] == kid:
      return json.dumps(jwk)
  raise HTTPException(status_code=401, detail="Unknown key ID")

def verify_jwt(request: Request):
  try:
    token = request.headers.get("X-Service-Token")
    
    headers = jwt.get_unverified_header(token)
    
    kid = headers["kid"]
    public_key = get_public_key(kid)
    payload = jwt.decode(
      token,
      public_key,
      algorithms=[ALGORITHM],
      audience=EXPECTED_AUDIENCE,
    )
    
    issuer = payload['iss']
    if issuer not in EXPECTED_ISSUERS:
      raise CustomError(
        401,
        "Invalid Token",
        "Invalid Issuer"
      )
    return payload
  except JWTError as e:
    raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
  except CustomError as e:
    raise
# def secure_endpoint(request: Request):
#   token = request.headers.get("Authorization")
#   if not token or not token.startswith("Bearer "):
#     raise HTTPException(status_code=401, detail="Missing token")

#   jwt_token = token[len("Bearer "):]
#   claims = verify_jwt(jwt_token)
#   return {"message": "✅ Token verified", "claims": claims}