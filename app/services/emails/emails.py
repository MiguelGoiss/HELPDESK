from app.utils.errors.exceptions import CustomError
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Template
from datetime import datetime, timedelta
import random
from app.utils.helpers.encryption import JOSEDictCrypto
from app.services.users import add_recovery_token
conf = ConnectionConfig(
  MAIL_USERNAME="noreply",
  MAIL_PASSWORD="impressoras",
  MAIL_FROM="noreply@savoysignature.com",
  MAIL_PORT=587,
  MAIL_SERVER="mail.savoysignature.com",
  MAIL_STARTTLS=True,
  MAIL_SSL_TLS=False,
  USE_CREDENTIALS=True,
  VALIDATE_CERTS=True
)

def generate_6_digit_code():
  return f"{random.randint(0, 999999):06d}"

async def recovery_email(request_user: dict):
  try:
    crypto = JOSEDictCrypto()
    six_digit_secret = generate_6_digit_code()
    
    crypto_dict = {
      "id": request_user['id'],
      "first_name": request_user['first_name'],
      "last_name": request_user['last_name'],
      "exp": (datetime.now() + timedelta(minutes=15)).timestamp(),
      "secret": six_digit_secret
    }
    
    encrypted = crypto.encrypt_dict(crypto_dict)
    
    await add_recovery_token(request_user['id'], encrypted.decode('utf-8'))
    
    # Load HTML template
    template_path = "app/utils/templates/recovery_email.html"
    with open(template_path, "r") as file:
      template_content = file.read()
    
    # Render template with variables
    html_content = Template(template_content).render(
      verification_code=six_digit_secret,
      current_year=datetime.now().year
    )
    
    for contact in request_user['contacts']:
      if contact['main_contact'] and contact['contact_type']['id'] == 1:
        email = contact['contact']
    
    message = MessageSchema(
      subject="Password Recovery",
      recipients=[email],
      body=html_content,
      subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return encrypted.decode('utf-8')
  
  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError (
      500,
      "An error occurred during the recovery process",
      str(e)
    )
    
async def ticket_email(ticket_details: dict, requester_info: dict, agent_info: dict | None = None, ticket_email_type: str = "create"):
  # Load HTML template
  template_path = "app/utils/templates/ticket_email.html"
  with open(template_path, "r", encoding="utf-8") as file:
    template_content = file.read()
  
  if ticket_email_type == 'create':
    email_dict = {
      "title": "Confirmação de Ticket de Suporte"
    }
  
  email_dict['ticket_type'] = ticket_email_type
  
  # Render template with variables
  html_content = Template(template_content).render(
    email_dict=email_dict,
    ticket_details=ticket_details,
    requester_info=requester_info,
    agent_info=agent_info,
    current_year=datetime.now().year
  )
  
  ccs = [cc['email'] for cc in ticket_details['ccs']]
  if agent_info:
    ccs.append(agent_info['email'])
  
  message = MessageSchema(
    subject=ticket_details['subject'],
    recipients=[requester_info['email']],
    cc=ccs,
    body=html_content,
    subtype="html"
  )
  fm = FastMail(conf)
  await fm.send_message(message)