# Field availability assessments

These reviewed artifacts survive database rebuilds and may change the actionable
denominator of the 18-category factory contract. Use one JSON file per company:

```json
{
  "company_id": "sa:7010",
  "assessments": [
    {
      "field_key": "example_metric",
      "status": "unavailable",
      "reason_code": "not_disclosed",
      "reason": "The issuer does not disclose this metric",
      "assessed_by": "reviewer-name",
      "evidence_source_url": "https://issuer.example/annual-report.pdf",
      "evidence_note": "The annual report and notes were searched.",
      "expires_at": "2027-04-01T00:00:00+00:00"
    },
    {
      "field_key": "example_inapplicable_metric",
      "status": "not_applicable",
      "reason_code": "not_applicable",
      "reason": "The company has no such business line",
      "assessed_by": "reviewer-name",
      "rule_reference": "telecom-pack:no-such-business-line"
    }
  ]
}
```

`unavailable` requires an exact URL that already exists in the company's source
archive with a content hash. `not_applicable` requires a structural rule reference.
Expired assessments are retained for audit but ignored by contract scoring. Missing,
invalid, or unarchived evidence fails bootstrap instead of silently raising coverage.
