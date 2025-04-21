from jose import jwe, jwk
from jose.utils import base64url_encode
from dotenv import load_dotenv
import json
import os

load_dotenv()

RECOVERY_SECRET = os.getenv('JWT_RECOVERY_SECRET')

class JOSEDictCrypto:
  def __init__(self, key=RECOVERY_SECRET):
    if len(key) < 32:
      raise ValueError("Key must be at least 32 bytes")
    # Use first 32 bytes for AES-256
    self.encryption_key = key[:32]
    
  def encrypt_dict(self, data_dict):
    return jwe.encrypt(
      json.dumps(data_dict),
      self.encryption_key,
      algorithm='dir',
      encryption='A256GCM'
    )
  
  def decrypt_dict(self, encrypted_jwe):
    return json.loads(jwe.decrypt(encrypted_jwe, self.encryption_key).decode('utf-8'))
