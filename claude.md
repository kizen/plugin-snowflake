# Snowflake Code Steps

This directory contains two Python code steps for interacting with Snowflake via the SQL REST API v2. Both use Programmatic Access Tokens (PAT) for auth.

## Files

### 1. `snowflake_get`
**Purpose**: Read-only queries against Snowflake. Returns query results as strings.

**Key Features**
- **Read-only guardrail**: Regex check blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, `COPY`, `CALL`, `DO`. Only `SELECT` queries should pass.
- **Smart quote normalization**: Converts curly quotes `“”‘’` to straight quotes before `json.loads()` to handle copy-paste from docs.
- **Multi-env support**: Reads `SNOWFLAKE_CONNECTION` secret. If `inputs.connection_secret_tag` is set, uses that nested key. Otherwise treats the secret as flat.
- **Single value mode**: Set `inputs.return_single_value = True` to extract one cell. Throws if query returns >1 row or >1 column.

### 2. `snowflake_send`  
**Purpose**: Write operations against Snowflake. Returns stats + results.

**Key Features**
- **No SQL guardrail**: Intentionally allows `INSERT`, `UPDATE`, `DELETE`, etc. Use with caution.
- **DML stats logging**: Logs `numRowsInserted`, `numRowsUpdated`, `numRowsDeleted` from response `stats` block on 200 status.
- **Same secret/env handling** as `snowflake_get`
- **Single value mode** also supported for write queries that return a value, e.g. `INSERT ... RETURNING id`

## Required Secrets

Both steps expect a secret with name ending in `snowflake_connection`. Value must be valid JSON.

**Flat structure:**
```json
{
  "warehouse": "COMPUTE_WH",
  "schema": "PUBLIC", 
  "account": "myorg-account123",
  "pat": "ver:1-hint:abc123..."
}

**Multi-env structure:**
```json
{
    "production_db": {
        "warehouse": "COMPUTE_WH",
        "schema": "PUBLIC", 
        "account": "myorg-account123",
        "pat": "ver:1-hint:abc123..."
    },
    "development_db": {
        "warehouse": "COMPUTE_WH",
        "schema": "PUBLIC", 
        "account": "myorg-account123",
        "pat": "ver:1-hint:abc123..."
    },
}

Use inputs.connection_secret_tag = "production_db" to select an env.

**Required Inputs**
Input	                Type	Description	                                    Used By
database	            string	Snowflake database to query	                    Both
query	                string	SQL statement to execute	                    Both
connection_secret_tag	string	Optional key for multi-env secrets	            Both
return_single_value	    bool	If true, expect 1x1 result and return as string	Both

**Outputs**
Output	    Type	Description
result	    string	Query results. Single value or str(rows) for multi-row
log	        string	Debug info: raw response, row counts, stats

**API Details**
- **Endpoint**: POST https://{account}.snowflakecomputing.com/api/v2/statements
- **Auth**: Authorization: Bearer {pat} + X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN
- **Params**: requestId={uuid} + async=false for sync execution
- **Timeout** 1000s hard-coded

**Usage Guidelines**
Do:
- Use snowflake_get for all read operations. The regex guardrail prevents accidental writes.
- Use snowflake_send for DML/DDL. Check outputs.log for numRowsInserted/Updated/Deleted.
- Set return_single_value=True for SELECT COUNT(*), SELECT MAX(id), etc.

Don't:
- Pass user-generated SQL directly to snowflake_send without validation. No guardrail exists.
- Use snowflake_get for writes - it will reject them pre-flight.
- Store the PAT anywhere except the secrets manager. Note: snowflake_send currently logs secrets - remove outputs.log(f'Secret: {secrets}') in prod.

**Error Handling**
Both steps raise ValueError on:
- Missing snowflake_connection secret
- Invalid JSON after smart-quote cleaning
- Missing connection_secret_tag key
- snowflake_get: Query starts with write keyword
- return_single_value=True but result isn't 1x1
- Any HTTP/API exception from Snowflake

**Limitations**
- No parameterized queries: bindings is always {}. Use string formatting carefully to avoid SQL injection.
- String results only: All data comes back as str(). Parse JSON/numeric types downstream if needed.
- No pagination: Returns first page only. For large result sets, add LIMIT or use Snowflake's resultSetMetaData + getResultUrl.
- Sync only: async=false. Long queries will block until 1000s timeout.
