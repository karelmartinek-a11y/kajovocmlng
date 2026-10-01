-- Technical SQL projection of SSOT51.8 PostgresAdvisoryKey.
-- Input is the full32-byte SHA-256 digest of canonical key bytes. This routine
-- never establishes caller authority, row identity, scope, or uniqueness.
-- Namespace1000 uses literal key0; it must not call this hashed-key routine.
CREATE OR REPLACE FUNCTION kcml_postgres_advisory_key_v1(p_digest bytea)
RETURNS integer
LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE
SET search_path = pg_catalog
AS $$
DECLARE
  v_unsigned bigint;
BEGIN
  IF p_digest IS NULL OR octet_length(p_digest) <> 32 THEN
    RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'ADVISORY_KEY_REQUIRES_SHA256_DIGEST';
  END IF;
  v_unsigned := get_byte(p_digest,0)::bigint * 16777216
              + get_byte(p_digest,1)::bigint * 65536
              + get_byte(p_digest,2)::bigint * 256
              + get_byte(p_digest,3)::bigint;
  RETURN CASE WHEN v_unsigned >= 2147483648
              THEN (v_unsigned - 4294967296)::integer
              ELSE v_unsigned::integer END;
END;
$$;
