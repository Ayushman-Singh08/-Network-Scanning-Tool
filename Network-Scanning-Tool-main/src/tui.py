import curses
import threading
import time
from typing import Optional
from scanner import NetworkScanner


def draw_box(stdscr, y, x, w, label=""):
    stdscr.addstr(y, x, "+" + "-" * (w - 2) + "+")
    stdscr.addstr(y + 1, x, "|" + " " * (w - 2) + "|")
    stdscr.addstr(y + 2, x, "+" + "-" * (w - 2) + "+")
    if label:
        stdscr.addstr(y, x + 2, f"[{label}]")


def prompt_field(stdscr, y, x, prompt, default: Optional[str] = None) -> str:
    stdscr.addstr(y, x, prompt)
    stdscr.clrtoeol()
    if default:
        stdscr.addstr(y, x + len(prompt) + 1, default)
        stdscr.refresh()
        curses.echo()
        s = stdscr.getstr(y, x + len(prompt) + 1, 60).decode(errors="ignore")
        curses.noecho()
        return s if s else default
    else:
        curses.echo()
        s = stdscr.getstr(y, x + len(prompt) + 1, 60).decode(errors="ignore")
        curses.noecho()
        return s


def display_results(stdscr, results):
    stdscr.clear()
    stdscr.addstr(0, 0, "Scan Results:")
    stdscr.addstr(1, 0, "=============")
    row = 3
    if results.get("icmp") is not None:
        status = "UP" if results["icmp"] else "DOWN"
        stdscr.addstr(row, 0, f"ICMP: {status}")
        row += 2
    if results.get("tcp") is not None:
        stdscr.addstr(row, 0, "TCP Port Scan Results:")
        row += 1
        for port, status in sorted(results["tcp"].items()):
            stdscr.addstr(row, 2, f"{port}: {status}")
            row += 1
        row += 1
    if results.get("udp") is not None:
        stdscr.addstr(row, 0, "UDP Port Scan Results:")
        row += 1
        for port, status in sorted(results["udp"].items()):
            stdscr.addstr(row, 2, f"{port}: {status}")
            row += 1
        row += 1
    if results.get("arp") is not None:
        stdscr.addstr(row, 0, "ARP Scan Results:")
        row += 1
        if results["arp"]:
            for c in results["arp"]:
                stdscr.addstr(row, 2, f"{c.get('ip')}\t{c.get('mac')}")
                row += 1
        else:
            stdscr.addstr(row, 2, "No hosts found")
            row += 1
    stdscr.addstr(row + 1, 0, "Press any key to return to the main menu...")
    stdscr.refresh()
    stdscr.getch()


def run_scan_thread(scanner: NetworkScanner, target, scan_type, ports, results_container, lock):
    try:
        res = scanner.scan_network(target=target, scan_type=scan_type, ports=ports)
        with lock:
            results_container.clear()
            results_container.update(res)
    except Exception as e:
        with lock:
            results_container.clear()
            results_container["__error__"] = str(e)


def run_tui(scanner: NetworkScanner):
    curses.wrapper(_tui_main, scanner)


def _tui_main(stdscr, scanner: NetworkScanner):
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.clear()

    # Defaults
    target = "127.0.0.1"
    ports = "80,443"
    scan_type = "udp"
    timeout = str(scanner.timeout)
    delay = str(scanner.delay)
    service_detect = False

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Packet-Hunters - Interactive TUI")
        stdscr.addstr(1, 0, "Use the prompts to configure a scan. Press 's' to start, 'q' to quit.")

        stdscr.addstr(3, 0, f"Target: {target}")
        stdscr.addstr(4, 0, f"Ports: {ports}")
        stdscr.addstr(5, 0, f"Scan type: {scan_type}  (toggle with 't')")
        stdscr.addstr(6, 0, f"Timeout: {timeout}")
        stdscr.addstr(7, 0, f"Delay: {delay}")
        stdscr.addstr(8, 0, f"Service detection: {'ON' if service_detect else 'OFF'} (toggle with 'd')")

        stdscr.addstr(10, 0, "Commands: (e)dit fields  (t)oggle scan type  (s)tart  (q)uit")
        stdscr.refresh()

        c = stdscr.getch()
        if c == ord('q'):
            return
        elif c == ord('e'):
            curses.curs_set(1)
            target = prompt_field(stdscr, 12, 0, "Target:", default=target)
            ports = prompt_field(stdscr, 13, 0, "Ports:", default=ports)
            timeout = prompt_field(stdscr, 14, 0, "Timeout:", default=timeout)
            delay = prompt_field(stdscr, 15, 0, "Delay:", default=delay)
            curses.curs_set(0)
        elif c == ord('t'):
            scan_type = "tcp" if scan_type == "udp" else "udp"
        elif c == ord('d'):
            service_detect = not service_detect
        elif c == ord('s'):
            # Start scan
            stdscr.clear()
            stdscr.addstr(0, 0, f"Starting {scan_type} scan on {target} ports {ports}...")
            stdscr.addstr(1, 0, "Scanning — please wait. This may require root privileges for some probes.")
            stdscr.refresh()

            try:
                port_list = None
                if ports.strip():
                    # simple parse
                    parts = []
                    for p in ports.split(','):
                        p = p.strip()
                        if '-' in p:
                            a, b = p.split('-')
                            parts.extend(list(range(int(a), int(b) + 1)))
                        else:
                            parts.append(int(p))
                    port_list = sorted(list(set(parts)))
            except Exception as e:
                stdscr.addstr(3, 0, f"Invalid ports: {e}")
                stdscr.addstr(4, 0, "Press any key to continue...")
                stdscr.getch()
                continue

            results_container = {}
            lock = threading.Lock()
            th = threading.Thread(target=run_scan_thread, args=(scanner, target, scan_type, port_list, results_container, lock))
            th.start()

            spinner = ['|', '/', '-', '\\']
            idx = 0
            while th.is_alive():
                stdscr.addstr(3, 0, f"Scanning... {spinner[idx % len(spinner)]}")
                stdscr.refresh()
                idx += 1
                time.sleep(0.2)

            with lock:
                if "__error__" in results_container:
                    stdscr.addstr(5, 0, f"Scan error: {results_container['__error__']}")
                    stdscr.addstr(6, 0, "Press any key to continue...")
                    stdscr.getch()
                    continue
                results = dict(results_container)

            display_results(stdscr, results)
        else:
            # ignored key
            pass
