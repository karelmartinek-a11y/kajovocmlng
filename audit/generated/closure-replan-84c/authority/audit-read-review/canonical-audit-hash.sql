CREATE FUNCTION kcml_audit_hash_v1(format integer, previous bytea, sequence bigint, canonical bytea)
 RETURNS bytea LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog AS $$
BEGIN
 IF format IS DISTINCT FROM 1 OR previous IS NULL OR octet_length(previous)<>32
 OR sequence IS NULL OR sequence<1 OR canonical IS NULL THEN
 RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='AUDIT_HASH_INPUT_INVALID';
 END IF;
 RETURN sha256(convert_to('KCML-AUDIT-CHAIN','UTF8')||int4send(format)||previous||int8send(sequence)||int8send(octet_length(canonical)::bigint)||canonical);
END; $$;
