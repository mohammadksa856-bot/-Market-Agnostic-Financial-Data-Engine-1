"""Consumed operands and guarded replay for deterministic canonical projections.

Replay proves the governed transformation and reconciliation arithmetic. It
does not independently certify the original issuer values.
"""
from dataclasses import fields
from decimal import Decimal
from .models import Fact, PeriodKind


def descriptor(fact):
    row = {field.name: getattr(fact, field.name) for field in fields(Fact)}
    row['value'] = str(fact.value)
    row['quality_score'] = str(fact.quality_score)
    row['period_kind'] = fact.period_kind.value
    row['dimensions'] = dict(fact.dimensions)
    return row


def fact_from_descriptor(row, value=None):
    row = dict(row)
    row['value'] = Decimal(row['value'] if value is None else value)
    row['quality_score'] = Decimal(row['quality_score'])
    row['period_kind'] = PeriodKind(row['period_kind'])
    return Fact(**row)


def projection_trace(output, inputs):
    from .calculation_lineage import trace
    inputs = tuple(inputs)
    return trace(output, inputs, 'canonical_projection', {
        'projection_revision': 'canonical-projector/1',
        'target': descriptor(output),
        'input_descriptors': [descriptor(fact) for fact in inputs],
    })


def _replay(inputs, parameters):
    from .canonicalization import CanonicalProjector
    if parameters.get('projection_revision') != 'canonical-projector/1':
        raise ValueError('unsupported canonical projection revision')
    target = parameters['target']
    matches = [fact for fact in CanonicalProjector().project(inputs)
               if (fact.metric, fact.period_end, fact.period_kind.value, fact.scope, fact.dimensions) ==
                  (target['metric'], target['period_end'], target['period_kind'], target['scope'], target['dimensions'])]
    if len(matches) != 1:
        raise ValueError('canonical projection guard failed or target ambiguous')
    return matches[0]


def validate_projection(output, inputs, parameters):
    if [descriptor(fact) for fact in inputs] != parameters.get('input_descriptors'):
        raise ValueError('canonical projection operands differ from consumed descriptors')
    if descriptor(output) != parameters.get('target'):
        raise ValueError('canonical projection output binding mismatch')
    if descriptor(_replay(inputs, parameters)) != descriptor(output):
        raise ValueError('canonical projection does not match governed transformation')


def reproduce_projection(values, parameters):
    descriptors = parameters['input_descriptors']
    if len(values) != len(descriptors):
        raise ValueError('canonical projection input count mismatch')
    inputs = [fact_from_descriptor(row, value) for row, value in zip(descriptors, values)]
    return _replay(inputs, parameters).value
