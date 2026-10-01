"""Native MCP's format=byte means RFC 4648 base64, not arbitrary text.
Source: exact pinned MCP Text/Audio/Image/BlobResourceContents descriptions.
No decode/re-encode normalization is performed; this is validation only.
"""
import base64,binascii
from jsonschema import FormatChecker

def is_byte(value):
    if not isinstance(value,str):return True # type keyword handles non-strings
    try:base64.b64decode(value.encode('ascii'),validate=True)
    except (ValueError,UnicodeEncodeError,binascii.Error):return False
    return True

def install_native_byte_checker():
    # Inventory checks both the class's available names and new instances.
    # Preserve a supported existing checker and verify its required semantics.
    if 'byte' not in FormatChecker.checkers:
        FormatChecker.checkers['byte']=(is_byte,())
    checker=FormatChecker()
    for value,expected in [('',True),('AAE=',True),('YWJj',True),('%%%',False),('a',False),('AA E=',False),('ž',False)]:
        if checker.conforms(value,'byte')!=expected:raise ValueError('NATIVE_BYTE_CHECKER_SEMANTICS_MISMATCH')
    return checker
