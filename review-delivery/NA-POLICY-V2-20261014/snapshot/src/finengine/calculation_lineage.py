"""Exact consumed-input evidence for explicitly instrumented formula families.

Unsupported formulas retain a diagnostic record, never a verified-lineage claim.
This module does not initialize or migrate a production connection implicitly.
"""
from dataclasses import dataclass, fields, field
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json

from .models import Fact

REVISION = "consumed-inputs-v1"
SCHEMA = """
CREATE TABLE IF NOT EXISTS calculation_lineage(
 output_id INTEGER PRIMARY KEY REFERENCES data_points(id),
 formula_revision TEXT NOT NULL, formula_text TEXT NOT NULL,
 operation TEXT NOT NULL, status TEXT NOT NULL,
 evidence_json TEXT NOT NULL, evidence_sha256 TEXT NOT NULL,
 parameters_json TEXT NOT NULL, output_snapshot_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS calculation_input_edges(
 output_id INTEGER NOT NULL REFERENCES data_points(id),
 input_id INTEGER NOT NULL REFERENCES data_points(id),
 input_version INTEGER NOT NULL, ordinal INTEGER NOT NULL,
 PRIMARY KEY(output_id,ordinal));
CREATE INDEX IF NOT EXISTS calculation_input_dependents ON calculation_input_edges(input_id);
CREATE TABLE IF NOT EXISTS calculation_legacy_outputs(
 output_id INTEGER PRIMARY KEY REFERENCES data_points(id),
 observation_id INTEGER NOT NULL UNIQUE REFERENCES observations(id));
CREATE TRIGGER IF NOT EXISTS retire_calculation_dependents
AFTER UPDATE OF is_current ON data_points
WHEN OLD.is_current=1 AND NEW.is_current=0
BEGIN
 UPDATE data_points SET is_current=0 WHERE id IN (
  WITH RECURSIVE dependents(id) AS (
   SELECT output_id FROM calculation_input_edges WHERE input_id=OLD.id
   UNION SELECT e.output_id FROM calculation_input_edges e JOIN dependents d ON e.input_id=d.id
  ) SELECT id FROM dependents);
 UPDATE observations SET is_current=0 WHERE id IN (
  SELECT l.observation_id FROM calculation_legacy_outputs l JOIN data_points d ON d.id=l.output_id
  WHERE d.is_current=0);
END;
"""

@dataclass(frozen=True)
class BoundFact(Fact):
    consumed_data_point_id: int | None = None
    consumed_data_point_version: int | None = None

@dataclass(frozen=True)
class TracedFact(Fact):
    consumed_inputs: tuple[Fact, ...] = ()
    lineage_operation: str = ""
    lineage_parameters: dict = field(default_factory=dict)

def trace(output, inputs, operation, parameters=None):
    return TracedFact(**{f.name: getattr(output, f.name) for f in fields(Fact)},
                      consumed_inputs=tuple(inputs), lineage_operation=operation,
                      lineage_parameters=dict(parameters or {}))

def reproduce(operation, values, parameters=None):
    if operation == "derived_quarter":
        if len(values) not in (1, 2):
            raise ValueError("invalid quarter operands")
        return values[0] if len(values) == 1 else values[0] - values[1]
    if operation=="canonical_projection":
        from .projection_lineage import reproduce_projection
        return reproduce_projection(values,parameters)
    if operation=="composite_replay":
        from .calculations import Calculator
        from .models import PeriodKind
        from types import SimpleNamespace
        lookup={}; historical={}; year=parameters["year"]
        for alias,value in zip(parameters["aliases"],values):
            period,metric=alias.split(".",1)
            item=SimpleNamespace(value=value)
            if period=="now":
                lookup[metric]=item
            else:
                kind=PeriodKind.INSTANT if period.endswith("instant") else PeriodKind.FY
                offset=2 if period.startswith("prior2") else 1
                historical.setdefault(("replay",year-offset,kind),{})[metric]=item
        results={}
        Calculator()._composite_scores("replay",SimpleNamespace(fiscal_year=year),lookup,historical,
                                      lambda metric,value,*args,**kw: results.setdefault(metric,value))
        if parameters["metric"] not in results:
            raise ValueError("composite inputs do not reproduce a result")
        return results[parameters["metric"]]
    if operation=="weighted_arithmetic":
        numerator=sum((value*Decimal(weight) for value,weight in zip(values,parameters["numerator_weights"])),Decimal(0))
        if "denominator_weights" in parameters:
            denominator=sum((value*Decimal(weight) for value,weight in zip(values,parameters["denominator_weights"])),Decimal(0))
            numerator/=denominator
        return numerator+Decimal(parameters.get("result_offset","0"))
    if operation == "ratio":
        return values[0] / values[1]
    if operation == "absolute_ratio":
        return abs(values[0] / values[1])
    if operation == "free_cash_flow":
        return values[0] - abs(values[1])
    if operation == "identity":
        return values[0]
    if operation == "add_absolute_second":
        return values[0] + abs(values[1])
    if operation == "sum_absolute":
        return sum((abs(value) for value in values),Decimal(0))
    if operation == "absolute_numerator_ratio":
        return abs(values[0]) / values[1]
    if operation == "quick_ratio":
        return sum(values[:-1],Decimal(0)) / values[-1]
    if operation == "sum_numerator_ratio":
        return sum(values[:-1],Decimal(0)) / values[-1]
    if operation == "growth":
        return values[0]/values[1]-1
    if operation == "cagr":
        return (values[0]/values[1]) ** (Decimal(1)/Decimal(parameters["years"]))-1
    if operation == "ttm_sum":
        return sum(values,Decimal(0))
    if operation == "q1_identity":
        return values[0]
    if operation in {"average_ratio","absolute_average_ratio","average_days","average_sum_ratio"}:
        average=sum(values[1:],Decimal(0))/Decimal(2)
        if operation=="average_days":
            return average/values[0]*Decimal(365)
        return (abs(values[0]) if operation=="absolute_average_ratio" else values[0])/average
    raise ValueError("unsupported lineage operation")

def validate_periods(fact, inputs, operation, parameters):
    if operation == "derived_quarter":
        from .derived_periods import validate_derived_quarter
        validate_derived_quarter(fact, inputs, parameters)
        return
    if operation=="canonical_projection":
        from .projection_lineage import validate_projection
        validate_projection(fact,inputs,parameters)
        return
    share_metrics={"shares_outstanding","weighted_average_shares_basic","weighted_average_shares_diluted"}
    monetary=[item for item in inputs if item.currency and not (item.metric in share_metrics and item.unit in {"shares","share"})]
    if monetary and any((item.currency,item.unit)!=(monetary[0].currency,monetary[0].unit) for item in monetary):
        raise ValueError("calculation input currency/unit mismatch")
    for item in inputs:
        if (item.company_id,item.scope,item.dimensions) != (fact.company_id,fact.scope,fact.dimensions):
            raise ValueError("calculation input company/scope mismatch")
    if operation=="composite_replay":
        aliases=parameters["aliases"]
        if len(aliases)!=len(inputs) or len(set(aliases))!=len(aliases) or parameters["year"]!=fact.fiscal_year or parameters["metric"]!=fact.metric:
            raise ValueError("composite input aliases mismatch")
        for alias,item in zip(aliases,inputs):
            role,metric=alias.split(".",1)
            offset=0 if role=="now" else 2 if role.startswith("prior2") else 1
            if metric!=item.metric or fact.fiscal_year-item.fiscal_year!=offset or item.period_kind.value not in {"instant","fy"}:
                raise ValueError("composite input period mismatch")
            days=(date.fromisoformat(fact.period_end)-date.fromisoformat(item.period_end)).days
            if offset==0 and days!=0 or offset and not offset*350<=days<=offset*371:
                raise ValueError("composite historical interval mismatch")
        return
    if operation=="weighted_arithmetic":
        if len(parameters["numerator_weights"])!=len(inputs) or ("denominator_weights" in parameters and len(parameters["denominator_weights"])!=len(inputs)):
            raise ValueError("weighted operand count mismatch")
        offsets=parameters.get("year_offsets",[0]*len(inputs))
        if len(offsets)!=len(inputs):
            raise ValueError("weighted operand period count mismatch")
        for item,offset in zip(inputs,offsets):
            if fact.fiscal_year-item.fiscal_year!=offset:
                raise ValueError("weighted operand fiscal year mismatch")
            days=(date.fromisoformat(fact.period_end)-date.fromisoformat(item.period_end)).days
            if offset==0 and days!=0 or offset and not offset*350<=days<=offset*371:
                raise ValueError("weighted operand historical interval mismatch")
            if item.period_kind.value!="instant" and (item.period_kind!=fact.period_kind or (offset==0 and item.period_start!=fact.period_start)):
                raise ValueError("weighted operand duration mismatch")
        return
    if operation in {"growth","cagr"}:
        if len(inputs)!=2:
            raise ValueError("growth input count mismatch")
        current,prior=inputs
        years=1 if operation=="growth" else parameters["years"]
        if (current.period_end,current.fiscal_year,current.period_kind,current.period_start) != (fact.period_end,fact.fiscal_year,fact.period_kind,fact.period_start):
            raise ValueError("growth output period mismatch")
        if (current.metric,current.unit,current.currency,current.period_kind) != (prior.metric,prior.unit,prior.currency,prior.period_kind) or current.fiscal_year-prior.fiscal_year!=years:
            raise ValueError("growth input period mismatch")
        days=(date.fromisoformat(current.period_end)-date.fromisoformat(prior.period_end)).days
        if not years*350<=days<=years*371:
            raise ValueError("growth input historical interval mismatch")
        return
    if operation in {"average_ratio","absolute_average_ratio","average_days","average_sum_ratio"}:
        numerator=inputs[0]
        stocks=inputs[1:]
        if (numerator.period_start,numerator.period_end,numerator.fiscal_year,numerator.period_kind)!=(fact.period_start,fact.period_end,fact.fiscal_year,fact.period_kind) or len(stocks)%2:
            raise ValueError("average calculation period/count mismatch")
        half=len(stocks)//2
        for current,prior in zip(stocks[:half],stocks[half:]):
            if (current.period_kind.value,prior.period_kind.value)!=("instant","instant") or current.metric!=prior.metric or current.period_end!=fact.period_end or current.fiscal_year!=fact.fiscal_year or prior.fiscal_year!=fact.fiscal_year-1:
                raise ValueError("average calculation stock period mismatch")
            days=(date.fromisoformat(current.period_end)-date.fromisoformat(prior.period_end)).days
            if not 350<=days<=371:
                raise ValueError("average historical interval mismatch")
        return
    if operation == "ttm_sum":
        if len(inputs)!=4 or fact.period_kind.value!="ttm":
            raise ValueError("TTM input count/kind mismatch")
        spans=[]
        for item in inputs:
            if item.period_kind.value!="quarter" or (item.unit,item.currency,item.metric)!=(fact.unit,fact.currency,inputs[0].metric):
                raise ValueError("TTM input unit/metric/kind mismatch")
            start,end=date.fromisoformat(item.period_start),date.fromisoformat(item.period_end)
            if not 80<=(end-start).days+1<=100:
                raise ValueError("TTM input duration mismatch")
            spans.append((start,end))
        if any(spans[i][0]!=spans[i-1][1]+timedelta(days=1) for i in range(1,4)) or not 350<=(spans[-1][1]-spans[0][0]).days+1<=371:
            raise ValueError("TTM input gap/overlap mismatch")
        if (fact.period_start,fact.period_end,fact.fiscal_year,fact.fiscal_quarter)!=(inputs[0].period_start,inputs[-1].period_end,inputs[-1].fiscal_year,inputs[-1].fiscal_quarter):
            raise ValueError("TTM output period mismatch")
        return
    if operation == "q1_identity":
        item=inputs[0]
        if (item.period_kind.value,fact.period_kind.value,item.fiscal_quarter,fact.fiscal_quarter)!=("ytd","quarter",1,1) or (item.period_start,item.period_end,item.fiscal_year)!=(fact.period_start,fact.period_end,fact.fiscal_year):
            raise ValueError("Q1 period mismatch")
        if not 80<=(date.fromisoformat(item.period_end)-date.fromisoformat(item.period_start)).days+1<=100:
            raise ValueError("Q1 duration mismatch")
        return
    for item in inputs:
        if (item.period_end,item.fiscal_year,item.fiscal_quarter)!=(fact.period_end,fact.fiscal_year,fact.fiscal_quarter):
            raise ValueError("calculation input period mismatch")
        reported_year_end_point=(item.period_kind.value=="as_of" and item.metric=="market_cap" and item.period_start is None and fact.period_kind.value in {"fy","instant","as_of"})
        if item.period_kind.value!="instant" and not reported_year_end_point and (item.period_kind,item.period_start)!=(fact.period_kind,fact.period_start):
            raise ValueError("calculation input duration mismatch")

def snapshot(row):
    return {key:row[key] for key in row.keys() if key!="is_current"}

def seal(payload, parameters, output, operation, formula, revision):
    return hashlib.sha256(json.dumps([payload,parameters,output,operation,formula,revision],sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def persist(conn, output_id, fact):
    if hasattr(fact,"market_expression"):
        from .market_input_lineage import persist_market
        return persist_market(conn,output_id,fact)
    inputs = getattr(fact, "consumed_inputs", ())
    operation = getattr(fact, "lineage_operation", "")
    parameters = getattr(fact,"lineage_parameters",{})
    evidence = []
    status = "reproduced" if inputs else "unsupported_formula_inputs_not_captured"
    if inputs:
        validate_periods(fact,inputs,operation,parameters)
        for ordinal, item in enumerate(inputs):
            rows = conn.execute("""SELECT * FROM data_points WHERE company_id=? AND metric_key=?
             AND value_decimal=? AND source_key=? AND period_start=? AND period_end=?
             AND period_kind=? AND fiscal_year=? AND fiscal_quarter=? AND scope=?
             AND currency=? AND unit=? AND dimensions_json=? AND source_url=? AND filed_at=?
             AND metric_version=? AND is_calculated=? AND is_current=1""",
             (item.company_id,item.metric,str(item.value),item.source_key,item.period_start or "",
              item.period_end,item.period_kind.value,item.fiscal_year,item.fiscal_quarter or 0,
              item.scope,item.currency,item.unit,json.dumps(item.dimensions,ensure_ascii=False,sort_keys=True,separators=(",",":")),
              item.source_url,item.filed_at,item.metric_version,int(item.is_calculated))).fetchall()
            if len(rows) != 1:
                raise ValueError("calculation input missing, ambiguous or retired")
            row = rows[0]
            bound_id=getattr(item,"consumed_data_point_id",None)
            bound_version=getattr(item,"consumed_data_point_version",None)
            if bound_id is not None and (row["id"],row["version"])!=(bound_id,bound_version):
                raise ValueError("calculation input consumed version no longer current")
            if item.is_calculated:
                parent = conn.execute("SELECT status FROM calculation_lineage WHERE output_id=?", (row["id"],)).fetchone()
                if not parent or parent[0] != "reproduced":
                    status = "unsupported_dependency_inputs_not_captured"
                elif not verify(conn,row["id"]):
                    raise ValueError("calculation input parent lineage is invalid")
            evidence.append(snapshot(row))
            conn.execute("INSERT INTO calculation_input_edges VALUES(?,?,?,?)",
                         (output_id,row["id"],row["version"],ordinal))
        if reproduce(operation, [Decimal(e["value_decimal"]) for e in evidence],parameters) != fact.value:
            raise ValueError("calculation result does not reproduce")
    payload = json.dumps(evidence, sort_keys=True, separators=(",",":"))
    params=json.dumps(parameters,sort_keys=True,separators=(",",":"))
    output=json.dumps(snapshot(conn.execute("SELECT * FROM data_points WHERE id=?",(output_id,)).fetchone()),sort_keys=True,separators=(",",":"))
    conn.execute("INSERT INTO calculation_lineage VALUES(?,?,?,?,?,?,?,?,?)",
                 (output_id,REVISION,fact.calculation or "",operation,
                  status,
                  payload,seal(payload,params,output,operation,fact.calculation or "",REVISION),params,output))

def verify(conn, output_id, historical=False, _visiting=None):
    try:
        return _verify(conn,output_id,historical,_visiting)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError):
        return False

def _verify(conn, output_id, historical=False, _visiting=None):
    visiting = set(_visiting or ())
    if output_id in visiting:
        return False
    visiting.add(output_id)
    record = conn.execute("SELECT * FROM calculation_lineage WHERE output_id=?", (output_id,)).fetchone()
    if record is not None and record["operation"]=="market_expression":
        from .market_input_lineage import verify_market
        return verify_market(conn,output_id,historical=historical,_visiting=visiting)
    if not record or record["status"] != "reproduced" or record["formula_revision"] != REVISION:
        return False
    payload = record["evidence_json"]
    if seal(payload,record["parameters_json"],record["output_snapshot_json"],record["operation"],record["formula_text"],record["formula_revision"]) != record["evidence_sha256"]:
        return False
    evidence = json.loads(payload)
    edges = conn.execute("SELECT input_id,input_version FROM calculation_input_edges WHERE output_id=? ORDER BY ordinal", (output_id,)).fetchall()
    if [(e["id"],e["version"]) for e in evidence] != [(r[0],r[1]) for r in edges]:
        return False
    for item in evidence:
        row = conn.execute("SELECT * FROM data_points WHERE id=?", (item["id"],)).fetchone()
        if row is None or any(row[key] != value for key,value in item.items()) or (not historical and not row["is_current"]):
            return False
        if row["is_calculated"] and not verify(conn,row["id"],historical=historical,_visiting=visiting):
            return False
    result = conn.execute("SELECT * FROM data_points WHERE id=?", (output_id,)).fetchone()
    return (result is not None and result["calculation"] == record["formula_text"]
            and (historical or bool(result["is_current"]))
            and snapshot(result)==json.loads(record["output_snapshot_json"])
            and reproduce(record["operation"], [Decimal(e["value_decimal"]) for e in evidence],json.loads(record["parameters_json"])) == Decimal(result["value_decimal"]))
