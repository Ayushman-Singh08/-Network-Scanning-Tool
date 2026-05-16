import argparse 
import re 
import subprocess
from time import sleep 
from scapy.all import Ether , srp , ARP 
from _imports_ import banner 

'''
TodoList:
1. Fix the calling pkt(str) python 3 makes no sense Suggestion -> Read the scapy documentation
2. Add a new feature to support the range of ip(s)
3. 
'''

"""
Note: 

For the first to do list. In python 3, scapy has changed the way it handles packets. It handles them as objects.
So, using str(pkt) will not work. You used srp() which is already correct. So i don't understand what you mean by 
"Fix the calling pkt(str) python 3 makes no sense Suggestion -> Read the scapy documentation" ?
====================================================================================================================
Change i added:

- I renamed the variable "results" to "results" in the ScanSpecificSubnet class. As it's not a constant, it should be in lower case.
- I renamed the variable "clients" to "clients" in the ScanSpecificSubnet class. As it's  not a constant, it should be in lower case.
- I added a try except block in the ScanSpecificAdd class to improve error handling.
- I added a try except block in the ScanSpecificSubnet class to improve error handling.(Maybe add a specific exception ??)
- I added a check to see if the ip address is in the correct format or not.
- I added a help message for the ip argument.
- I added a print of the IP and MAC addresses of the devices found on the network in the ScanSpecificAdd class.
- I'm working on README.md file to explain how to use the script. Is it okay for you?? 
=====================================================================================================================

"""

parser = argparse.ArgumentParser() 
IP_Help = "Destination IP Address Eg 192.168.1.1 or 192.168.1.0/24"
parser.add_argument("-ip", type=str , help = IP_Help)
args = parser.parse_args()

class ScanSpecificAdd:
    def __init__(self , ip):
        try:
            arp = ARP(pdst = ip)
            ether = Ether(dst = "ff:ff:ff:ff:ff:ff")
            packet = ether/arp 
            result = srp(packet , timeout = 3)[1]
        except Exception as e :
            print(f"Error scanning subnet {ip}: Network timeout or no response ")
            return 
        for sent , received in result :
            print(f"IP: {received.psrc} MAC: {received.hwsrc}")

class ScanSpecificSubnet:
    def __init__(self , ip):
        try:
            arp = ARP(pds = ip)
            ether = Ether(dst = "ff:ff:ff:ff:ff:ff")
            packet = ether/arp 
            results = srp(packet , timeout = 3)[0] 
        except Exception as e :
            print(f"Error scanning subnet {ip}: Network timeout or no response ")
            return 
        clients = [] 
        for sent , received in results:
            clients.append({'ip': received.psrc, 'mac': received.hwsrc})
        
        print(clients)

if __name__ == "__main__":
    banner() 
    ListedAddress = re.split(r"[.|/]", args.ip)

    for address in ListedAddress:
        if int(address) in range(0 , 256) and len(ListedAddress) == 4 or len(ListedAddress) == 5:
            continue 
        else:
            print("Follow the IP Address format ; 192.168.1.1 for single IP\n or 192.168.1.0/24 for subnet")
            sleep(3)
            exit() 
