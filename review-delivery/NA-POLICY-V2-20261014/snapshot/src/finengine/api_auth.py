"""Fail-closed API startup policy shared by direct factory and CLI callers."""
import ipaddress
import os

def validate_api_auth(db_path, host, api_key=None, auth_mode=None):
    """Return the effective key and mode before opening sockets or writer state."""
    mode=auth_mode or os.environ.get('FINENGINE_API_AUTH_MODE','required')
    environment=os.environ.get('FINENGINE_ENVIRONMENT','local').strip().lower()
    if environment not in {'local','development','test','staging','production'}:
        raise ValueError('FINENGINE_ENVIRONMENT must name a supported deployment environment')
    if mode not in {'required','development-open'}:
        raise ValueError('API auth mode must be required or development-open')
    try:
        loopback=ipaddress.ip_address(host).is_loopback
    except ValueError:
        # A hostname may resolve elsewhere; only literal loopback is eligible.
        loopback=False
    path=str(db_path).replace('\\','/').lower()
    deployed=(environment in {'staging','production'} or path.startswith('/app/state/')
              or path.startswith('/var/lib/financial-data-engine/'))
    key=api_key if api_key is not None else os.environ.get('FINENGINE_API_KEY')
    if mode=='development-open':
        if deployed or not loopback:
            raise ValueError('Development-open API is limited to explicit local loopback use')
        if key:
            raise ValueError('Development-open mode and an API key are contradictory')
        return None,mode
    if not isinstance(key,str) or not key or any(ch.isspace() for ch in key):
        raise ValueError('API authentication requires an explicitly configured nonblank key')
    if (deployed or not loopback) and len(key)<32:
        raise ValueError('Deployed or exposed API keys must contain at least 32 characters')
    if key in {'replace-with-a-long-random-secret','change-me','changeme'}:
        raise ValueError('Example API keys cannot authenticate an API deployment')
    return key,mode
