
import re

model = re.compile(r'Model:\s(\S+)')

# ipv4 cidr
ipv4_cidr = re.compile(r'((\d+\.){3}\d+\/\d+)')
rfc1918_a = re.compile(r'')
rfc1918_b = re.compile(r'172\.(1[6-9]|2[0-9]|3[01])')
rfc1918_c = re.compile(r'')

bgp_nei_v4 = re.compile(r'neighbor\s((\d+\.){3}\d+)')

# ios
ios_intf = re.compile(r'^interface\s(([a-zA-Z\-]+)([\d\/\.]+))')
ios_intf_ip_v4 = re.compile(r'ip\saddress\s((\d+\.){3}\d+)\s((\d+\.){3}\d+)')

# nexus
nxos_intf_ip_v4 = re.compile(r'ip\saddress\s((\d+\.){3}\d+\/\d+)')

# junos
#junos_intf = re.compile(r'^\s+([a-z]+\-?[\d\/]+)\s{')
junos_intf = re.compile(r'^\s+(\S+\d(\S+)?)\s{')
model = re.compile(r'Model:\s(\S+)')
junos_version = re.compile(r'Junos:\s(\S+)')
                                                   # check paren> v  v
junos_intf_ip_v4 = re.compile(r'\saddress\s((\d+\.){3}\d+\/\d+)(\s{|;)')

# junos srx
srx_version = re.compile(r'JUNOS\sSoftware\sRelease\s\[(\S+)\]')
junos_node = re.compile(r'\s+(node\d+)\s{')

# junos other
ex_version = re.compile(r'JUNOS\sEX\s+Software\sSuite\s\[(\S+)\]')
qfx3500_version = re.compile(r'JUNOS\sBase\sOS\sboot\s\[(\S+)\]')

# cumulus
cumul_intf = re.compile(r'^interface\s([\w\d\.]+)')
cumul_intf_ip_v4 = re.compile(r'\saddress\s((\d+\.){3}\d+\/\d+)')

# ios
nhrp_ip_v4 = re.compile(r'(vrrp|standby)\s?(\d+)?\s?ip\s((\d+\.){3}\d+)')

# junos
junos_vrrp_v4 = re.compile(r'virtual-address\s((\d+\.){3}\d+);')

# cumulus
cumul_vrrp_v4 = re.compile(r'address-virtual\s[\d\w:]+\s((\d+\.){3}\d+)/')

netscr_intf_ip_v4 = re.compile(
  r'\sinterface\s(\S+)\s(manage-)?ip\s((\d+\.){3}\d+(\/\d+)?)')

# 90b1.1c46.a51d
mac_addr_dot = re.compile(r'((\w{4})\.(\w{4})\.(\w{4}))')
# 90:b1:1c:46:a5:1d or 90 B1 1C 46 A5 1D
mac_addr_colon = re.compile(
  r'((\w{2})[: ](\w{2})[: ](\w{2})[: ](\w{2})[: ](\w{2})[: ](\w{2}))')


