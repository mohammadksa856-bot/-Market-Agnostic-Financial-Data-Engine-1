"""Reviewed, market-agnostic company peer sets.

Peer membership is classification evidence, not a claim that an issuer named the
other company as a competitor.  External peers can be represented before their
financial histories are onboarded; ``peer_company_id`` links only peers already
present in the engine and therefore eligible for quantitative comparison.
"""
from __future__ import annotations

import json


SAUDI_TELECOMS = {
    "sa:7010": ("Saudi Telecom Company (stc)", "https://www.stc.com/content/dam/stc/stc-annual-report-2025/"),
    "sa:7020": ("Etihad Etisalat Company (Mobily)", "https://mobily.com.sa/web/en/personal/about-mobily/investor-relations-details/annual-reports"),
    "sa:7030": ("Mobile Telecommunication Company Saudi Arabia (Zain KSA)", "https://sa.zain.com/en/investor-relations/financial-reports"),
    "sa:7040": ("Etihad Atheeb Telecommunication Company (GO)", "https://www.go.com.sa/en/investor-relations"),
}

GLOBAL_TELECOM_PEERS = (
    ("ae:eand", None, "e&", "AE", "EAND", "regional_integrated_operator", "https://www.eand.com/en/investors/annual-reports.html"),
    ("qa:ooredoo", None, "Ooredoo Q.P.S.C.", "QA", "ORDS", "regional_integrated_operator", "https://www.ooredoo.com/en/investors/financial-information/annual-reports/"),
    ("kw:zain", None, "Mobile Telecommunications Company K.S.C.P. (Zain Group)", "KW", "ZAIN", "regional_integrated_operator", "https://www.zain.com/en/investor-relations/financial-reports"),
    ("gb:vodafone", None, "Vodafone Group Plc", "GB", "VOD", "global_integrated_operator", "https://www.vodafone.com/investors/annual-reports"),
    ("fr:orange", None, "Orange S.A.", "FR", "ORA", "global_integrated_operator", "https://www.orange.com/en/finance/investors/annual-reports"),
    ("de:deutsche-telekom", None, "Deutsche Telekom AG", "DE", "DTE", "global_integrated_operator", "https://www.telekom.com/en/investor-relations/publications/financial-results"),
)


def seed_reviewed_peer_sets(conn) -> None:
    """Seed reviewed telecom peer identities without inventing financial data."""
    present = {row[0] for row in conn.execute("SELECT company_id FROM companies")}
    for company_id, (name, source_url) in SAUDI_TELECOMS.items():
        if company_id not in present:
            continue
        peer_set_id = f"reviewed:global-telecom:{company_id}"
        conn.execute(
            """INSERT INTO company_peer_sets(peer_set_id,company_id,name,methodology,scope,
            reviewed_at,source_url,metadata_json,enabled) VALUES(?,?,?,?,?,?,?,?,1)
            ON CONFLICT(peer_set_id) DO UPDATE SET methodology=excluded.methodology,
            reviewed_at=excluded.reviewed_at,source_url=excluded.source_url,enabled=1""",
            (peer_set_id, company_id, "Reviewed global telecommunications operators",
             "Explicit peers selected by comparable telecom/network-operator business classification; geography is not a constraint.",
             "global", "2026-09-22", source_url,
             json.dumps({"target_name": name, "selection_basis": "official company annual-report classification"})),
        )
        members = []
        for peer_id, (peer_name, peer_url) in SAUDI_TELECOMS.items():
            if peer_id != company_id and peer_id in present:
                members.append((peer_id, peer_id, peer_name, "SA", peer_id.split(":", 1)[1],
                                "domestic_network_operator", peer_url))
        members.extend(GLOBAL_TELECOM_PEERS)
        for key, linked_id, peer_name, market, symbol, rel_type, peer_url in members:
            conn.execute(
                """INSERT INTO company_peer_members(peer_set_id,peer_key,peer_company_id,peer_name,
                peer_market,peer_symbol,relationship_type,classification_source_url,rationale,
                metadata_json,enabled) VALUES(?,?,?,?,?,?,?,?,?,?,1)
                ON CONFLICT(peer_set_id,peer_key) DO UPDATE SET peer_company_id=excluded.peer_company_id,
                peer_name=excluded.peer_name,classification_source_url=excluded.classification_source_url,
                rationale=excluded.rationale,enabled=1""",
                (peer_set_id, key, linked_id, peer_name, market, symbol, rel_type, peer_url,
                 "Operator of public mobile/fixed telecommunications networks and adjacent digital services.", "{}"),
            )
    conn.commit()
