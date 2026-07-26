-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Row-level security helper: set tenant context for the current session
CREATE OR REPLACE FUNCTION set_tenant_id(p_tenant_id TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.tenant_id', p_tenant_id, TRUE);
END;
$$ LANGUAGE plpgsql;

-- All DDL is managed by Alembic migrations in services/agent-api/migrations/
-- This init only installs extensions and the RLS helper.
