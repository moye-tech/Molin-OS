     1|---
     2|name: ag-web-security-testing
     3|description: "Web application security testing workflow for OWASP Top 10 vulnerabilities including injection, XSS, authentication flaws, and access control issues."
     4|version: 1.0.0
     5|tags: [antigravity, security]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: web-security-testing
    12|description: "Web application security testing workflow for OWASP Top 10 vulnerabilities including injection, XSS, authentication flaws, and access control issues."
    13|category: granular-workflow-bundle
    14|risk: safe
    15|source: personal
    16|date_added: "2026-02-27"
    17|---
    18|
    19|# Web Security Testing Workflow
    20|
    21|## Overview
    22|
    23|Specialized workflow for testing web applications against OWASP Top 10 vulnerabilities including injection attacks, XSS, broken authentication, and access control issues.
    24|
    25|## When to Use This Workflow
    26|
    27|Use this workflow when:
    28|- Testing web application security
    29|- Performing OWASP Top 10 assessment
    30|- Conducting penetration tests
    31|- Validating security controls
    32|- Bug bounty hunting
    33|
    34|## Workflow Phases
    35|
    36|### Phase 1: Reconnaissance
    37|
    38|#### Skills to Invoke
    39|- `scanning-tools` - Security scanning
    40|- `top-web-vulnerabilities` - OWASP knowledge
    41|
    42|#### Actions
    43|1. Map application surface
    44|2. Identify technologies
    45|3. Discover endpoints
    46|4. Find subdomains
    47|5. Document findings
    48|
    49|#### Copy-Paste Prompts
    50|```
    51|Use @scanning-tools to perform web application reconnaissance
    52|```
    53|
    54|### Phase 2: Injection Testing
    55|
    56|#### Skills to Invoke
    57|- `sql-injection-testing` - SQL injection
    58|- `sqlmap-database-pentesting` - SQLMap
    59|
    60|#### Actions
    61|1. Test SQL injection
    62|2. Test NoSQL injection
    63|3. Test command injection
    64|4. Test LDAP injection
    65|5. Document vulnerabilities
    66|
    67|#### Copy-Paste Prompts
    68|```
    69|Use @sql-injection-testing to test for SQL injection
    70|```
    71|
    72|```
    73|Use @sqlmap-database-pentesting to automate SQL injection testing
    74|```
    75|
    76|### Phase 3: XSS Testing
    77|
    78|#### Skills to Invoke
    79|- `xss-html-injection` - XSS testing
    80|- `html-injection-testing` - HTML injection
    81|
    82|#### Actions
    83|1. Test reflected XSS
    84|2. Test stored XSS
    85|3. Test DOM-based XSS
    86|4. Test XSS filters
    87|5. Document findings
    88|
    89|#### Copy-Paste Prompts
    90|```
    91|Use @xss-html-injection to test for cross-site scripting
    92|```
    93|
    94|### Phase 4: Authentication Testing
    95|
    96|#### Skills to Invoke
    97|- `broken-authentication` - Authentication testing
    98|
    99|#### Actions
   100|1. Test credential stuffing
   101|2. Test brute force protection
   102|3. Test session management
   103|4. Test password policies
   104|5. Test MFA implementation
   105|
   106|#### Copy-Paste Prompts
   107|```
   108|Use @broken-authentication to test authentication security
   109|```
   110|
   111|### Phase 5: Access Control Testing
   112|
   113|#### Skills to Invoke
   114|- `idor-testing` - IDOR testing
   115|- `file-path-traversal` - Path traversal
   116|
   117|#### Actions
   118|1. Test vertical privilege escalation
   119|2. Test horizontal privilege escalation
   120|3. Test IDOR vulnerabilities
   121|4. Test directory traversal
   122|5. Test unauthorized access
   123|
   124|#### Copy-Paste Prompts
   125|```
   126|Use @idor-testing to test for insecure direct object references
   127|```
   128|
   129|```
   130|Use @file-path-traversal to test for path traversal
   131|```
   132|
   133|### Phase 6: Security Headers
   134|
   135|#### Skills to Invoke
   136|- `api-security-best-practices` - Security headers
   137|
   138|#### Actions
   139|1. Check CSP implementation
   140|2. Verify HSTS configuration
   141|3. Test X-Frame-Options
   142|4. Check X-Content-Type-Options
   143|5. Verify referrer policy
   144|
   145|#### Copy-Paste Prompts
   146|```
   147|Use @api-security-best-practices to audit security headers
   148|```
   149|
   150|### Phase 7: Reporting
   151|
   152|#### Skills to Invoke
   153|- `reporting-standards` - Security reporting
   154|
   155|#### Actions
   156|1. Document vulnerabilities
   157|2. Assess risk levels
   158|3. Provide remediation
   159|4. Create proof of concept
   160|5. Generate report
   161|
   162|#### Copy-Paste Prompts
   163|```
   164|Use @reporting-standards to create security report
   165|```
   166|
   167|## OWASP Top 10 Checklist
   168|
   169|- [ ] A01: Broken Access Control
   170|- [ ] A02: Cryptographic Failures
   171|- [ ] A03: Injection
   172|- [ ] A04: Insecure Design
   173|- [ ] A05: Security Misconfiguration
   174|- [ ] A06: Vulnerable Components
   175|- [ ] A07: Authentication Failures
   176|- [ ] A08: Software/Data Integrity
   177|- [ ] A09: Logging/Monitoring
   178|- [ ] A10: SSRF
   179|
   180|## Quality Gates
   181|
   182|- [ ] All OWASP Top 10 tested
   183|- [ ] Vulnerabilities documented
   184|- [ ] Proof of concepts captured
   185|- [ ] Remediation provided
   186|- [ ] Report generated
   187|
   188|## Related Workflow Bundles
   189|
   190|- `security-audit` - Security auditing
   191|- `api-security-testing` - API security
   192|- `wordpress-security` - WordPress security
   193|
   194|## Limitations
   195|- Use this skill only when the task clearly matches the scope described above.
   196|- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
   197|- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
   198|