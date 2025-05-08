import re
from html import escape
from urllib.parse import quote

def sanitize_input(
  user_input,
  input_type="text",
  allow_html=False,
  allow_special_chars=False,
  strip=True
):
  """
  Sanitize user input to prevent security vulnerabilities and malformed data.
  
  For 'text' input type, multiple consecutive whitespace characters within the string will be collapsed into a single space.

  Args:
    user_input: The input to be sanitized (str, int, float, etc.)
    input_type: Type of input ('text', 'email', 'url', 'int', 'float')
    allow_html: Whether to allow HTML tags (False by default for security). If False, HTML entities are escaped.
    allow_special_chars: Whether to allow special characters
    strip: Whether to strip whitespace from both ends
  
  Returns:
    Sanitized input in the appropriate type
      
  Raises:
    ValueError: If input fails validation
  """
    
  if user_input is None:
    return None
      
  # Convert to string for initial processing
  str_input = str(user_input)
  
  # Strip whitespace if requested
  if strip:
    str_input = str_input.strip()
  
  # Handle different input types
  if input_type == "email":
    if not re.match(r"[^@]+@[^@]+\.[^@]+", str_input):
      raise ValueError("Invalid email format")
    return str_input.lower()
  
  elif input_type == "url":
    # Basic URL validation
    if not re.match(r"https?://[^\s/$.?#].[^\s]*", str_input, re.IGNORECASE):
      raise ValueError("Invalid URL format")
    return quote(str_input, safe='/:?=&')
  
  elif input_type == "int":
    try:
      return int(str_input)
    except ValueError:
      raise ValueError("Input must be a valid integer")
  
  elif input_type == "float":
    try:
      return float(str_input)
    except ValueError:
      raise ValueError("Input must be a valid number")
  
  else:  # text or other
    # 1. Collapse multiple internal whitespaces to a single space
    str_input = re.sub(r'\s+', ' ', str_input)

    # 2. Escape HTML by default
    if not allow_html:
      str_input = escape(str_input)
    
    # 3. Remove special characters if not allowed
    if not allow_special_chars:
      str_input = re.sub(r'[^\w\s\-.,!?:]', '', str_input)
    
    return str_input