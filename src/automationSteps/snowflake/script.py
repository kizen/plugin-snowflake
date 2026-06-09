import http.client
import json

BASE_URL = "/external-integrations/proxy/scott_f_dev/snowflake_staging_api"

payload = {
    "statement": "select seq8(), randstr(1000, random()) from table(generator(rowcount=>600))",
    "timeout": 1000,
    "database": "SNOWFLAKE_SAMPLE_DATA",
    "schema": "TPCDS_SF100TCL",
    "warehouse": "COMPUTE_WH",
    "bindings": {},
    "parameters": {},
    "role": "PUBLIC",
}

outputs.log(f"{BASE_URL}/api/v2/statements?async=false")

res = kizen.api.post(f"{BASE_URL}/api/v2/statements?async=false", json=payload)

outputs.log(res.json())
