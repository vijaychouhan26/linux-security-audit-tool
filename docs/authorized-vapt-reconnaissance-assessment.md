# Authorized VAPT Reconnaissance & Enumeration Assessment

**Project type:** Cybersecurity / VAPT Minor Project  
**Assessment date:** August 18, 2026  
**Target:** `www.networksolutions.com`  
**Authorization:** Web.com Bug Bounty via Bugcrowd  
**Scope note:** The assessment was performed against the authorized target. Wildcard subdomains were documented for academic context only. No exploitation or customer-account interaction was performed.

## Objective

Perform a structured reconnaissance and enumeration assessment and document the attack surface, exposed services, security observations, severity, impact, and remediation recommendations.

## Methodology

| Phase | Activity | Tool |
|---|---|---|
| 1 | Target profiling | WHOIS, Netcraft |
| 2 | Subdomain enumeration | Subfinder |
| 3 | Service enumeration | Nmap |
| 4 | Web enumeration | ffuf |
| 5 | Intelligence gathering | Shodan |

## Assessment Summary

- **615** unique subdomains were identified from 1,230 raw results.
- **4** CDN-facing TCP ports were observed: 80, 443, 8080, and 8443.
- **7** origin IPs were identified through Shodan.
- Observations included exposed cPanel/WHM interfaces, Exim version disclosure, legacy JSP endpoints, publicly accessible test infrastructure, and session identifiers in URLs.

## Key Technical Observations

### DNS / Infrastructure

WHOIS and Netcraft indicated Cloudflare protection and origin-IP hiding at the primary web layer. The assessment also identified origin infrastructure through external intelligence sources.

### Shodan

Shodan results identified origin IPs and exposed services including SMTP and cPanel/WHM. Exim version banners and self-signed certificates were observed on production mail infrastructure. An internal hostname was also visible in an SSL certificate.

### Subdomain Enumeration

Subfinder identified 615 unique subdomains. Examples of notable entries documented in the assessment included OWA, customer-service remote access, control-panel, payment infrastructure, VPN, staging, test, and management environments.

### Nmap

The assessment observed HTTP/HTTPS services on 80, 443, 8080, and 8443, while the remaining tested ports were filtered.

### Web Enumeration

ffuf was used after Gobuster encountered Cloudflare WAF blocking. The assessment documented accessible application paths and redirects, including a security disclosure page and a potentially interesting `/save` flow for further authorized business-logic review.

## Risk Summary

| Finding | Severity |
|---|---|
| cPanel/WHM accessible on origin IPs | Critical |
| Origin IPs bypassing Cloudflare | High |
| Exim version disclosure | High |
| Legacy acquisition-related JSP endpoints | High |
| Internal hostname in SSL certificate | Medium |
| Self-signed certificates on production mail servers | Medium |
| Publicly accessible test environment | Medium |
| Large set of dev/QA/UAT subdomains | Medium |
| Java session IDs in URLs | Medium |
| Legacy Struts/Spring endpoint | Medium |
| OWA exposed | Medium |
| DNSSEC not implemented | Low |

## Recommendations

1. Restrict cPanel/WHM access on origin infrastructure to VPN or approved IP ranges.
2. Configure origin servers to accept traffic only from trusted Cloudflare ranges where appropriate.
3. Update Exim and suppress unnecessary SMTP version disclosure.
4. Audit and decommission legacy JSP and CGI endpoints that are no longer required.
5. Replace self-signed production certificates with certificates issued by a trusted CA.
6. Place test and staging environments behind VPN or IP allowlisting.
7. Prevent session identifiers from being exposed in URLs and review session-management controls.
8. Consider DNSSEC to provide cryptographic validation of DNS responses.

## What This Project Demonstrates

- Linux command-line usage and security tooling
- Network and service enumeration
- DNS and web infrastructure analysis
- HTTP/HTTPS observation
- WAF-aware troubleshooting and tool selection
- Structured root-cause-oriented investigation
- Risk classification and prioritization
- Technical documentation and remediation writing
- Responsible security testing within an authorized scope

## Ethical / Scope Note

This documentation is a record of authorized academic security research. It does not contain credentials, private customer information, or instructions for unauthorized access. Any future testing should remain within the target's published authorization and scope.

## Source

Assessment details are based on the accompanying VAPT project report prepared for the academic minor project.