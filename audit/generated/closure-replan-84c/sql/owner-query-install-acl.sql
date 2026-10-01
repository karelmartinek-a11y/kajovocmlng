-- Execute after operation-helper-owner-query.sql and exact operation-functions.sql,
-- in the SAME privileged installation transaction before granting any dispatcher.
-- This package provides no runtime service grant and activates no public handler.
REVOKE ALL ON FUNCTION public.kcml_op_e2102887249da0cf3e17_v1(public.kcml_operation_context_v1) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.kcml_op_876669c0a0a51c444e5b_v1(public.kcml_operation_context_v1) FROM PUBLIC;
