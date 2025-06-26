from functools import reduce
from operator import or_, and_
from tortoise.queryset import QuerySet
from app.utils.errors.exceptions import CustomError
from tortoise.expressions import Q
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


# Função auxiliar interna para processar um dicionário de filtros e preparar kwargs para Tortoise .filter()
# Alterado para devolver uma lista de objetos Q
def _build_q_objects_from_filter_dict(
  filters_source: dict[str, any] | str | None,
  date_fields_config: set[str],
  allowed_fields_config: set[str]
) -> list[Q]:
  """
  Processa um dicionário de filtros (ou uma string JSON)
  e devolve uma LISTA de objetos Q do Tortoise.
  Valida os campos contra date_fields_config e allowed_fields_config.
  """
  if not filters_source:
    return []

  actual_filters_dict: dict[str, any]
  if isinstance(filters_source, str):
    try:
      loaded_json = json.loads(filters_source)
      if not isinstance(loaded_json, dict):
        logger.warning(f"Filtro JSON carregado não é um dicionário: {filters_source}")
        return []
      actual_filters_dict = loaded_json
    except json.JSONDecodeError as e:
      raise CustomError(400, "Formato de filtro inválido", f"O dicionário de filtros (string JSON) não é válido: {e}")
  elif isinstance(filters_source, dict):
    actual_filters_dict = filters_source
  else:
    logger.warning(f"Tipo de fonte de filtros inesperado: {type(filters_source)}")
    return []

  if not actual_filters_dict: # Trata dicionário vazio ou dicionário de JSON vazio/não-dicionário
    return []

  q_objects = []
  for field, value in actual_filters_dict.items():
    # --- Filtro de datas ---
    if field.endswith('_after'):
      base_field = field[:-6] # Remove o '_after'
      if base_field in date_fields_config:
        try:
          start_date = datetime.fromisoformat(str(value)).date()
          filter_key = f"{base_field}__gte"
          q_objects.append(Q(**{filter_key: datetime.combine(start_date, datetime.min.time())}))
        except ValueError:
          raise CustomError(400, "Formato de data inválido", f"Formato inválido para '{field}'. Usar YYYY-MM-DD.")
      else:
        raise CustomError(400, "Filtro inválido", f"Não é possível filtrar por data no campo '{base_field}'. Campo não permitido para filtro de data.")
    elif field.endswith('_before'):
      base_field = field[:-7] # Remove o '_before'
      if base_field in date_fields_config:
        try:
          end_date = datetime.fromisoformat(str(value)).date()
          # Para tornar '_before' exclusivo da data fornecida, filtramos por menos que o início do dia seguinte.
          next_day_start = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
          filter_key = f"{base_field}__lt"
          q_objects.append(Q(**{filter_key: next_day_start}))
        except ValueError:
          raise CustomError(400, "Formato de data inválido", f"Formato inválido para '{field}'. Usar YYYY-MM-DD.")
      else:
        raise CustomError(400, "Filtro inválido", f"Não é possível filtrar por data no campo '{base_field}'. Campo não permitido para filtro de data.")
    # --- Filtro de campos que não são datas ---
    elif field in allowed_fields_config:
      print(field)
      if isinstance(value, str) and not field.endswith('_id') and field != "id" and not field.endswith('_isnull'):
        if ',' in value:
          parts = [part.strip() for part in value.split(',') if part.strip()]
          if parts:
            # Cria um objeto Q para cada parte e combina-os com AND para este campo específico.
            # Cada parte deve estar contida no campo.
            print(f"{field}__icontains")
            field_specific_q_objects = [Q(**{f"{field}__icontains": part}) for part in parts]
            q_objects.append(reduce(or_, field_specific_q_objects))
          # Se 'parts' estiver vazio (ex: valor era apenas ","), nenhum filtro é adicionado para este campo.
        else:
          # Sem vírgula, comportamento original de __icontains para o valor completo.
          
          print(f"{field}_icontains: {value}")
          q_objects.append(Q(**{f"{field}__icontains": value}))
      elif isinstance(value, list):
        # Filtro para correspondência em lista de valores.
        # Confirma se existe algum valor dentro do value que seja lista.
        _type = None
        if ':' in str(value[-1]):
          _type = value[-1].split(':').pop()
          value[-1] = value[-1][:-2]

        
        if any(isinstance(item, list) for item in value):
          # Se pelo menos 1 dos elementos do value for uma lista
          # Trata como: (cond1 OR cond2) AND (cond3 OR cond4) ...
          # Onde cada elemento de 'value' pode ser uma lista de condições OR-ed, ou uma string única.
          for element_in_value in value: # element_in_value can be a list or a string
            current_or_group_qs = []
            if isinstance(element_in_value, list): # This is a sub-list for OR conditions
              for part in element_in_value:
                part_str = str(part).strip() # Ensure part is a string and stripped
                if part_str: # Only add if part is non-empty
                  current_or_group_qs.append(Q(**{f"{field}__icontains": part_str}))
            elif isinstance(element_in_value, str): # This is a single string condition
              part_str = element_in_value.strip()
              if part_str:
                current_or_group_qs.append(Q(**{f"{field}__icontains": part_str}))
            
            if current_or_group_qs: # Garante que current_or_group_qs não está vazia antes de reduce
              q_objects.append(reduce(or_, current_or_group_qs))
          
        # ELIF: If not a list containing sub-lists, check if it's a flat list of strings.
        # Example: value = ["tagA", "tagB"] -> field__icontains="tagA" OR field__icontains="tagB"
        elif all(isinstance(item, str) for item in value): # `all` ensures it's purely a list of strings
          current_or_group_qs = []
          for item_str in value:
            part_str = item_str.strip() # item_str is already a string
            if part_str:
              current_or_group_qs.append(Q(**{f"{field}__icontains": part_str}))
          if current_or_group_qs: # Only add if there are actual conditions
            q_objects.append(reduce(or_, current_or_group_qs))

        else:
          # Fallback for other list types, e.g., list of IDs for an __in query
          q_objects.append(Q(**{f"{field}__in": value}))
      else:
        value = str(value)
        print("\n\nVALUE:",str(value))
        if ',' in value:
          values = [part_val.strip() for part_val in value.split(',') if part_val.strip()]
        
          # Cria um objeto Q para cada parte e combina-os com AND para este campo específico.
          # Cada parte deve estar contida no campo.
          q_objects.append(Q(**{f"{field}__in": values}))
        elif field.endswith('_isnull'):
          # Se a pesquisa for feita com __isnull, deve ser feita com o valor 0/1 para conseguir 
          # transformar em boolean, para a query
          q_objects.append(Q(**{field: bool(int(value))}))
        else:
          # Correspondência exata para outros tipos ou campos _id.
          q_objects.append(Q(**{field: value}))
    else:
      raise CustomError(400, "Filtro inválido", f"Não é possível filtrar pelo campo '{field}'. Campo não permitido para filtro.")
  print(str(q_objects))
  
  return q_objects

def _apply_and_filters(
    queryset: QuerySet,
    DATE_FIELDS: set[str] | None,
    ALLOWED_AND_FILTER_FIELDS: set[str],
    filters_dict: dict[str, any] | str | None,
  ) -> QuerySet:
  """
  Aplica filtros AND a um queryset do Tortoise.
  Valida campos e trata tipos de dados.
  Suporta tratamento específico para filtros de intervalo de datas (usando sufixos `_after`
  e `_before`), filtros de lista (usando `__in`), e filtros de string (usando `__icontains`).
  Se uma string para um campo não-ID contiver vírgulas, ela é dividida, e cada parte
  deve estar contida no campo (lógica AND para as partes).
  Os nomes dos campos são validados contra as listas `DATE_FIELDS` e `ALLOWED_AND_FILTER_FIELDS`.

  Args:
    queryset: O queryset do Tortoise ao qual os filtros serão aplicados.
    DATE_FIELDS: Conjunto de nomes de campos de data permitidos para filtros de intervalo.
                 Pode ser None se não houver campos de data a serem considerados.
    ALLOWED_AND_FILTER_FIELDS: Conjunto de nomes de campos permitidos para filtros diretos.
    filters_dict: Um dicionário (ou string JSON) com os filtros do cliente. Pode ser None.

  Returns:
    O queryset com todos os filtros AND aplicados.

  Raises:
    CustomError:
      - Se `filters_dict` for uma string JSON inválida.
      - Se um campo usado com o sufixo `_after` ou `_before` não estiver em `DATE_FIELDS`.
      - Se um valor de data fornecido para um filtro de data tiver um formato inválido (espera-se YYYY-MM-DD).
      - Se um campo para filtragem direta não estiver em `ALLOWED_AND_FILTER_FIELDS`.
  """
  
  # Aplica filtros (AND) ao queryset
  if filters_dict:
    q_conditions = _build_q_objects_from_filter_dict(
      filters_dict,
      DATE_FIELDS if DATE_FIELDS is not None else set(),
      ALLOWED_AND_FILTER_FIELDS
    )
    
    if q_conditions:
      # Aplica todos os objetos Q; o Tortoise irá combiná-los com AND.
      for q_condition_group in q_conditions:
        queryset = queryset.filter(q_condition_group)
  return queryset

def _apply_or_search(queryset: QuerySet, DEFAULT_OR_SEARCH_FIELDS: list[str], search: str | None) -> QuerySet:
  """
  Aplica condições de pesquisa complexas (AND entre palavras, OR entre campos para cada palavra)
  a um queryset do Tortoise ORM usando campos pré-definidos.

  A string de pesquisa `search` é dividida em palavras. Para que um registo seja correspondente,
  TODAS as palavras da string de pesquisa devem ser encontradas.
  Para CADA palavra individual, esta deve ser encontrada em PELO MENOS UM dos campos
  especificados em `DEFAULT_OR_SEARCH_FIELDS`.

  Exemplo: Se search="palavra1 palavra2" e DEFAULT_OR_SEARCH_FIELDS=["titulo", "conteudo"],
  a lógica será:
  ( (titulo contém "palavra1") OU (conteudo contém "palavra1") )
  E
  ( (titulo contém "palavra2") OU (conteudo contém "palavra2") )

  Se um campo em `DEFAULT_OR_SEARCH_FIELDS` for 'id' e uma palavra na string de pesquisa
  for um número inteiro, a pesquisa para essa palavra nesse campo será uma correspondência exata do ID.
  Para outros campos, ou para o campo 'id' se a palavra não for um inteiro, a pesquisa utiliza `__icontains`
  (não sensível a maiúsculas/minúsculas).

  Args:
    queryset: O queryset do Tortoise ORM ao qual as condições de pesquisa serão aplicadas.
    DEFAULT_OR_SEARCH_FIELDS: Uma lista de strings contendo os nomes dos campos
                              do modelo nos quais a pesquisa deve ser realizada para cada palavra.
    search: A string de pesquisa a ser aplicada. Se for `None` ou uma string vazia,
            o queryset original é retornado sem modificações.

  Returns:
    O queryset com as condições de pesquisa complexas aplicadas.
    Retorna o queryset original se `search` for `None`/vazio, `DEFAULT_OR_SEARCH_FIELDS` estiver vazio,
    ou se a string de pesquisa não contiver palavras após a divisão.
  """
  if not search or not search.strip() or not DEFAULT_OR_SEARCH_FIELDS:
    return queryset

  words = [word for word in search.split() if word] # Divide por espaços e remove palavras vazias
  if not words: # Trata o caso em que a pesquisa era apenas espaços em branco
    return queryset

  all_word_group_conditions = []

  for word in words:
    current_word_or_conditions = []
    for field in DEFAULT_OR_SEARCH_FIELDS:
      if field == 'id':
        if word.isdigit():
          try:
            current_word_or_conditions.append(Q(id=int(word)))
          except ValueError: 
            logger.error(f"Erro ao converter a palavra '{word}' para inteiro para pesquisa no campo 'id'.", exc_info=True)
        # Se a palavra não for um dígito, não tentamos Q(id__icontains=word)
      else: # O campo não é 'id'
        filter_key = f"{field}__icontains"
        current_word_or_conditions.append(Q(**{filter_key: word}))
    
    if current_word_or_conditions:
      # Para esta palavra, ela deve ser encontrada em qualquer um dos campos (OR)
      word_group_q = reduce(or_, current_word_or_conditions)
      all_word_group_conditions.append(word_group_q)

  # Se nem todas as palavras puderam formar um grupo de pesquisa pesquisável, então a condição AND geral falha.
  if len(all_word_group_conditions) < len(words):
    return queryset.none() # Retorna um queryset vazio
  
  # Se all_word_group_conditions estiver vazio neste ponto, significa que words também estava vazio (já tratado),
  # ou que len(all_word_group_conditions) < len(words) já foi acionado.
  # Portanto, se chegarmos aqui, all_word_group_conditions tem pelo menos um elemento e o seu comprimento é igual a len(words).

  combined_all_words_condition = reduce(and_, all_word_group_conditions)
  queryset = queryset.filter(combined_all_words_condition)
  
  return queryset

def _apply_ordering(queryset: QuerySet, ALLOWED_ORDER_FIELDS: set[str], default_order: str, order_by: str | None = None) -> QuerySet:
  """
  Aplica ordenação num queryset do Tortoise, validando o campo de ordenação
  e utilizando uma ordenação padrão caso nenhuma seja especificada.

  Se `order_by` for fornecido, a função verifica se o campo base (sem o prefixo '-')
  está na lista `ALLOWED_ORDER_FIELDS`. Se for válido, aplica a ordenação.
  Caso contrário, levanta um `CustomError`. Se `order_by` não for fornecido,
  aplica a ordenação especificada em `default_order`.

  Args:
    queryset: O queryset do Tortoise ORM ao qual a ordenação será aplicada.
    order_by: Uma string opcional especificando o campo e a direção da ordenação
              (ex: 'created_at' para ascendente, '-created_at' para descendente).
    default_order: A string de ordenação padrão a ser aplicada se `order_by`
                   não for fornecido (ex: '-created_at').
    ALLOWED_ORDER_FIELDS: Um conjunto de strings contendo os nomes dos campos
                          permitidos para ordenação.

  Returns:
    O queryset com a ordenação aplicada.

  Raises:
    CustomError: Se o campo especificado em `order_by` não estiver em
                 `ALLOWED_ORDER_FIELDS`.
  """
  if order_by:
    # Remove o prefixo '-' para validar o nome base do campo
    order_field_name = order_by.lstrip('-')
    if order_field_name in ALLOWED_ORDER_FIELDS:
      queryset = queryset.order_by(order_by)
    else:
      raise CustomError(400, "Ordenação inválida", f"Ordenação pelo campo '{order_field_name}' não é permitida.")
  else:
    # Aplica a ordenação padrão se nenhuma específica for fornecida
    queryset = queryset.order_by(default_order)
  return queryset