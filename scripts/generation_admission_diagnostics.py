"""Exact finite current-source admission diagnostic projection."""
import hashlib,json
from functools import lru_cache
from ssot_sources import SSOT,resource_index,resources
@lru_cache(maxsize=2)
def _codes(raw):
 rows=json.loads(resource_index(resources(raw.decode()))["contracts/generation/admission-diagnostics.json"]["raw"])["diagnostics"]
 result={r["diagnostic"]:r["stableCode"] for r in rows}
 if len(result)!=len(rows):raise ValueError("DUPLICATE_ADMISSION_DIAGNOSTIC")
 return result
def codes():return _codes(SSOT.read_bytes())
