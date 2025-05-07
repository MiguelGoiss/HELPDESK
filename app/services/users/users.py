from app.database.models.helpdesk import Employees, Companies, EmployeeLogs, EmployeeContacts, EmployeePermissions
from app.utils.errors.exceptions import CustomError
from app.utils.helpers.paginate import paginate
from datetime import datetime
from .auth import create_token, validate_access_token
from app.utils.helpers.encryption import JOSEDictCrypto
from app.services.logs import LogService
from tortoise.expressions import Q
from tortoise.exceptions import DoesNotExist
import time
from functools import reduce
from operator import or_


async def validate_unique_fields(model_class, fields_to_check: dict, exclude_id: int | None = None):
  query_filters = []
  for field, value in fields_to_check.items():
    if value: # Apenas valida valores que não estejam vazios
      query_filters.append(Q(**{field: value}))

  if not query_filters:
    return # Nada a verificar

  query = model_class.filter(Q(*query_filters, join_type="OR"))
  if exclude_id is not None:
    query = query.exclude(id=exclude_id)

  existing_record = await query.first()
  if existing_record:
    # Encontra qual o campo que causou o erro
    for field, value in fields_to_check.items():
      if getattr(existing_record, field, None) == value:
        raise CustomError(
          400,
          f"O campo {field}, {value} já se encontra em uso."
        )
    raise CustomError(400, "A unique field conflict occurred.")

async def fetch_company_ids(company_ids: list[int]):
  try:
    companies = await Companies.filter(id__in=company_ids).all()
    return companies

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while fetching the companies",
      str(e)
    )

async def fetch_permission_ids(permission_ids: list[int]):
  try:
    permissions = await EmployeePermissions.filter(id__in=permission_ids).all()
    return permissions

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while fetching the permissions",
      str(e)
    )

async def insert_employee_contacts(contacts: list[dict[any, any]], user_id: int):
  try:
    for contact in contacts:
      contact['employee_id'] = user_id
      await EmployeeContacts().create(**contact)
      
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a inserir os contactos, mas o colaborador foi criado.",
      str(e)
    )  

async def create_user(user: dict, current_user: dict):
  try:
    await validate_unique_fields(Employees, {'username': user.username})
    if user.password:
      # Põe um hash na password inserida pelo cliente
      user.password = Employees.hash_password(user.password)

    # Convert para dict e extrai as linguas
    user_data = user.dict(exclude_unset=True)
    # Extrai as empresas do dicionario
    company_ids = user_data.pop('companies', None)
    employee_contacts = user_data.pop('contacts', None)
    employee_permission_ids = user_data.pop('permissions', None)

    # Criar o utilizador
    new_user = await Employees.create(**user_data)

    # Adiciona as empresas adicionais, se existirem
    if company_ids:
      # Tortoise não adicionar raw ids apenas modelos
      # É necessário obter as linguas da base de dados com base na lista de ids
      companies = await fetch_company_ids(company_ids)
      # Adiciona a associação dos modelos obtidos ao utilizador criado
      await new_user.companies.add(*companies)

    if employee_permission_ids:
      # O Tortoise não consegue adicionar chaves estrangeiras de uma ligação many_to_many apenas com ids
      # É necessário o modelo completo da base de dados
      # Obtem os modelos da base de dados através dos ids recebidos pelo cliente
      permissions = await fetch_permission_ids(employee_permission_ids)
      # Adiciona as associações dos modelos obtidos ao colaborador criado
      await new_user.permissions.add(*permissions)

    # Adicionar contactos do colaborador
    if employee_contacts:
      await insert_employee_contacts(employee_contacts, new_user.id)
    
    log_user_info = await new_user.to_dict_log()
    await LogService.log_action(
      action_type="user_created",
      employee_id=current_user['id'],
      model=EmployeeLogs,
      target_id=new_user.id,
      new_values=log_user_info,
      details="criou"
    )
    
    # Formatar o novo colaborador para resposta.
    user_dict = await new_user.to_dict()
    return user_dict

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while creating the user",
      str(e)
    )

# --- Configuração: Definição dos campos para pesquisas e order by ---
# Campos permitidos para a pesquisa geral 'search' (OR)
DEFAULT_OR_SEARCH_FIELDS: list[str] = ['first_name', 'last_name', 'full_name', 'employee_num']

# Campos permitidos para o search (AND)
ALLOWED_AND_FILTER_FIELDS: set[str] = {
  'id', 'first_name', 'last_name', 'full_name', 'employee_num',
  'username', 'email', 'department_id', 'company_id', 'local_id',
  'department__name', 'company__name', 'local__name'
}

# Campos permitidos para order
ALLOWED_ORDER_FIELDS: set[str] = {
  'id', 'first_name', 'last_name', 'full_name', 'employee_num',
  'created_at', 'updated_at', 'last_time_seen',
  'department__name', 'company__name', 'local__name',
}
# --- Fim da Configuração ---

async def get_users(
  path: str,
  page: int,
  page_size: int,
  original_query_params: dict[str, any] | None = None,
  # O parametro search serve para pesquisa (OR)
  search: str | None = None,
  # Dict para pesquisa especifica (AND)
  and_filters: dict[str, any] | None = None,
  # Campos para ordenação, usar o prefixo '-' para descendente
  order_by: str | None = None
):
  start = time.time()
  queryset = Employees.filter(deleted_at__isnull=True)

  # Aplicar os filtros (AND)
  if and_filters:
    valid_and_filters = {}
    for field, value in and_filters.items():
      if field in ALLOWED_AND_FILTER_FIELDS:
        # You could add more sophisticated lookup logic here if needed
        # e.g., if value is a list, use __in, or parse __gte, __lte etc.
        # For now, assuming exact match unless the field name implies otherwise
        filter_key = f"{field}__icontains"
        valid_and_filters[filter_key] = value
      else:
        raise CustomError(400, "Pesquisa inválida", "Não é possível filtrar pelo campo '{field}'.")
        
    if valid_and_filters:
      # Aplica filtros a com os argumentos acima
      queryset = queryset.filter(**valid_and_filters)

  # Aplica pesquisa geral (OR)
  if search:
    search_conditions = [
      Q(**{f"{field}__icontains": search}) for field in DEFAULT_OR_SEARCH_FIELDS
    ]
    if search_conditions:
      combined_condition = reduce(or_, search_conditions)
      queryset = queryset.filter(combined_condition)

  # Aplica os orders
  if order_by:
    # Valida os campos de order
    order_field_name = order_by.lstrip('-') # Obtem o campo sem o '-'
    if order_field_name in ALLOWED_ORDER_FIELDS:
      queryset = queryset.order_by(order_by) # Passa a string original com '-' (se for o caso)
    else:
      raise CustomError(400, "Ordenação inválida", f"Ordenação pelo campo '{order_field_name}' não é permitida.")
      queryset = queryset.order_by('id')

  # Fazer os dados relacionados (Prefetch) para maior eficiencia (IMPORTANTE! reduziu o tempo para metade!)
  # Garantir que todos os campos necessários no .to_dict() estão prefetched
  queryset = queryset.prefetch_related(
    'department',
    'company',
    'local',
    'employee_relation',
    'permissions',
    'employee_relation__contact_type'
  )

  # Chamar a função de paginação
  res = await paginate(
    queryset=queryset,
    url=path,
    page=page,
    page_size=page_size,
    original_query_params=original_query_params
  )
  end = time.time()
  print(f"get_users execution time: {end-start:.4f}s")
  return res

async def get_user_details(id: int):
  try:
    dbUser = await Employees.get(id=id).prefetch_related(
      'department',
      'company',
      'local',
      'employee_relation',
      'permissions',
      'employee_relation__contact_type'
    )
    
    return await dbUser.to_dict_details()

  except DoesNotExist:
    raise CustomError(
      404,
      "Colaborador não encontrado",
      f"Não foi possível encontrar um utilizador com o id: {id}."
    )
    
  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while fetching user details",
      str(e)
    )

async def fetch_user_for_changes(id: int):
  try:
    # Obtem o colaborador através do id
    db_user = await Employees.get(id=id)
    if not db_user:
      raise CustomError(
        404,
        "Colaborador não encontrado",
        None
      )
    return db_user

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while fetching the user",
       str(e)
    )

async def update_or_create_employee_contacts(contacts_data: list[dict], user_id: int):
  try:
    # Obtem todos os contactos existentes
    existing_contacts_qs = EmployeeContacts.filter(employee_id=user_id)
    existing_contacts_list = await existing_contacts_qs

    # Cria um set com todos os contactos existentes
    #    Guarda um tuplo com (contact_type_id, contact)
    existing_contacts_map = {
      (contact.contact_type_id, contact.contact): contact
      for contact in existing_contacts_list
    }

    contacts_to_create = []
    contacts_to_update = []
    processed_contact_ids = set() # Acompanha os ids do input que existe

    # Processa os contactos adicionados pelo cliente
    for contact_input in contacts_data:
      # Garante que o employee_id está no set
      contact_input['employee_id'] = user_id
      lookup_key = (contact_input.get('contact_type_id'), contact_input.get('contact'))

      if not lookup_key[0] or not lookup_key[1]:
        # Dá skip de dados inválidos
        continue

      existing_contact = existing_contacts_map.get(lookup_key)

      if existing_contact:
          # Contacto já existe - confirma se é necessário fazer update
          processed_contact_ids.add(existing_contact.id)
          needs_update = False
          update_payload = {}
          # Compara os campos relevantes (name, main_contact e public)
          # Add other fields you might want to update
          if contact_input.get('name') != existing_contact.name:
            needs_update = True
            update_payload['name'] = contact_input.get('name')
            
          if contact_input.get('main_contact') != existing_contact.main_contact:
            needs_update = True
            update_payload['main_contact'] = contact_input.get('main_contact')
            
          if contact_input.get('public') != existing_contact.public:
            needs_update = True
            update_payload['public'] = contact_input.get('public')

          if needs_update:
            # O Tortoise, precisa de instancias da base de dados
            # adiciona as instancias a uma lista
            for key, value in update_payload.items():
              setattr(existing_contact, key, value)
            contacts_to_update.append(existing_contact) # Adiciona as instancias ao update

      else:
        # Contacto não existe - prepara para criação
        # Adiciona os novos contactos à lista de criação
        contacts_to_create.append(EmployeeContacts(**contact_input))

    # Identifica os contactos para eliminar
    existing_contact_ids = {contact.id for contact in existing_contacts_list}
    contact_ids_to_delete = existing_contact_ids - processed_contact_ids

    # Executa as Operações
    if contacts_to_create:
      await EmployeeContacts.bulk_create(contacts_to_create)

    if contacts_to_update:
      await EmployeeContacts.bulk_update(
        contacts_to_update,
        fields=['name', 'main_contact', 'public'] # Campos para dar update
      )

    if contact_ids_to_delete:
      await EmployeeContacts.filter(id__in=list(contact_ids_to_delete)).delete()

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao editar os contactos do colaborador",
      str(e)
    )

async def add_or_remove_employee_companies(companies: list[dict[any, any]], employee_data: dict):
  try:
    # Acede à relação de many to many
    current_companies = await employee_data.companies
    current_company_ids = {company.id for company in current_companies}
    new_company_ids_set = set(companies)
    
    # Identifica as empresas a adicionar
    companies_to_add_ids = new_company_ids_set - current_company_ids
    companies_to_add = await Companies.filter(id__in=list(companies_to_add_ids))
    if companies_to_add:
      await employee_data.companies.add(*companies_to_add)
    
    # Identifica as empresas a remover
    companies_to_remove_ids = current_company_ids - new_company_ids_set
    companies_to_remove = await Companies.filter(id__in=list(companies_to_remove_ids))
    if companies_to_remove:
      await employee_data.companies.remove(*companies_to_remove)
    
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao editar as empresas do colaborador",
      str(e)
    )
    
async def add_or_remove_employee_permissions(permissions: list[int], employee_data: dict):
  try:
    # Acede à relação de many to many
    current_permissions = await employee_data.permissions
    # Cria um set com os ids das permissões
    current_permission_ids = {permission.id for permission in current_permissions}
    # Cria um ser com as permissões inseridas pelo cliente
    new_permission_ids_set = set(permissions)
    
    # Identifica as permissões a adicionar
    permissions_to_add_ids = new_permission_ids_set - current_permission_ids
    permissions_to_add = await EmployeePermissions.filter(id__in=list(permissions_to_add_ids))
    if permissions_to_add:
      await employee_data.permissions.add(*permissions_to_add)
    
    # Identifica as permissões a remover
    permissions_to_remove_ids = current_permission_ids - new_permission_ids_set
    permissions_to_remove = await EmployeePermissions.filter(id__in=list(permissions_to_remove_ids))
    if permissions_to_remove:
      await employee_data.permissions.remove(*permissions_to_remove)
    
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao editar as permissões do colaborador",
      str(e)
    )

async def update_user_details(id: int, user_data: dict, current_user: dict):
  try:
    db_user = await fetch_user_for_changes(id)

    await validate_unique_fields(Employees, { 'username': user_data.username }, db_user.id)

    # Remove as chaves com valor None
    update_data = user_data.dict(exclude_unset=True)
    
    # Extrai os contactos e empresas do dict se existir
    contacts = update_data.pop('contacts', None)
    companies = update_data.pop('companies', None)
    permissions = update_data.pop('permissions', None)
    
    # Se for para desativar o utilizador procura o campo "deactivate"
    if 'deactivate' in update_data:
      if getattr(user_data, 'deactivate'):
        update_data['deactivated_at'] = datetime.now()
      else:
        update_data['deactivated_at'] = None

    # Adiciona o campo updated_at ao dict
    update_data['updated_at'] = datetime.now()

    if 'password' in update_data:
      update_data['password'] = db_user.hash_password(getattr(user_data, 'password'))

    # Obtem os detalhes do utilizador antes das alterações
    before_changes = await db_user.to_dict_log()
    await db_user.update_from_dict(update_data).save()
    
    # Atualiza os contactos se existir na lista
    if contacts:
      await update_or_create_employee_contacts(contacts, db_user.id)
    
    if companies:
      await add_or_remove_employee_companies(companies, db_user)
    
    if permissions:
      await add_or_remove_employee_permissions(permissions, db_user)
      
    # Obtem os detalhes do utilizador depois das alterações
    # updated_user = await fetch_user_for_changes(id)
    await db_user.refresh_from_db()
    after_changes = await db_user.to_dict_log()
    if 'password' in update_data:
      after_changes['password'] = "ALTERADA"

    # Adiciona um log com as alterações gerais do utilizador, antes e depois da edição
    await LogService.log_action(
      action_type="user_updated",
      employee_id=current_user['id'],
      model=EmployeeLogs,
      target_id=db_user.id,
      new_values=before_changes,
      old_values=after_changes,
      details=f"editou"
    )
    # Obtem o utilizador com as novas atualizações para a resposta
    user_details = await get_user_details(db_user.id)
    return user_details

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while updating the user",
      str(e)
    )

async def delete_user_details(id: int):
  try:
    # Obtem o colaborador através do id
    db_user = await fetch_user_for_changes(id)
    # Atualiza o campo de "deleted_at" com a data atual
    await db_user.update_from_dict({ 'deleted_at': datetime.now() }).save()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while deleting the user",
      str(e)
    )

async def user_authentication(authentication_form: dict):
  try:
    # Valida o username inserido se existe em algum colaborador que não esteja desativado nem apagado
    db_user = Employees.filter(username=authentication_form.username, deactivated_at=None, deleted_at=None).first()
    db_user = await db_user.prefetch_related(
      'permissions',
      'employee_relation',
      'employee_relation__contact_type'
    )
    # Verifica a password se corresponde com a recebida pelo cliente
    if not db_user or not db_user.verify_password(authentication_form.password, db_user.password):
      raise CustomError(
        401,
        "Incorrect username or password",
      )
    # Formata os dados do utilizador para dict
    user_info = await db_user.to_dict()
    # Cria o access token com exp de 30 mins
    access_token = await create_token(user_info, 'access')
    # Cria o refresh token com exp de 5 dias
    refresh_token = await create_token(user_info, 'refresh')

    # Devolve os tokens
    return {
      "access_token": access_token,
      "refresh_token": refresh_token
    }

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while authenticating the user",
      str(e)
    )

async def read_user_me(token: dict):
  try:
    # Verifica o token recebido pelo cliente se é válido
    return await validate_access_token(token)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while validating user",
      str(e)
    )

async def fetch_email_user(email: str):
  try:
    # Obtem o utilizador através do email
    print(email)
    db_user = await Employees.get(employee_relation__contact=email, employee_relation__main_contact=True)
    if not db_user:
      raise CustomError(
        404,
        "User not found"
        "A User with the requested email could not be found"
      )
    return await db_user.to_dict_details()

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while fetching the user email",
      str(e)
    )

async def add_recovery_token(id: int, recovery_token: str):
  try:
    # Obtem o utilizador através do id
    db_user = await fetch_user_for_changes(id)
    # É inserido o recovery_token no utilizador
    await db_user.update_from_dict(
      {
        "recovery_token": recovery_token
      }
    ).save()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while sending the recovery email",
      str(e)
    )

async def code_verification(code: dict):
  try:
    crypto = JOSEDictCrypto()
    # Obtem o utilizador através do id recebido no body
    db_user = await Employees.get_or_none(id=code.id)

    if not db_user.recovery_token:
      raise CustomError(
        403,
        "Invalid request",
        "Este utilizador não tem recovery_token. Não fez o pedido ou ocorreu durante o pedido."
      )
    # Tenta desencriptar o token
    decrypt_code = crypto.decrypt_dict(db_user.recovery_token)

    # Valida a data de expiração do token
    if decrypt_code['exp'] < datetime.now().timestamp():
      # Se a data de expiração já tiver passado, remove o token do colaborador e repõe as tentativas
      await db_user.update_from_dict(
        {
          "recovery_token": None,
          "recovery_attempts": 4
        }
      ).save()
      raise CustomError(
        403,
        "Code has expired"
      )

    # Confirma se o código do token e o código recebido do cliente são iguais
    if decrypt_code['secret'] == code.code:
      return await db_user.to_dict_details()


    if db_user.recovery_attempts > 0:
      # Ao falhar no token é alterado a quantidade de tentativas do utilizador para n-1 enquanto n for > 0
      await db_user.update_from_dict(
        {
          "recovery_attempts":db_user.recovery_attempts-1
        }
      ).save()
      raise CustomError(
        401,
        "Code is not valid",
        f"{db_user.recovery_attempts+1} attempts missing."
      )
    # Após chegar a 0 tentativas, o token será eliminado e as tentativas repostas
    await db_user.update_from_dict(
      {
        "recovery_token": None,
        "recovery_attempts": 4
      }
    ).save()
    # Devolve 403 para no cliente retirar o utilizador da página de inserção do código
    raise CustomError(
      403,
      "Maximum attempts reached",
      "Este utilizador chegou ao limite de tentativas e o código foi eliminado."
    )

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while verifying the code",
      str(e)
    )

async def update_user_password(recovery_form: dict):
  try:
    # Obtem o colaborador pelo id
    db_user = await Employees.get(id=recovery_form.id)
    # Verifica a legitimidade do código inserido novamente
    await code_verification(recovery_form)
    # Cria o hash da password inserida pelo cliente
    password = Employees.hash_password(recovery_form.password)
    # Insere a nova password na base de dados
    await db_user.update_from_dict({"password": password}).save()
    return {'message': "Senha recuperada com sucesso"}

  except Exception as e:
    raise CustomError(
      500,
      "An error occurred while recovering the user password",
      str(e)
    )

async def get_employees_with_permission(permission_id: int, search: str | None = None):
  try:
    # Filtra os colaboradores que têm a permissão recebida
    queryset = Employees.filter(
      permissions__id=permission_id,
      deactivated_at__isnull=True,
      deleted_at__isnull=True
    )

    if search:
      search_conditions = [
        Q(first_name__icontains=search),
        Q(last_name__icontains=search),
        Q(full_name__icontains=search),
        Q(local__name__icontains=search),
        Q(department__name__icontains=search),
        Q(employee_relation__contact__icontains=search, employee_relation__public=True)
      ]
      combined_condition = reduce(or_, search_conditions)
      queryset = queryset.filter(combined_condition)

    employees_with_permission = await queryset.prefetch_related(
      'local', 
      'department',
      'employee_relation',
      'employee_relation__contact_type'
    ).distinct().all() 
    # .distinct() por causa do join no employee_relation pode mostrar dados duplicados
    # se um colaborador tiver vários contactos que iguale à pesquisa
    # if an employee has multiple contacts matching the search term.
    return [await employee.to_dict_contacts() for employee in employees_with_permission]

  except Exception as e:
    raise CustomError(
      500,
      f"Ocorreu um erro ao obter os colaboradores com a permissão {permission_id}",
      str(e)
    )
    
async def get_users_by_ids(ids: list[int]):
  try:
    # Obtem objetos dos ids pedidos.
    db_employees = Employees.filter(id__in=ids, deactivated_at__isnull=True, deleted_at__isnull=True)
    return await db_employees.all()
  
  except DoesNotExist as e:
    raise CustomError(
      404,
      "Colaboradores não encontrados",
      str(e)
    )
  
  except Exception as e:
    raise e

async def get_employee_basic_info(id: int) -> dict:
  try:
    # Obtem as informações básicas de um utilizador com o email
    db_employee = await Employees.filter(id=id, deactivated_at__isnull=True, deleted_at__isnull=True).first()
    if not db_employee:
      return None
    return await db_employee.to_dict_employee_emails()
    
  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao obter as informações do colaborador",
      str(e)
    )
    