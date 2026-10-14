"""Server-side, read-only engine bridge; disabled flags retain legacy paths.

No Supabase client, writes, production flag mutation or secret-bearing browser URL.
"""
from dataclasses import dataclass
import json
import re
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from .api_contract import API_CONTRACT_VERSION,PAGE_PAYLOAD_VERSION

@dataclass(frozen=True)
class ConsumerFlags:
    site_engine: bool=False
    bot_engine: bool=False

def _safe(value):
    if isinstance(value,dict):return {k:_safe(v) for k,v in value.items() if k.lower() not in {'api_key','authorization','token','manifest_path','archived_path','local_path'}}
    if isinstance(value,list):return [_safe(v) for v in value]
    return value

class ServerSideEngineBridge:
    def __init__(self,origin,api_key,flags=None,*,opener=urlopen,allow_local_http=False):
        self.flags=flags or ConsumerFlags()
        if not origin and not api_key and not (self.flags.site_engine or self.flags.bot_engine):
            self._origin='';self._api_key='';self._opener=opener
            return
        parsed=urlsplit(origin)
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
            raise ValueError('Server origin only, no embedded credentials/path/query')
        if parsed.scheme!='https' and not (allow_local_http and parsed.scheme=='http' and parsed.hostname in {'localhost','127.0.0.1','::1'}):
            raise ValueError('TLS required except explicit localhost testing')
        if not parsed.hostname or not api_key:raise ValueError('Server origin and server-only API key required')
        self._origin=origin.rstrip('/');self._api_key=api_key;self._opener=opener
    def page(self,channel,market,symbol):
        if channel not in {'site','bot'}:raise ValueError('Unknown channel')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',market) or not re.fullmatch(r'[A-Za-z0-9._-]+',symbol):raise ValueError('Invalid company identity')
        enabled=self.flags.site_engine if channel=='site' else self.flags.bot_engine
        if not enabled:return {'state':'legacy_retained','enabled':False,'payload':None}
        request=Request(self._origin+'/v1/companies/'+market.upper()+'/'+symbol.upper()+'/page',headers={'X-API-Key':self._api_key})
        try:
            with self._opener(request,timeout=10) as response:
                if response.headers.get('X-Marefa-API-Contract')!=API_CONTRACT_VERSION:
                    return {'state':'unavailable','reason':'engine_contract_version_mismatch','payload':None}
                raw=response.read(3*1024*1024+1)
            if len(raw)>3*1024*1024:raise ValueError('Response exceeds local contract bound')
            payload=json.loads(raw)
            if payload.get('contract_version')!=PAGE_PAYLOAD_VERSION or payload.get('placeholder_policy')!='never_substitute_demo_values':
                return {'state':'unavailable','reason':'page_contract_version_mismatch','payload':None}
            if not {'company','sections','capabilities','data_quality'}<=set(payload):raise ValueError('Incomplete page')
            return {'state':'engine_response','enabled':True,'payload':_safe(payload)}
        except HTTPError as error:
            return {'state':'unavailable','reason':'engine_http_'+str(error.code),'payload':None}
        except (URLError,TimeoutError,OSError,ValueError,TypeError):
            return {'state':'unavailable','reason':'engine_response_unavailable','payload':None}

def bot_answer_adapter(bridge,legacy_answer):
    def answer(db_path,text):
        if not bridge.flags.bot_engine:return legacy_answer(db_path,text)
        parts=text.strip().split();command=parts[0].split('@',1)[0].lower() if parts else ''
        if command not in {'/topics','/fin','/missing','/sources'}:return legacy_answer(db_path,text)
        if len(parts) not in ((3,4) if command=='/fin' else (3,)):
            from product.bot import HELP
            return HELP
        result=bridge.page('bot',parts[1],parts[2])
        if result['state']!='engine_response':return 'تعذر الوصول إلى بيانات المحرك ('+result.get('reason','unknown')+').'
        from product.bot import answer_topics,answer_fin,answer_missing,answer_sources
        page=result['payload']
        if command=='/topics':return answer_topics(page)
        if command=='/missing':return answer_missing(page)
        if command=='/sources':return answer_sources(page)
        kind=parts[3].lower() if len(parts)==4 else 'fy'
        if kind not in {'fy','quarter','instant'}:return 'الفترة يجب أن تكون fy أو quarter أو instant.'
        return answer_fin(page,kind)
    return answer
