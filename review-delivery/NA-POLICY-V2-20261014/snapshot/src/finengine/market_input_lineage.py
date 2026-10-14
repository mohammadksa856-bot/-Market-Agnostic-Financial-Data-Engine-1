"""Consumed market-price and fundamental identities, without synthetic prices."""
from dataclasses import dataclass, fields
from decimal import Decimal
import json
import math
import statistics

from .models import Fact

MARKET_SCHEMA = """
CREATE TABLE IF NOT EXISTS calculation_market_input_edges(
 output_id INTEGER NOT NULL REFERENCES data_points(id),
 input_id INTEGER NOT NULL REFERENCES market_prices(id),
 input_version INTEGER NOT NULL, ordinal INTEGER NOT NULL,
 PRIMARY KEY(output_id,ordinal));
CREATE INDEX IF NOT EXISTS calculation_market_dependents ON calculation_market_input_edges(input_id);
CREATE TRIGGER IF NOT EXISTS retire_market_calculation_dependents
AFTER UPDATE OF is_current ON market_prices
WHEN OLD.is_current=1 AND NEW.is_current=0
BEGIN
 UPDATE data_points SET is_current=0 WHERE id IN (
  WITH RECURSIVE dependents(id) AS (
   SELECT output_id FROM calculation_market_input_edges WHERE input_id=OLD.id
   UNION SELECT e.output_id FROM calculation_input_edges e JOIN dependents d ON e.input_id=d.id
  ) SELECT id FROM dependents);
 UPDATE observations SET is_current=0 WHERE is_calculated=1 AND is_current=1
 AND id IN (SELECT l.observation_id FROM calculation_legacy_outputs l
 JOIN data_points d ON d.id=l.output_id WHERE d.is_current=0);
END;
"""

@dataclass(frozen=True)
class MarketTracedFact(Fact):
    market_evidence: tuple = ()
    market_expression: dict = None


class MarketExpressionBuilder:
    def __init__(self, conn):
        self.conn = conn
        self.evidence = []
        self.identities = {}

    def ref(self, row, domain, field):
        if domain not in {'market_prices', 'data_points'}:
            raise ValueError('unsupported market input domain')
        identity = (domain, row['id'], row['version'])
        if identity not in self.identities:
            stored = self.conn.execute(f'SELECT * FROM {domain} WHERE id=?', (row['id'],)).fetchone()
            if not stored or not stored['is_current'] or any(
                row[key] != stored[key] for key in stored.keys() if key in row.keys()
            ):
                raise ValueError('market input snapshot changed during consumption')
            self.identities[identity] = len(self.evidence)
            self.evidence.append({'domain': domain, 'snapshot': {
                key: stored[key] for key in stored.keys() if key != 'is_current'}})
        return {'ref': self.identities[identity], 'field': field}

    def trace(self, output, expression):
        # Capture only references this output actually consumed.
        used = set()
        def walk(node):
            if 'ref' in node:
                used.add(node['ref'])
            for arg in node.get('args', []):
                walk(arg)
        walk(expression)
        indexes = sorted(used)
        renumber = {old: new for new, old in enumerate(indexes)}
        def rebind(node):
            rebound = dict(node)
            if 'ref' in rebound:
                rebound['ref'] = renumber[rebound['ref']]
            if 'args' in rebound:
                rebound['args'] = [rebind(arg) for arg in rebound['args']]
            return rebound
        return MarketTracedFact(**{f.name:getattr(output,f.name) for f in fields(Fact)},
            market_evidence=tuple(self.evidence[index] for index in indexes),
            market_expression=rebind(expression))


def const(value):
    return {'const': str(value)}


def expression(operation, *args):
    return {'op': operation, 'args': list(args)}


def reproduce_market(evidence, tree):
    if 'const' in tree:
        return Decimal(tree['const'])
    if 'ref' in tree:
        item = evidence[tree['ref']]
        allowed = {'market_prices': {'close','high','low','volume','turnover'},
                   'data_points': {'value_decimal'}}
        if tree['field'] not in allowed[item['domain']]:
            raise ValueError('invalid market operand field')
        return Decimal(item['snapshot'][tree['field']])
    values = [reproduce_market(evidence,arg) for arg in tree['args']]
    op = tree['op']
    if op == 'add': return sum(values,Decimal(0))
    if op == 'subtract': return values[0]-values[1]
    if op == 'multiply': return values[0]*values[1]
    if op == 'divide': return values[0]/values[1]
    if op == 'abs': return abs(values[0])
    if op == 'sqrt': return values[0].sqrt()
    if op == 'mean': return sum(values,Decimal(0))/Decimal(len(values))
    if op == 'max': return max(values)
    if op == 'min': return min(values)
    if op == 'percentile': return Decimal(sum(value<=values[0] for value in values[1:]))/Decimal(len(values)-1)
    if op == 'volatility':
        closes=[float(value) for value in values]
        returns=[math.log(closes[i]/closes[i-1]) for i in range(1,len(closes))]
        return Decimal(str(statistics.stdev(returns)*math.sqrt(252)))
    raise ValueError('unsupported market expression operation')


def _validate_identity(conn, item, output, historical=False):
    domain=item['domain']; snapshot=item['snapshot']
    if domain not in {'data_points','market_prices'}:
        raise ValueError('invalid market input domain')
    row=conn.execute(f'SELECT * FROM {domain} WHERE id=?',(snapshot['id'],)).fetchone()
    if row is None or any(row[key]!=value for key,value in snapshot.items()) or (not historical and not row['is_current']):
        raise ValueError('market input retired or modified')
    if domain=='market_prices':
        issuer=conn.execute('SELECT s.company_id FROM listings l JOIN securities s USING(security_id) WHERE l.listing_id=?',(row['listing_id'],)).fetchone()
        if not issuer or issuer[0]!=output['company_id'] or row['observed_at'][:10]>output['period_end'][:10]:
            raise ValueError('market input company/as-of mismatch')
    else:
        from .normalization import per_share_contract_issues
        if per_share_contract_issues(row['metric_key'],row['unit'],row['currency']):
            raise ValueError('market_fundamental_unit_requires_review')
        if row['company_id']!=output['company_id'] or row['scope']!='consolidated' or row['dimensions_json']!='{}' or row['filed_at']>output['period_end'] or row['period_end']>output['period_end']:
            raise ValueError('fundamental input company/scope/as-of mismatch')
    return row


def persist_market(conn, output_id, fact):
    from .calculation_lineage import REVISION, snapshot, seal, verify
    output=conn.execute('SELECT * FROM data_points WHERE id=?',(output_id,)).fetchone()
    evidence=list(fact.market_evidence)
    if not evidence:
        raise ValueError('market expression has no consumed inputs')
    currencies=set()
    status='reproduced'
    for ordinal,item in enumerate(evidence):
        row=_validate_identity(conn,item,output)
        if row['currency']:
            currencies.add(row['currency'])
        if item['domain']=='data_points':
            if row['is_calculated'] and not verify(conn,row['id']):
                status='unsupported_dependency_inputs_not_captured'
            table='calculation_input_edges'
        else:
            table='calculation_market_input_edges'
        conn.execute(f'INSERT INTO {table} VALUES(?,?,?,?)',(output_id,row['id'],row['version'],ordinal))
    if len(currencies)>1 or (fact.currency and currencies and fact.currency not in currencies):
        raise ValueError('market calculation currency mismatch')
    if reproduce_market(evidence,fact.market_expression)!=fact.value:
        raise ValueError('market calculation result does not reproduce')
    payload=json.dumps(evidence,sort_keys=True,separators=(',',':'))
    params=json.dumps({'expression':fact.market_expression},sort_keys=True,separators=(',',':'))
    output_json=json.dumps(snapshot(output),sort_keys=True,separators=(',',':'))
    operation='market_expression'
    conn.execute('INSERT INTO calculation_lineage VALUES(?,?,?,?,?,?,?,?,?)',
        (output_id,REVISION,fact.calculation or '',operation,status,payload,
         seal(payload,params,output_json,operation,fact.calculation or '',REVISION),params,output_json))


def verify_market(conn, output_id, historical=False, _visiting=None):
    from .calculation_lineage import REVISION, snapshot, seal, verify
    record=conn.execute('SELECT * FROM calculation_lineage WHERE output_id=?',(output_id,)).fetchone()
    output=conn.execute('SELECT * FROM data_points WHERE id=?',(output_id,)).fetchone()
    if not record or not output or record['status']!='reproduced' or record['formula_revision']!=REVISION or (not historical and not output['is_current']):
        return False
    if snapshot(output)!=json.loads(record['output_snapshot_json']) or output['calculation']!=record['formula_text']:
        return False
    if seal(record['evidence_json'],record['parameters_json'],record['output_snapshot_json'],record['operation'],record['formula_text'],record['formula_revision'])!=record['evidence_sha256']:
        return False
    evidence=json.loads(record['evidence_json'])
    expected={'data_points':[],'market_prices':[]}
    visiting=set(_visiting or ())
    for ordinal,item in enumerate(evidence):
        row=_validate_identity(conn,item,output,historical)
        expected[item['domain']].append((row['id'],row['version'],ordinal))
        if item['domain']=='data_points' and row['is_calculated'] and not verify(conn,row['id'],historical=historical,_visiting=visiting):
            return False
    for domain,table in [('data_points','calculation_input_edges'),('market_prices','calculation_market_input_edges')]:
        actual=[tuple(row) for row in conn.execute(f'SELECT input_id,input_version,ordinal FROM {table} WHERE output_id=? ORDER BY ordinal',(output_id,))]
        if actual!=expected[domain]: return False
    return reproduce_market(evidence,json.loads(record['parameters_json'])['expression'])==Decimal(output['value_decimal'])
