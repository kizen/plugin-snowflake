import http.client
import json
import uuid
import re

def connect_to_snowflake():
  secret_connection = next(iter(key for key in secrets if key.endswith("snowflake_connection")), None)
  if not secret_connection:
      raise ValueError("No snowflake_connection secret found")
  SNOWFLAKE_CONNECTION_RAW = secrets[secret_connection]

  # Replace curly quotes with straight quotes
  SMART_QUOTE_MAP = str.maketrans({
      '\u201c': '"',  # “
      '\u201d': '"',  # ”
      '\u2018': "'",  # ‘
      '\u2019': "'",  # ’
      '\u201b': "'",  # ‛ single high-reversed-9
      '\u201e': '"',  # „ double low-9
      '\u201f': '"',  # ‟ double high-reversed-9
  })
  cleaned_json = SNOWFLAKE_CONNECTION_RAW.translate(SMART_QUOTE_MAP)
  SNOWFLAKE_CONNECTION = json.loads(cleaned_json)

  # Pick which env you want
  conn_data = {}
  if getattr(inputs, "connection_secret_tag", None):
    if inputs.connection_secret_tag not in SNOWFLAKE_CONNECTION:
      raise ValueError(f"Connection secret tag {inputs.connection_secret_tag} not found in SNOWFLAKE_CONNECTION")
    conn_data = SNOWFLAKE_CONNECTION[inputs.connection_secret_tag]
  else:
    # If no connection secret tag is provided, SNOWFLAKE_CONNECTION isn't nested
    conn_data = SNOWFLAKE_CONNECTION
  
  REQUIRED_KEYS = ('warehouse', 'schema', 'account', 'pat')
  missing_keys = [key for key in REQUIRED_KEYS if key not in conn_data]
  if missing_keys:
      raise ValueError(f"Snowflake connection secret is missing required key(s): {', '.join(missing_keys)}")

  SNOWFLAKE_WAREHOUSE = conn_data['warehouse']
  SNOWFLAKE_SCHEMA = conn_data['schema']
  SNOWFLAKE_ACCOUNT = conn_data['account']
  SNOWFLAKE_PAT = conn_data['pat']

  INPUT_DATABASE = inputs.database
  INPUT_QUERY = inputs.query

  # Basic SQL guardrail - reject obvious write operations before hitting DB
  write_keywords = r'^\s*(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|COPY|CALL|DO)\b'
  if re.match(write_keywords, INPUT_QUERY, re.IGNORECASE):
    raise ValueError("Write operations are not allowed. Only SELECT queries permitted.")

  conn = http.client.HTTPSConnection(f"{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com")
  payload = json.dumps({
    "statement": INPUT_QUERY,
    "timeout": 30,
    "database": INPUT_DATABASE,
    "schema": SNOWFLAKE_SCHEMA,
    "warehouse": SNOWFLAKE_WAREHOUSE,
    "bindings": {},
    "parameters": {}
  })
  headers = {
    'User-Agent': 'myApplication/1.0',
    'X-Snowflake-Authorization-Token-Type': 'PROGRAMMATIC_ACCESS_TOKEN',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {SNOWFLAKE_PAT}'
  }

  try:
    request_id = str(uuid.uuid4())  # Generate unique requestId each time
    conn.request("POST", f"/api/v2/statements?requestId={request_id}&async=false", payload, headers)
    res = conn.getresponse()

    outputs.log(res)
    response_data = json.loads(res.read())
    outputs.log(f"Data: {response_data['data']}")
    rows = response_data['data']

    if not rows:
      outputs.log("Query returned no rows")
      outputs.result = ""
    elif inputs.return_single_value:
      if len(rows) == 1 and len(rows[0]) == 1:
        single_value = next(iter(rows[0]))
        outputs.log(f"Single value result: {single_value}")
        outputs.result = str(single_value)
      else:
        raise ValueError("Expected a single value result, but the query returned multiple rows or columns.")
    else:
      outputs.log(f"Multiple values/rows returned: {len(rows)} rows")
      outputs.result = str(rows)
  except Exception as e:
    raise ValueError(f"Error while using Snowflake connection: {e}")

connect_to_snowflake()
