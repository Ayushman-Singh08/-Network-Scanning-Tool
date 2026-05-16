

import argparse
import os
import sys
import logging
from datetime import datetime
from scanner import NetworkScanner
from typing import List, Optional
import ipaddress

def parse_ports(ports_str: str) -> List[int]:
    """Parse port string into list of integers"""
    ports = []
    try:
        for part in ports_str.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                if not (0 <= start <= 65535 and 0 <= end <= 65535):
                    raise ValueError("Port numbers must be between 0 and 65535")
                if start > end:
                    raise ValueError("Start port must be less than or equal to end port")
                ports.extend(range(start, end + 1))
            else:
                port = int(part)
                if not 0 <= port <= 65535:
                    raise ValueError("Port numbers must be between 0 and 65535")
                ports.append(port)
        return sorted(list(set(ports)))  # Remove duplicates and sort
    except ValueError as e:
        raise ValueError(f"Invalid port format: {str(e)}")

def validate_target(target: str) -> bool:
    """Validate target IP address or network"""
    try:
        # Try to parse as IP address
        ipaddress.ip_address(target)
        return True
    except ValueError:
        try:
            # Try to parse as network
            ipaddress.ip_network(target, strict=False)
            return True
        except ValueError:
            return False


def format_results(results: dict, target: Optional[str] = None) -> str:
    """Format the scan results into a string suitable for printing or writing to a file.

    If `target` is provided, include it in the ICMP line (e.g.:
    "ICMP Scan: Host 192.168.1.1 is UP").
    """
    lines = []
    lines.append("\nScan Results:")
    lines.append("=============\n")

    if results.get("icmp") is not None:
        status = "UP" if results["icmp"] else "DOWN"
        if target:
            lines.append(f"ICMP Scan: Host {target} is {status}\n")
        else:
            lines.append(f"ICMP Scan: Host is {status}\n")

    if results.get("tcp") is not None:
        lines.append("TCP Port Scan Results:")
        for port, status in sorted(results["tcp"].items()):
            lines.append(f"Port {port}: {status}")
        lines.append("")

    # Optional TCP service banners
    tcp_services = results.get("_tcp_services")
    if tcp_services:
        lines.append("TCP Service Detection:")
        for port, banner in sorted(tcp_services.items()):
            lines.append(f"Port {port}: {banner}")
        lines.append("")

    if results.get("udp") is not None:
        lines.append("UDP Port Scan Results:")
        for port, status in sorted(results["udp"].items()):
            lines.append(f"Port {port}: {status}")
        lines.append("")

    # Optional UDP service detection
    udp_services = results.get("_udp_services")
    if udp_services:
        lines.append("UDP Service Detection:")
        for port, info in sorted(udp_services.items()):
            lines.append(f"Port {port}: {info}")
        lines.append("")

    if results.get("arp") is not None:
        lines.append("ARP Scan Results:")
        if results["arp"]:
            lines.append("IP Address\t\tMAC Address")
            lines.append("----------------------------------------")
            for client in sorted(results["arp"], key=lambda x: ipaddress.ip_address(x['ip'])):
                lines.append(f"{client['ip']}\t\t{client['mac']}")
        else:
            lines.append("No hosts found in the network")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Network Scanner - A tool for analyzing hosts on a network",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "target",
        help="Target IP address or network (e.g., 192.168.1.1 or 192.168.1.0/24)"
    )
    
    parser.add_argument(
        "-t", "--type",
        choices=["all", "icmp", "tcp", "udp", "arp"],
        default="all",
        help="Type of scan to perform (default: all)"
    )
    
    parser.add_argument(
        "-p", "--ports",
        help="Ports to scan (e.g., 80,443 or 1-1000)"
    )
    
    parser.add_argument(
        "-T", "--timeout",
        type=int,
        default=2,
        help="Timeout in seconds for each scan (default: 2)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Write scan output to a text file",
        default=None
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between probes to avoid flooding the network (default: 0.0)"
    )

    parser.add_argument(
        "--udp-ambiguity",
        choices=["open", "closed"],
        default="open",
        help="How to classify ambiguous UDP results when no definitive response is received (default: open)"
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch the interactive curses-based TUI"
    )

    parser.add_argument(
        "--max-ports",
        type=int,
        default=1024,
        help="Maximum number of ports allowed in a single TCP scan (default: 1024)"
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the output file instead of overwriting"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force actions that would otherwise be blocked (e.g., overwrite files or run without warnings)"
    )

    parser.add_argument(
        "-s", "--service-detect",
        action="store_true",
        help="Perform basic service detection/banner grabbing on open ports"
    )
    
    try:
        args = parser.parse_args()
        
        # Validate target
        if not validate_target(args.target):
            print(f"Error: Invalid target format: {args.target}")
            print("Please provide a valid IP address (e.g., 192.168.1.1) or network (e.g., 192.168.1.0/24)")
            sys.exit(1)
        
        # Validate timeout
        if args.timeout <= 0:
            print("Error: Timeout must be a positive number")
            sys.exit(1)
        
        # Setup logging
        os.makedirs("logs", exist_ok=True)
        log_file = os.path.join("logs", "scanner.log")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        scanner = NetworkScanner(
            timeout=args.timeout,
            delay=args.delay,
            max_ports=args.max_ports,
            udp_ambiguity=args.udp_ambiguity
        )

        # If TUI requested, launch it and exit
        if args.tui:
            try:
                from tui import run_tui
            except Exception:
                # try package-style import if running as module
                from src.tui import run_tui  # type: ignore
            run_tui(scanner)
            return

        # Privilege check: scapy often requires root for raw sockets; warn user
        if os.geteuid() != 0:
            # ARP and some raw socket operations require root privileges
            if args.type in ["arp"] or args.type == "all":
                msg = "ARP and raw socket scans may require root privileges. Run with sudo or use --force to continue anyway."
                if not args.force:
                    print("Warning:", msg)
                    print("Aborting since --force not provided")
                    sys.exit(1)
                else:
                    print("Warning:", msg, "Proceeding due to --force.")
        
        # Parse ports if provided
        ports = None
        if args.ports:
            try:
                ports = parse_ports(args.ports)
            except ValueError as e:
                print(f"Error: {str(e)}")
                sys.exit(1)
        
        # Perform scan
        results = scanner.scan_network(
            target=args.target,
            scan_type=args.type,
            ports=ports
        )

        # Optionally perform service detection (banner grabbing)
        if args.service_detect:
            # TCP service detection for ports marked 'open'
            if results.get("tcp"):
                open_tcp = [p for p, s in results["tcp"].items() if s == "open"]
                if open_tcp:
                    tcp_services = scanner.tcp_service_detect(args.target, open_tcp)
                    results["_tcp_services"] = tcp_services

            # UDP service detection for ports marked 'open' or 'open|filtered'
            if results.get("udp"):
                udp_ports = [p for p, s in results["udp"].items() if s in ("open", "open|filtered")]
                if udp_ports:
                    udp_services = scanner.udp_service_detect(args.target, udp_ports)
                    results["_udp_services"] = udp_services

        # Format results (single string) and print
        output_text = format_results(results, target=args.target)
        print(output_text)

        # If output file provided, write to it safely
        if args.output:
            mode = "a" if args.append else "w"
            if os.path.exists(args.output) and not args.append and not args.force:
                print(f"Error: Output file {args.output} exists. Use --append to append or --force to overwrite.")
                sys.exit(1)

            # Prepend metadata header when creating new file or when not appending
            header = (
                f"Scan run: {datetime.utcnow().isoformat()}Z\n"
                f"Target: {args.target}\n"
                f"Scan type: {args.type}\n"
                f"Ports: {args.ports or 'None'}\n"
                f"Timeout: {args.timeout}s\n"
                f"Delay between probes: {args.delay}s\n"
                "---\n"
            )

            try:
                with open(args.output, mode, encoding="utf-8") as f:
                    if mode == "w":
                        f.write(header)
                    f.write(output_text + "\n")
                print(f"\nResults written to: {args.output}")
            except Exception as e:
                print(f"Failed to write to {args.output}: {e}")
    
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 