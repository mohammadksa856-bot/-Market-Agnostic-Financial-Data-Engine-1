# Master Schema v8

The catalog is the governed target for collection. It is not a claim that every
company discloses every field, and it never authorizes agents to invent a value.

## Composition

Every company receives the universal pack, the dividend pack, and the
announcement pack. It then receives exactly the applicable sector pack selected
by its reviewed canonical `industry` in the company registry.

| Pack | Canonical industry | Fields |
|---|---|---:|
| `company_core_v5` | All companies | 532 |
| `dividends_v1` | All companies | 20 |
| `announcements_v1` | All companies | 28 |
| `oil_gas_v2` | Integrated Oil & Gas | 69 |
| `chemicals_v1` | Diversified Chemicals | 43 |
| `banking_v1` | Banks | 34 |
| `insurance_v1` | Insurance | 26 |
| `telecommunications_v1` | Telecommunications | 25 |
| `utilities_v1` | Utilities | 23 |
| `mining_v1` | Mining | 25 |
| `real_estate_v1` | Real Estate & REITs | 26 |
| `retail_v1` | Retail | 23 |
| `healthcare_v1` | Health Care | 23 |
| `transportation_logistics_v1` | Transportation & Logistics | 22 |
| `industrial_construction_v1` | Industrials & Construction | 21 |
| `technology_v1` | Technology | 23 |
| `food_agriculture_v1` | Food & Agriculture | 20 |
| `asset_management_v1` | Asset Management | 20 |

There are 1,003 unique catalog fields, 873 enforceable metric contracts, and 61
governed dimensions. Shared accounting, valuation, market, ownership, disclosure,
segment, and calculation fields remain in the universal packs so a sector pack
does not duplicate them.

## Application rules

- The registry uses the canonical industry names shown above. A new company must
  be classified during onboarding before its completeness backlog is generated.
- A field is applicable only when its pack matches the company. For example,
  `subscriber_count` is not an expected field for a bank.
- Missing applicable fields are backlog items with an explicit reason: pending
  extraction, not disclosed, not applicable, event not observed, missing formula
  inputs/history, qualitative-only, or licensed source required.
- Values enter staging with source, artifact hash, page/table, reported label,
  period semantics, unit, dimensions, and mapping confidence. Only deterministic
  normalization and validation may publish them.
- Sector fields use the same restatement, idempotency, versioning, exception, and
  read-only query controls as financial-statement facts.

## Coverage lifecycle

1. Classify the company and apply its packs.
2. Generate the company completeness matrix and durable backlog.
3. Monitor official issuer/exchange/SEC sources and archive immutable artifacts.
4. Extract source-faithful facts, map them to this catalog, and retain lineage.
5. Normalize units and FY/Q/YTD/TTM semantics, then validate and publish.
6. Recalculate deterministic ratios and expose production data through the API or
   Telegram bot.

The current release establishes the schema and enforcement layer. Formula
coverage and source-specific extraction templates are expanded pack by pack; a
field being defined does not mean it is already populated for a company.
