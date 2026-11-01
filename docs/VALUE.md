# The Value of M365 Security Assessment

## The problem

Microsoft 365 is the identity and data backbone of most modern organisations. It is also one of the most commonly misconfigured environments in the wild.

A default or lightly hardened M365 tenant routinely fails **15–30% of CISA's Secure Cloud Business Applications (SCuBA) baseline controls**. Each failed control is a potential attack vector — a way for threat actors to gain access, escalate privileges, exfiltrate data, or establish persistence.

Most organisations — including many that have deployed M365 for years — have never had a formal security assessment.

---

## What a manual assessment looks like

A skilled analyst performing a manual M365 security review typically spends:

| Task | Time |
|------|------|
| Logging into each admin portal (Entra, Exchange, Defender, SharePoint, Teams, Purview) | 30–45 min |
| Reviewing Conditional Access policies | 45–60 min |
| Checking MFA, legacy auth, and identity settings | 30–45 min |
| Reviewing email security (SPF/DKIM/DMARC, anti-phish, forwarding rules) | 30–45 min |
| Checking SharePoint/OneDrive sharing settings | 20–30 min |
| Reviewing Teams external access and guest settings | 20–30 min |
| Checking audit log settings and retention | 15–20 min |
| Reviewing privileged role assignments | 20–30 min |
| Cross-referencing findings against CISA/CIS baselines | 45–60 min |
| Writing the report with findings, risk ratings, and remediation steps | 60–120 min |
| **Total** | **4–8 hours** |

That's a full working day, minimum, for one experienced analyst. Then it needs to be repeated every time the configuration changes.

---

## What ORBIT does

ORBIT compresses that to **10–15 minutes of hands-on time**:

1. Enter credentials once (stored in OS keychain — not re-entered next time).
2. Select tools and output folder.
3. Press Run.
4. Tool runtime is 5–20 minutes depending on tenant size (unattended — you can do other work).
5. ORBIT parses output from all tools, scores every finding, and writes a formatted summary report.

Total hands-on time: under 15 minutes.

---

## What clients get

When you present ORBIT's output to a client or stakeholder:

- **An overall posture score** (0–100) and severity breakdown they can understand at a glance.
- **Prioritised top findings** with CVE references and specific remediation steps — not just "MFA should be enabled" but the exact Conditional Access policy to create.
- **Evidence** from authoritative tools (CISA ScubaGear, Maester, Monkey365) they can verify independently.
- **Compliance mapping** against CISA SCuBA, CIS M365 Foundations Benchmark, NIST SP 800-53, and MITRE ATT&CK.
- **A re-runnable method** — run ORBIT again after remediation to demonstrate improvement.
- **A reproducible baseline** — the same tools, the same controls, every time.

---

## Value for clients who have never had an assessment

For an organisation that has never formally assessed their M365 environment, the first ORBIT run is often eye-opening.

Common findings on first assessment:

| Finding | Typical severity | What an attacker can do |
|---------|-----------------|------------------------|
| Legacy authentication not blocked | Critical | Bypass MFA using older protocols (IMAP, POP3, Basic Auth) |
| MFA not required for admins | Critical | Account takeover of privileged accounts with phished credentials |
| Unrestricted external email forwarding | High | Silent data exfiltration of all email |
| Audit logs not retained for 1 year | High | Attacker activity invisible; incident response impaired |
| SharePoint external sharing unrestricted | High | Sensitive documents shared externally without oversight |
| No anti-phishing policy | High | Impersonation attacks against users and executives |
| Conditional Access not enforced | High | Access from untrusted devices and locations |
| No DMARC policy | Medium | Email spoofing of your domain |

Many of these findings have exploits in the wild today. Fixing them is often a matter of a few configuration changes — but you can't fix what you haven't found.

---

## Time saved over a year

If you assess a client quarterly:

| Activity | Without ORBIT | With ORBIT |
|----------|--------------|------------|
| Per assessment | 4–8 hours | 10–15 minutes active |
| Per year (quarterly) | 16–32 hours | ~1 hour active |
| Time saved per client per year | — | **15–31 hours** |

At a day rate of £400–£600, that's **£6,000–£18,600 of billable time** freed per client per year that can be redirected to higher-value work — or passed on as cost savings.

---

## Everything stays on your machine

Unlike SaaS compliance tools that process your tenant data in the cloud, ORBIT:

- Runs entirely client-side — no data leaves your machine.
- Uses open-source tools from CISA and the security research community.
- Has no subscription fee, no per-seat cost, and no data processing agreements to negotiate.
- Can be audited: the source code is fully open.

This makes it suitable for use with clients who have strict data sovereignty, regulatory, or contractual restrictions on sharing configuration data with third parties.
