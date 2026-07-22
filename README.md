# Snowflake Connection

A Kizen plugin that connects an Agentic Workflow to an external Snowflake database for real-time data lookups. It talks to Snowflake over the SQL REST API v2 and authenticates with a Programmatic Access Token (PAT).

The plugin ships two automation steps:

- **Read Data** (`snowflake_read`) runs read-only queries. A pre-flight check rejects anything that isn't a `SELECT`, so a workflow can't write by accident.
- **Write Data** (`snowflake_write`) runs `INSERT`, `UPDATE`, `DELETE`, and other DML/DDL. There is no guardrail, so validate any query built from user input before it runs.

## Setup

Both steps read a secret named `snowflake_connection`. Its value must be valid JSON.

For a single environment, use a flat object:

```json
{
  "warehouse": "COMPUTE_WH",
  "schema": "PUBLIC",
  "account": "myorg-account123",
  "pat": "ver:1-hint:abc123..."
}
```

For multiple environments, nest each one under its own key:

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
  }
}
```

With a nested secret, set the `Connection Secret Tag` input to the key you want (for example `production_db`).

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| Database | string | yes | Snowflake database to query |
| Query | string | yes | SQL statement to run |
| Return Single Value | boolean | yes | Expect a single cell and return it as a string. Fails if the result isn't exactly one row and one column. |
| Connection Secret Tag | string | no | Key to pick an environment from a nested connection secret |

## Outputs

| Output | Type | Step | Description |
|--------|------|------|-------------|
| Result | string | both | Query results. A single value, or the string form of the rows for a multi-row result. |
| Result Status | string | write only | Summary of what happened: the DML row counts when Snowflake returns stats, otherwise a row-count description. |

## Good to know

- Results come back as strings. Parse JSON or numeric types downstream if you need them.
- Queries block until they finish or hit the 30 second timeout. Long-running queries will time out.
- Only the first page of results is returned. Add a `LIMIT` for large result sets.
- Queries aren't parameterized. Build SQL from external input carefully to avoid injection.
