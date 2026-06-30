import http.client
import json
import uuid

# PAT config
# SNOWFLAKE_ACCOUNT = "yhjtexo-kv44817"  # host without .snowflakecomputing.com
# SNOWFLAKE_PAT = "eyJraWQiOiI0MDk5NjA2NDEzNjU2MDcwIiwiYWxnIjoiRVMyNTYifQ.eyJwIjoiMjQ0MzU1NTg4OjYyNTU1MDI5NzY1IiwiaXNzIjoiU0Y6MTAxNiIsImV4cCI6MTc4ODgwMDg1OH0.fc9xJVwZLLmN76D_ewx51O_iWtXAg-o6kCeUSmay5XY2R4W6QGt1FwWw99orvmYG61i335Cr6UEfz8tR4K_ylA"  # Your PAT from ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN

outputs.log(f'Secret: {secrets}')
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

# Now actually use it - pick which env you want
conn_data = {}
if inputs.connection_secret_tag:
  if inputs.connection_secret_tag not in SNOWFLAKE_CONNECTION:
      raise ValueError(f"Connection secret tag {inputs.connection_secret_tag} not found in SNOWFLAKE_CONNECTION")
  conn_data = SNOWFLAKE_CONNECTION[inputs.connection_secret_tag]
else:
  # If no connection secret tag is provided, SNOWFLAKE_CONNECTION isn't nested
  conn_data = SNOWFLAKE_CONNECTION

SNOWFLAKE_WAREHOUSE = conn_data['warehouse']
SNOWFLAKE_SCHEMA = conn_data['schema']
SNOWFLAKE_ACCOUNT = conn_data['account']
SNOWFLAKE_PAT = conn_data['pat']

INPUT_DATABASE = inputs.database
INPUT_QUERY = inputs.query

conn = http.client.HTTPSConnection(f"{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com")
payload = json.dumps({
  "statement": INPUT_QUERY,
  "timeout": 1000,
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

request_id = str(uuid.uuid4())  # Generate unique requestId each time
conn.request("POST", f"/api/v2/statements?requestId={request_id}&async=false", payload, headers)
res = conn.getresponse()

outputs.log(res)
response_data = json.loads(res.read())
outputs.log(f"Data: {response_data['data']}")
outputs.result = response_data['data']
