"""Fail-closed semantic alias review, not automatic DATA02 canonicalization."""
SIGNATURE_FIELDS = ('meaning', 'unit', 'currency', 'period_kind', 'period_start',
                    'period_end', 'entity_scope', 'entity_type', 'relationship_kind', 'event_kind')

def can_coalesce(left, right):
    """Equal names or amounts are insufficient evidence of semantic equality."""
    if any(field not in left or field not in right for field in SIGNATURE_FIELDS):
        return False
    if not left.get('meaning') or not left.get('period_kind') or not left.get('entity_scope'):
        return False
    return all(left[field] == right[field] for field in SIGNATURE_FIELDS)

def review_display_map(entries):
    seen=set();result=[]
    for entry in entries:
        key=entry['delivered_key'];canonical=entry['canonical_key']
        if key in seen:raise ValueError('Duplicate delivered key')
        seen.add(key)
        unsafe = ((key=='acquired_hospitals' and canonical=='subsidiaries') or
                  (key in ('subsidiaries','joint_ventures','associates') and canonical!=key))
        decision='REJECT' if unsafe else ('ACCEPT' if key==canonical else 'REVIEW')
        result.append(dict(delivered_key=key,proposed_canonical_key=canonical,
            retained_identity=key,decision=decision,
            reason=('Different legal/accounting concepts cannot be collapsed' if unsafe else
                    'Identity mapping only; no alias or row merge' if key==canonical else
                    'Missing record-level meaning/unit/period/scope signature; grouping may be UI-only'),
            row_coalescing_allowed=False,production_applied=False))
    return result
