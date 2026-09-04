from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .query import FinancialQueryService


def create_api_server(db_path: str, host: str = "127.0.0.1", port: int = 8000,
                      api_key: str | None = None) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        server_version = "FinEngineAPI/1.4"

        def _send(self, status: int, payload: dict | list):
            body=json.dumps(payload,ensure_ascii=False,default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.end_headers(); self.wfile.write(body)

        def _authorized(self) -> bool:
            if not api_key:
                return True
            bearer=self.headers.get("Authorization","")
            return self.headers.get("X-API-Key") == api_key or bearer == f"Bearer {api_key}"

        @staticmethod
        def _int(params, name, default):
            try: return int(params.get(name,[default])[0])
            except (TypeError,ValueError): raise ValueError(f"{name} must be an integer")

        def do_GET(self):
            if not self._authorized():
                self._send(401,{"error":"unauthorized"}); return
            parsed=urlparse(self.path); parts=[part for part in parsed.path.split("/") if part]
            params=parse_qs(parsed.query)
            query=FinancialQueryService(db_path)
            try:
                if parts == ["health"]:
                    result=query.health()
                elif len(parts)>=4 and parts[:2]==["v1","companies"]:
                    market,symbol=parts[2],parts[3]
                    tail=parts[4:]
                    if not tail: result=query.company_overview(market,symbol)
                    elif tail==["dossier"]: result=query.company_dossier(market,symbol)
                    elif tail==["facts"]:
                        result=query.facts(market,symbol,params.get("category",[None])[0],
                            params.get("period_kind",[None])[0],self._int(params,"limit",500),
                            self._int(params,"offset",0))
                    elif tail==["snapshot"]:
                        result=query.snapshot(market,symbol,params.get("period_end",[None])[0])
                    elif len(tail)==2 and tail[0]=="metrics":
                        result=query.metric_history(market,symbol,tail[1],self._int(params,"limit",20))
                    elif tail==["coverage"]: result=query.coverage(market,symbol,self._int(params,"limit",100))
                    elif tail==["completeness"]: result=query.completeness(market,symbol)
                    elif tail==["backlog"]: result=query.backlog(market,symbol,params.get("status",["active"])[0],self._int(params,"limit",500))
                    elif tail==["disclosures"]: result=query.disclosures(market,symbol,params.get("type",[None])[0],self._int(params,"limit",50))
                    elif tail==["attributes"]: result=query.attributes(market,symbol)
                    elif tail==["sources"]: result=query.source_candidates(market,symbol,params.get("status",[None])[0],self._int(params,"limit",100))
                    elif tail==["prices"]: result=query.market_prices(market,symbol,params.get("interval",["1d"])[0],self._int(params,"limit",100))
                    elif tail==["ownership"]: result=query.ownership(market,symbol,params.get("as_of",[None])[0],self._int(params,"limit",100))
                    elif tail==["estimates"]: result=query.consensus_estimates(market,symbol,params.get("metric",[None])[0],params.get("period_end",[None])[0],self._int(params,"limit",100))
                    elif tail==["actions"]: result=query.corporate_actions(market,symbol,params.get("type",[None])[0],self._int(params,"limit",100))
                    else: raise KeyError("unknown endpoint")
                elif parts == ["v1","exceptions"]:
                    result=query.exceptions(status=params.get("status",["open"])[0],limit=self._int(params,"limit",100))
                elif parts == ["v1","catalog"]:
                    result=query.data_catalog(params.get("category",[None])[0],params.get("domain",[None])[0],self._int(params,"limit",1000))
                else:
                    raise KeyError("unknown endpoint")
                self._send(200,result)
            except KeyError as error:
                self._send(404,{"error":str(error)})
            except ValueError as error:
                self._send(400,{"error":str(error)})
            except Exception:
                self._send(500,{"error":"internal_error"})
            finally:
                query.close()

        def do_HEAD(self):
            self.send_response(200); self.end_headers()

        def do_POST(self):
            self._send(405,{"error":"read_only_service"})

        def log_message(self, format, *args):
            return

    return ThreadingHTTPServer((host,port),Handler)


def serve_api(db_path: str, host: str = "127.0.0.1", port: int = 8000,
              api_key: str | None = None) -> None:
    server=create_api_server(db_path,host,port,api_key)
    try: server.serve_forever()
    finally: server.server_close()
