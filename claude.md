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