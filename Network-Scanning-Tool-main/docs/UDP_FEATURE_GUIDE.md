# UDP Port Scanning Feature - Implementation Guide

## Overview
UDP port scanning capability has been successfully added to the Network Scanning Tool. This enables users to perform comprehensive network reconnaissance across TCP, UDP, and ARP protocols.

## What is UDP Scanning?

UDP (User Datagram Protocol) is a connectionless protocol unlike TCP. UDP scanning is more challenging than TCP scanning because:
- UDP doesn't establish a connection (no handshake)
- Responses are less reliable and may be rate-limited
- Open ports may not respond at all
- Closed ports typically respond with ICMP "Port Unreachable"

## How It Works

The UDP scan implementation in this project:

1. **Sends UDP packets** to specified ports on the target
2. **Analyzes responses**:
   - **No response** → `open|filtered` (port may be open or filtered by firewall)
   - **ICMP Port Unreachable (type 3, code 3)** → `closed`
   - **ICMP Host/Protocol Unreachable** → `filtered`
   - **UDP response** → `open`
   - **Other ICMP response** → `open|filtered`

3. **Respects rate limiting** with `--delay` parameter to avoid network flooding

## Port Status Meanings

| Status | Meaning |
|--------|---------|
| `open` | Port is confirmed open (UDP response received) |
| `closed` | Port is confirmed closed (ICMP unreachable) |
| `filtered` | Port is blocked by firewall or access control |
| `open\|filtered` | Cannot determine if port is open or filtered |
| `error` | Error occurred during scan |

## Usage Examples

### Scan a single UDP port
```bash
python src/main.py 192.168.1.100 -t udp -p 53
```

### Scan multiple UDP ports
```bash
python src/main.py 192.168.1.100 -t udp -p 53,123,161,389
```

### Scan UDP port range
```bash
python src/main.py 192.168.1.100 -t udp -p 1-1000
```

### UDP scan with rate limiting (0.5 sec delay between probes)
```bash
python src/main.py 192.168.1.100 -t udp -p 53,123,161 --delay 0.5
```

### Save UDP scan results to file
```bash
python src/main.py 192.168.1.100 -t udp -p 53,123,161 -o udp_scan_results.txt
```

### Run all scans including UDP (ICMP, TCP, UDP, ARP)
```bash
python src/main.py 192.168.1.100 -t all -p 80,443,53,123 -o full_scan.txt
```

### UDP scan with custom timeout
```bash
python src/main.py 192.168.1.100 -t udp -p 1-500 -T 3 --delay 0.2
```

## Sample Output

```
Scan Results:
=============

ICMP Scan: Host 192.168.1.100 is UP

UDP Port Scan Results:
Port 53: open
Port 123: open|filtered
Port 161: filtered
Port 389: closed
```

## Common UDP Ports to Scan

| Port | Service | Purpose |
|------|---------|---------|
| 53 | DNS | Domain Name System |
| 123 | NTP | Network Time Protocol |
| 161 | SNMP | Simple Network Management Protocol |
| 162 | SNMP Trap | SNMP Trap Service |
| 389 | LDAP | Lightweight Directory Access Protocol |
| 636 | LDAPS | LDAP over SSL/TLS |
| 5353 | mDNS | Multicast DNS |
| 67 | DHCP | Dynamic Host Configuration Protocol |
| 68 | DHCP | DHCP Client |
| 111 | Portmapper | RPC Port Mapper |
| 137 | NetBIOS | NetBIOS Name Service |
| 138 | NetBIOS | NetBIOS Datagram Service |
| 500 | IKE | Internet Key Exchange |
| 514 | Syslog | System Logging |
| 1900 | UPNP | Universal Plug and Play |

## CLI Reference

Updated command-line options:

```
python src/main.py TARGET [OPTIONS]

Positional Arguments:
  TARGET                    Target IP or network (e.g., 192.168.1.1 or 192.168.1.0/24)

Optional Arguments:
  -t, --type {all,icmp,tcp,udp,arp}    Scan type (default: all)
  -p, --ports PORTS                    Ports to scan (e.g., 80,443 or 1-1000)
  -T, --timeout SECONDS                Timeout per scan (default: 2)
  -o, --output FILE                    Save results to file
  --delay SECONDS                      Delay between probes (default: 0.0)
  --max-ports MAX                      Max ports per scan (default: 1024)
  --append                             Append to output file
  --force                              Force overwrite/continue
  -h, --help                           Show help message
```

## Implementation Details

### Modified Files

1. **src/scanner.py**
   - Added `UDP` to Scapy imports
   - Added `udp_scan(target, ports)` method
   - Updated `scan_network()` to support UDP scan type
   - Rate limiting applies to UDP scans

2. **src/main.py**
   - Added `udp` to `--type` choices
   - Updated `format_results()` to display UDP results
   - UDP scan type automatically triggers port requirement

### Code Structure

```python
def udp_scan(self, target: str, ports: List[int]) -> Dict[int, str]:
    """
    Perform UDP scan on specified ports
    Returns dictionary of port:status
    """
    # Implementation details:
    # - Validates ports don't exceed max_ports limit
    # - Sends UDP packets to each port
    # - Analyzes ICMP responses
    # - Applies rate limiting with self.delay
    # - Logs exceptions via logger
    # - Returns port:status dictionary
```

## Security & Ethical Considerations

⚠️ **Important:**
- UDP scanning is **less reliable** than TCP (some responses may be delayed or dropped)
- Some hosts rate-limit ICMP responses, causing false positives
- Only scan networks you own or have written permission to scan
- Use appropriate timeouts; UDP services may be slow to respond
- Respect network resources with `--delay` on production networks

## Performance Notes

- **UDP scans are typically slower** than TCP due to fewer reliable responses
- **Timeout is critical**: UDP responses may take longer; consider increasing `-T` (timeout)
- **Rate limiting recommended**: Use `--delay 0.2-0.5` on production networks
- **ICMP filtering**: Many networks filter ICMP responses, so `open|filtered` is common

## Future Enhancements

Potential improvements for UDP scanning:
- Service fingerprinting (identify running services by response)
- DNS query probing for port 53
- NTP monlist queries for port 123
- SNMP community string enumeration
- Parallel scanning for performance
- Custom UDP payload support

## Troubleshooting

### No responses received
- **Cause**: ICMP filtering or host offline
- **Solution**: Verify host is reachable with ICMP scan first

### All ports show as `open|filtered`
- **Cause**: Normal UDP behavior; firewall may block all responses
- **Solution**: Use `--delay` and increase timeout; try specific services

### "Max ports exceeded" error
- **Cause**: Trying to scan >1024 ports
- **Solution**: Use `--max-ports 2000` or scan fewer ports

### Permission denied errors
- **Cause**: Running without root privileges
- **Solution**: Use `sudo python src/main.py ...` or use `--force`

## Testing the UDP Feature

Test scan a local DNS server (port 53):
```bash
sudo python src/main.py 8.8.8.8 -t udp -p 53 -T 3
```

Test scan multiple services:
```bash
sudo python src/main.py 192.168.1.1 -t udp -p 53,123,161,389 --delay 0.3 -o udp_results.txt
```

Verify output:
```bash
cat udp_results.txt | grep "UDP Port"
```

## Documentation Updates

The following project documents have been updated:
- README.md: Added UDP usage examples
- docs/Documentation_Overview.md: Added UDP feature
- docs/Project_Presentation_Content.md: Updated with UDP capability

---

**Feature Status**: ✅ Complete and Ready for Use
**Added**: December 2025
**Tested**: Linux with Python 3.10+
