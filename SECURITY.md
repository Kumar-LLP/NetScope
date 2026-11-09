# Security Policy

## Supported Versions
NetScope actively maintains security patches for the following versions:

| Version | Supported |
| :--- | :--- |
| 1.0.x | :white_check_mark: Yes |
| < 1.0 | :x: No |

---

## Defensive Engineering Architecture
NetScope is strictly designed as an observability, diagnostic, and cybersecurity auditing tool. It is engineered with defense-in-depth principles:

1. **Non-Elevated Privilege Safe Operations**: Standard dashboard operations run with ordinary user permissions on Windows 11 and Linux without requiring administrative or root rights.
2. **Explicit Port Scan Authorization**: The backend enforces an explicit authorization confirmation flag before executing any TCP port probes.
3. **Zero Shell Interpolation**: All external process invocations (`ping`, `tracert`, `arp`) use tokenized argument arrays via Python's `subprocess.run(["cmd", "arg"])` with `shell=True` strictly forbidden.
4. **Zero Traffic Payload Capture**: NetScope only inspects performance counters and hardware headers. It never captures, inspects, or stores private plaintext application payload packets or credentials.

---

## Reporting a Vulnerability
If you discover a potential security vulnerability within NetScope, please do not file a public issue on GitHub. Instead, report it privately to the maintainers at `security@netscope-project.org`. We strive to acknowledge reports within 48 hours and provide a coordinated disclosure timeline.
