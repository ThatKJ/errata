"""SYNTHETIC DATASET — fictional company "Kestrel Ledger" and fictional customers.
Nothing here describes a real company. Ground truth is fixed by construction BEFORE any model runs.

- FACTS: 20 product facts (v1). CHANGES: 4 free-text change notes, each superseding exactly one fact (v2 text given).
- QUESTIONS: 30 questions previously answered to deals. `deps` = the facts a correct answer semantically relies on (ground truth B).
  `affected_by` = the change that makes the *previously sent* answer false or materially incomplete (gold impact label).
  Q03, Q07, Q10 are deliberate TRAPS: they depend on a changed fact but stay true after the change.
- NEW_QUESTIONS: 8 post-change questions for the superseded-fact test. `new` tokens must appear; `stale` tokens signal superseded usage.
"""

FACTS = {
    "F01": ("residency", "All Kestrel Ledger customer data is stored and processed only in AWS us-east-1 (N. Virginia, USA). No other hosting region is offered."),
    "F02": ("backups", "Kestrel Ledger encrypted backups are replicated to AWS us-west-2 (Oregon, USA) and kept for 35 days."),
    "F03": ("subprocessors", "Kestrel Ledger's only subprocessors are AWS (hosting), Stripe (billing) and Zendesk (support tickets). No other third party, including any analytics vendor, processes customer data."),
    "F04": ("encryption_rest", "Kestrel Ledger encrypts all data at rest with AES-256 using AWS KMS customer-managed keys."),
    "F05": ("encryption_transit", "Kestrel Ledger encrypts all data in transit with TLS 1.2 or higher."),
    "F06": ("soc2", "Kestrel Ledger holds a SOC 2 Type II report covering the web platform and public API. The Kestrel mobile app is out of scope of the SOC 2 report."),
    "F07": ("iso27001", "Kestrel Ledger is not ISO 27001 certified and has no ISO 27001 certification planned for 2026."),
    "F08": ("retention", "After contract termination, Kestrel Ledger permanently deletes all customer data within 90 days."),
    "F09": ("sso", "Kestrel Ledger supports SAML 2.0 single sign-on with Okta and Microsoft Entra ID on the Enterprise plan."),
    "F10": ("mfa", "Kestrel Ledger enforces multi-factor authentication for every user login."),
    "F11": ("sla", "Kestrel Ledger offers a 99.9% monthly uptime SLA on the Enterprise plan."),
    "F12": ("dr", "Kestrel Ledger's disaster recovery targets are an RTO of 4 hours and an RPO of 1 hour."),
    "F13": ("pentest", "Kestrel Ledger commissions an independent third-party penetration test of the web platform once a year."),
    "F14": ("breach_notice", "Kestrel Ledger notifies affected customers of a confirmed security breach within 72 hours."),
    "F15": ("support", "Kestrel Ledger support is available 24x5 on business days; Enterprise P1 incidents get 24x7 response."),
    "F16": ("rate_limit", "The Kestrel Ledger public API allows 1,000 requests per minute per tenant."),
    "F17": ("export", "Customers can export all their Kestrel Ledger data as CSV or JSON at any time."),
    "F18": ("audit_logs", "Kestrel Ledger retains tenant audit logs for 1 year."),
    "F19": ("pricing", "The Kestrel Ledger Enterprise plan starts at USD 40,000 per year."),
    "F20": ("gdpr", "Kestrel Ledger signs a GDPR Data Processing Agreement including EU Standard Contractual Clauses on request."),
}

CHANGES = [  # (id, superseded fact, free-text note as it would arrive in Slack/changelog, clean v2 fact text, date)
    ("E1", "F01", "Ops update Nov 3: our Mumbai region (AWS ap-south-1) is now GA. New Indian customers' data is stored and processed in India by default; us-east-1 is no longer the only region.",
     "Kestrel Ledger offers two hosting regions: AWS us-east-1 (N. Virginia, USA) and AWS ap-south-1 (Mumbai, India). Indian customers' data is stored and processed in India by default.", "2026-11-03"),
    ("E2", "F03", "Heads up from legal: as of Nov 4 we onboarded Snowflake (US) as a new subprocessor for product usage analytics; it receives customer account metadata.",
     "Kestrel Ledger's subprocessors are AWS (hosting), Stripe (billing), Zendesk (support tickets) and Snowflake (US-based product usage analytics, receives customer account metadata).", "2026-11-04"),
    ("E3", "F06", "Audit news: the new SOC 2 Type II report (period Jul-Sep 2026) now includes the Kestrel mobile app in scope, alongside web and API.",
     "Kestrel Ledger's SOC 2 Type II report (period Jul-Sep 2026) covers the web platform, public API and the Kestrel mobile app.", "2026-11-05"),
    ("E4", "F08", "Policy change Nov 6: due to a regulatory record-keeping hold, customer data is now retained for 180 days after termination before permanent deletion (previously 90).",
     "After contract termination, Kestrel Ledger retains customer data for 180 days for regulatory record-keeping, then permanently deletes it.", "2026-11-06"),
]

# (qid, deal, question, deps, affected_by or None)
QUESTIONS = [
    ("Q01", "Acme Fintech (IN)", "Where will our customer data be hosted and processed?", ["F01"], "E1"),
    ("Q02", "Bharat Microfinance (IN)", "Can our data remain within India to satisfy RBI data localisation rules?", ["F01"], "E1"),
    ("Q03", "Midwest Credit Union (US)", "Is our data stored inside the United States?", ["F01"], None),  # TRAP
    ("Q04", "Bharat Microfinance (IN)", "Where are backups of our data stored and for how long?", ["F02"], None),
    ("Q05", "Acme Fintech (IN)", "List every third party that processes our data.", ["F03"], "E2"),
    ("Q06", "Nordlys Bank (EU)", "Do you share any customer data with an analytics vendor?", ["F03"], "E2"),
    ("Q07", "Midwest Credit Union (US)", "Which company processes your billing?", ["F03"], None),  # TRAP
    ("Q08", "Nordlys Bank (EU)", "Will you sign a GDPR DPA with Standard Contractual Clauses?", ["F20"], None),
    ("Q09", "Pinecrest Insurance (US)", "Does your SOC 2 report cover your mobile app?", ["F06"], "E3"),
    ("Q10", "Acme Fintech (IN)", "Do you have a SOC 2 Type II report?", ["F06"], None),  # TRAP
    ("Q11", "Pinecrest Insurance (US)", "Are you ISO 27001 certified?", ["F07"], None),
    ("Q12", "Nordlys Bank (EU)", "How long after termination is our data deleted?", ["F08"], "E4"),
    ("Q13", "Midwest Credit Union (US)", "What happens to our data when the contract ends?", ["F08"], "E4"),
    ("Q14", "Acme Fintech (IN)", "Can we export all of our data before we leave?", ["F17"], None),
    ("Q15", "Bharat Microfinance (IN)", "Do you support SAML single sign-on?", ["F09"], None),
    ("Q16", "Pinecrest Insurance (US)", "Is multi-factor authentication enforced?", ["F10"], None),
    ("Q17", "Nordlys Bank (EU)", "What uptime SLA do you commit to?", ["F11"], None),
    ("Q18", "Midwest Credit Union (US)", "What are your RTO and RPO?", ["F12"], None),
    ("Q19", "Acme Fintech (IN)", "Do you run independent penetration tests?", ["F13"], None),
    ("Q20", "Pinecrest Insurance (US)", "How quickly will you notify us of a breach?", ["F14"], None),
    ("Q21", "Bharat Microfinance (IN)", "What are your support hours?", ["F15"], None),
    ("Q22", "Tasman Wealth (AU)", "Do you offer any hosting region in Asia-Pacific closer to Australia?", ["F01"], "E1"),
    ("Q23", "Tasman Wealth (AU)", "How is our data encrypted at rest?", ["F04"], None),
    ("Q24", "Tasman Wealth (AU)", "Which of your subprocessors are located in the USA?", ["F03"], "E2"),
    ("Q25", "Pinecrest Insurance (US)", "Is the mobile application included in your independent audit scope?", ["F06"], "E3"),
    ("Q26", "Nordlys Bank (EU)", "Will our data be fully erased within three months of offboarding?", ["F08"], "E4"),
    ("Q27", "Midwest Credit Union (US)", "What API rate limits apply?", ["F16"], None),
    ("Q28", "Bharat Microfinance (IN)", "How long do you keep audit logs?", ["F18"], None),
    ("Q29", "Acme Fintech (IN)", "Is data encrypted in transit?", ["F05"], None),
    ("Q30", "Tasman Wealth (AU)", "Which companies outside Australia receive any of our customer data?", ["F01", "F02", "F03"], "E2"),
]

# (id, question, new-value tokens (any must appear), stale tokens (signal superseded usage))
NEW_QUESTIONS = [
    ("N1", "Do you offer hosting in India?", ["mumbai", "ap-south-1"], ["only in aws us-east-1", "no other hosting region", "only us-east-1"]),
    ("N2", "List all of your subprocessors.", ["snowflake"], []),
    ("N3", "Is your mobile app in scope of your SOC 2 report?", ["includes the", "covers the", "in scope", "yes"], ["out of scope", "not in scope", "not covered"]),
    ("N4", "How long after termination is customer data deleted?", ["180"], ["90 days"]),
    ("N5", "Which hosting regions do you offer?", ["ap-south-1", "mumbai"], ["no other hosting region", "only region"]),
    ("N6", "Does any analytics provider receive customer data?", ["snowflake"], ["no analytics", "no other third party"]),
    ("N7", "Is your mobile app covered by an independent SOC 2 audit?", ["includes the", "covers the", "in scope", "yes"], ["out of scope", "not in scope", "not covered"]),
    ("N8", "Will our data be deleted within 90 days after we leave?", ["180"], []),
]

AFFECTED = {q[0]: q[4] for q in QUESTIONS}
GOLD_DEPS = {q[0]: q[3] for q in QUESTIONS}
TRAPS = {"Q03", "Q07", "Q10"}
