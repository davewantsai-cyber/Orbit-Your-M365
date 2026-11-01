# Scoring methodology

## Severity weights
| Severity | Points |
|----------|--------|
| Critical | 10 |
| High | 7 |
| Medium | 4 |
| Low | 1 |
| Pass | 0 |

## Normalisation
- **ScubaGear:** Fail + *Shall* → High; Fail + *Should* → Medium; Warning/manual → Low; N/A and Omitted are excluded.
- **Maester:** Failed uses the test's `Severity` (default Medium); Skipped is excluded.
- **Monkey365:** `level`/`severity` field; `pass` status → Pass.
- A mapped control may carry a **severity floor** (e.g. missing admin MFA is raised to Critical).

## Deduplication
Findings from different tools are merged when they share a control. Tool control IDs (version suffix stripped) are resolved through the aliases in `data/cve_mappings.json`; unmapped controls dedupe on their normalised ID. The worst severity wins.

## Posture score
`posture = passed_controls / total_controls × 100` over unique controls. It measures the share of evaluated controls that pass — **not** a probability of compromise. 50% means half of evaluated controls pass. Risk points (sum of weights) are shown alongside to indicate how severe the failures are.

## Top findings
Non-pass Critical/High findings ordered by severity, weight, number of mapped CVEs, then control ID; the top 3 appear in the report.

## CVE / NIST mapping
`data/cve_mappings.json` is a static, offline lookup from control to related CVEs / NIST 800-53 controls. The associations are **indicative** (the misconfiguration class relates to the vulnerability or control family), not proof that a tenant is exploitable; verify each before citing to a client. CVSS scores are included only where recorded in the file.
