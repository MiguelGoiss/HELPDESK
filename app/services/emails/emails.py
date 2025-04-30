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
  # Carrega o template HTML
  template_path = "app/utils/templates/ticket_email.html"
  with open(template_path, "r", encoding="utf-8") as file:
    template_content = file.read()

  if ticket_email_type == 'create':
    email_dict = {
      "title": "Confirmação de Ticket de Suporte",
      "text_1": [
        "Confirmamos que o seu ticket de suporte foi criado com sucesso. Agradecemos o seu contacto!"
      ],
      "text_2": [
        "A nossa equipa de suporte irá rever o seu pedido e entrará em contacto consigo o mais rapidamente possível."
      ],
      "link_text": {
        "text":"Pode acompanhar o estado do seu ticket através deste link:",
        "link":f"172.17.1.52:5923/ticket/details/{ticket_details['uid']}"
      },
      "text_3": [
        "Obrigado pela sua paciência"
      ],
      "text_4": [
        "Com os melhores cumprimentos,",
        "A Equipa de Suporte"
      ]
    }
  elif ticket_email_type == 'assigned':
    email_dict = {
      "title": "Ticket de Suporte Atribuído",
      "text_1": [
        f"Caro(a) {requester_info['first_name']} {requester_info['last_name']},",
        f"Informamos que o seu ticket de suporte foi alocado a {agent_info['first_name']} {agent_info['last_name']}!"
      ],
      "text_2": [
        "Se tiver alguma informação adicional, por favor responda para <a style='padding:0; margin:0' href='mailto:suporte@afa.pt'>suporte@afa.pt</a> ou <a style='padding:0; margin:0' href='mailto:suporte@savoysignature.pt'>suporte@savoysignature.pt</a>",
      ],
      "link_text": {
        "text":"Pode acompanhar o estado do seu ticket através deste link:",
        "link":f"172.17.1.52:5923/ticket/details/{ticket_details['uid']}"
      },
      "text_3": [
        "Obrigado pela sua paciência"
      ],
      "text_4": [
        "Com os melhores cumprimentos,",
        "A Equipa de Suporte"
      ]
    }
  elif ticket_email_type == 'closed':
    email_dict = {
      "title": "Ticket de Suporte Fechado",
       "text_1": [
        f"Caro(a) {requester_info['first_name']} {requester_info['last_name']},",
        f"Informamos que o seu ticket de suporte foi fechado.",
      ],
      "text_2": [
        "Ajude-nos a ajuda-lo!",
        "Estamos constantemente a tentar melhorar a sua experiência.",
        "Invista 1 minuto para uma melhor experiência! Preencha o questionário de satisfação <a href='#'>aqui</a>",
      ],
      "link_text": {
        "text":"Se o problema se mantiver pode reabrir e adicionar informação adicional ao ticket através deste link:",
        "link":f"172.17.1.52:5923/ticket/details/{ticket_details['uid']}"
      },
      "text_3": [
        "Obrigado pela sua paciência"
      ],
      "text_4": [
        "Com os melhores cumprimentos,",
        "A Equipa de Suporte"
      ]
    }
  elif ticket_email_type == 'reopened':
    email_dict = {
      "title": "Ticket de Suporte Re-Aberto",
      "text_1": [
        f"Confirmamos que o seu ticket foi reaberto com sucesso. E encontra-se alocado a {agent_info['first_name']} {agent_info['last_name']}"
      ],
      "text_2": [
        "A nossa equipa de suporte irá rever o seu pedido e entrará em contacto consigo o mais rapidamente possível."
      ],
      "link_text": {
        "text":"Pode acompanhar o estado do seu ticket através deste link:",
        "link":f"172.17.1.52:5923/ticket/details/{ticket_details['uid']}"
      },
      "text_3": [
        "Obrigado pela sua paciência"
      ],
      "text_4": [
        "Com os melhores cumprimentos,",
        "A Equipa de Suporte"
      ]
    }
  
  email_dict['email_type'] = ticket_email_type
  
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
    if agent_info['email']:
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