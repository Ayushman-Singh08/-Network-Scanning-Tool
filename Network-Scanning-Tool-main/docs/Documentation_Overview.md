# Network Scanning Project - Documentation Overview

## Project Purpose
This project is a Python-based network scanner designed to analyze hosts and services on a given network. It provides multiple scanning techniques (ICMP, TCP, ARP) and outputs results in both terminal and text file formats. 
The tool is suitable for network administrators, penetration testers, and anyone needing to audit or explore network devices and open ports.

## Main Features
- **ICMP Scan**: 
Checks if a host is up using ping (echo request).
- **TCP Port Scan**: 
Scans specified ports on a target host to determine if they are open, closed, or filtered.
- **ARP Scan**: 
Discovers active hosts and their MAC addresses on a local network segment.
- **Flexible Targeting**: 
Accepts single IPs or entire subnets (e.g., 192.168.1.0/24).
- **Customizable Port Range**: 
Allows scanning of individual ports or ranges (e.g., 80,443,8080 or 1-1000).
- **Timeout Control**: 
User can set scan timeout for responsiveness.
- **Output to File**: 
Results can be saved to a text file for later analysis.

## Project Structure
```
Network Scanning /
├── main.py                # CLI entry point, argument parsing, result formatting/output
├── src/
│   ├── scanner.py         # Core scanning logic (ICMP, TCP, ARP)
│   └── __init__.py        # (empty or package marker)
├── tests/
│   ├── test_scanner.py    # Unit tests for scanner logic
│   └── test_integration.py# Integration tests for CLI and scanning
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Dev/test dependencies
├── setup.py               # Packaging info
├── _imports_/             # Banner and import helpers
├── docs/
│   └── Documentation_Overview.md # This file
└── README.md              # Quickstart and summary
```

## How It Works
- The user runs `main.py` from the command line, specifying a target IP/network, scan type, ports, and optional output file.
- The script validates inputs, invokes the appropriate scan(s) via `scanner.py`, and formats results for display or saving.
- ICMP scan reports host status (UP/DOWN) and IP.
- TCP scan reports port status for each specified port.
- ARP scan lists discovered IP and MAC addresses on the network.
- Results are printed to the terminal and, if requested, written to a file.

## Example Usage
```bash
# Scan a single host for ICMP and TCP ports 80,443,8080
python src/main.py 192.168.1.1 -p 80,443,8080

# Scan a subnet for ARP and save results
python src/main.py 192.168.1.0/24 -t arp -o arp_results.txt

# Full scan with all features and output to file
python src/main.py 192.168.1.1 -t all -p 1-1000 -o full_scan.txt
```

## Dependencies
- Python 3.10+
- scapy (network packet manipulation)
- ipaddress (standard library)
- typing-extensions (for type hints)

## Extending the Project
- Add new scan types (e.g., UDP, service detection) in `scanner.py`.
- Integrate with a web UI or dashboard for visualization.
- Add more output formats (e.g., JSON, CSV).
- Improve error handling and reporting.

## Testing
- Unit tests are in `tests/test_scanner.py`.
- Integration tests for CLI and output in `tests/test_integration.py`.
- Run tests with:
```bash
python -m unittest discover tests
```

## Security & Usage Notes
- Requires appropriate permissions to send raw packets (may need `sudo`).
- Use responsibly and only on networks you own or have permission to scan.

## Contact & Support
For issues, feature requests, or contributions, see the `README.md` or open an issue in the project repository.
