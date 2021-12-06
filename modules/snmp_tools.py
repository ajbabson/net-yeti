#!/bin/env python3

import collections
import ipaddress
import re, time
import subprocess as sub
import oids

def snmpget(hostname, oid, snmp_comm):
    '''
    Makes an snmpget call to the specified host with the specified OID and
    returns the SNMP response.
    '''
    #print('Running snmpget -v2c -c {0} {1} {2}'.format(
    #  snmp_comm, host, oid))
    try:
        snmp_data = sub.check_output(['/usr/bin/snmpget', '-v2c', '-c', \
          snmp_comm, hostname, oid], universal_newlines=True)
        if (snmp_data):
            return snmp_data
        else:
            print('No data received from snmpget.')
            return None
    except:
        print('No response from snmpget command.')
        return None

def snmpbulkwalk(host, oid, snmp_comm, vlan_num=False, split=False):
    '''
    Makes an snmpbulkwalk call to the specified host with the specified OID and
    returns the SNMP response.
    '''
    if vlan_num:
        snmp_comm = '{0}@{1}'.format(snmp_comm, vlan_num)
    #print('Running snmpbulkwalk -v2c -c {0} {1} {2}'.format(
    #  snmp_comm, host, oid))
    try:
        snmp_data = sub.check_output(['/usr/bin/snmpbulkwalk','-v2c','-c',
          snmp_comm, host, oid], universal_newlines=True)
        if (snmp_data):
            if split == True:
                snmp_data = snmp_data.split('\n')
            return snmp_data
        else:
            print('No data received from snmpbulkwalk.')
            return None
    except:
        print('No response from snmpbulkwalk command for {0}.'.format(oid))
        return None

def convert_mac(mac):
    '''
    Converts '90 B1 1C 46 A5 1D' to '90b1.1c46.a51d'.
    '''
    hex_nums = mac.lower().split()
    hex_chunk1 = ''.join(hex_nums[0:2])
    hex_chunk2 = ''.join(hex_nums[2:4])
    hex_chunk3 = ''.join(hex_nums[4:])   
    hex_mac = '.'.join([hex_chunk1, hex_chunk2, hex_chunk3])
    return hex_mac

def dec_to_hex_mac(decimal_mac):
    '''
    Some SNMP OIDs return MAC addresses in decimal format.  This function will
    take a MAC address in decimal format and convert it to hexadecimal.  The
    leading '.' will be removed if passed in the argument.

    iso.3.6.1.2.1.17.4.3.1.2.0.80.86.149.64.110 = INTEGER: 3

    >>> snmp.dec_to_hex_mac('.0.80.86.149.64.110')
    '0050.5695.406e'

    '''
    if decimal_mac.startswith('.'):
        decimal_mac = decimal_mac[1:]
    decimal_mac = decimal_mac.split('.')
    if len(decimal_mac) > 6:
        print("Got more decimals than expected for a MAC address.")
        print("Only rightmost six decimal values will be used.")
        decimal_mac = decimal_mac[-6:]
    hex_nums = []
    for num in decimal_mac:
        hex_num = hex(int(num))[2:]
        if len(hex_num) < 2:
            hex_num = '0' + hex_num
        hex_nums.append(hex_num)
    hex_chunk1 = ''.join(hex_nums[0:2])
    hex_chunk2 = ''.join(hex_nums[2:4])
    hex_chunk3 = ''.join(hex_nums[4:])
    hex_mac = '.'.join([hex_chunk1, hex_chunk2, hex_chunk3])
    return hex_mac

def get_arp_table(arp_hosts, snmp_comm):
    '''
    Takes a list of hosts and returns a dictionary of mac address to IP address
    mappings.  Even a single host must be provided as a single-element list.

    All IP/MAC key/value entries are merged into the dictionary with no mention
    of which hostname they came from.  Only a single IP address per MAC can be
    stored which could lose some data for MAC addresses that have multiple IP
    addresses.  If this is a concern, use get_arp_ip_list instead.

    {'0024.3876.4e80': '192.168.254.71', 'f025.7294.afc2': '10.102.23.250'}
    '''
    # deprecated but works on cisco and juniper
    oid = oids.map['ipNetToMediaPhysAddress']
    arp_table = {}
    for host in arp_hosts:
        snmp_data = snmpbulkwalk(host, oid, snmp_comm)
        if snmp_data is None:
            return None
        else:
            snmp_data = snmp_data.split('\n')
            # .2.1.4.22.1.2.25.10.102.25.12 = Hex-STRING: 00 0C 29 00 7E 81
            re_arp = re.compile(
              r'(\d+\.\d+\.\d+\.\d+)\s=\sHex-STRING:\s([\s\d\w]+)',
              re.IGNORECASE)
            for line in snmp_data:
                arp_match = re_arp.search(line)
                if(arp_match):
                    ip  = arp_match.group(1)
                    mac = arp_match.group(2)
                    converted_mac = convert_mac(mac)
                    arp_table[converted_mac] = ip
    return arp_table

def get_arp_ip_list(arp_hosts, snmp_comm):
    '''
    Takes a list of hosts and returns a dictionary of MAC address to IP address
    mappings.  Even a single host must be provided as a single-element list.

    The IP address value is a list which allows multiple IP addresses per MAC
    address.

    {'0015.5d29.3e44': ['10.115.41.142'],
     'bc30.5bf4.e038': ['10.118.0.5', '10.118.0.7']}
    '''
    # deprecated but works on cisco and juniper
    oid = oids.map['ipNetToMediaPhysAddress']
    arp_table = {}
    for host in arp_hosts:
        snmp_data = snmpbulkwalk(host, oid, snmp_comm)
        if snmp_data is None:
            return None
        else:
            snmp_data = snmp_data.split('\n')
            # .2.1.4.22.1.2.25.10.102.25.12 = Hex-STRING: 00 0C 29 00 7E 81
            re_arp = re.compile(
              r'(\d+\.\d+\.\d+\.\d+)\s=\sHex-STRING:\s([\s\d\w]+)',
              re.IGNORECASE)
            for line in snmp_data:
                arp_match = re_arp.search(line)
                if(arp_match):
                    ip  = arp_match.group(1)
                    mac = arp_match.group(2)
                    converted_mac = convert_mac(mac)
                    if converted_mac in arp_table.keys():
                        if ip in arp_table[converted_mac]:
                            continue
                        else:
                            arp_table[converted_mac].append(ip)
                    else:
                        arp_table[converted_mac] = [ip]
    return arp_table

def get_bgp_ipv4_peers(hostname, snmp_comm):
    '''
    IOS, IOS-XE, JunOS
    Returns a dictionary where the keys are the IPv4 addresses of all BGP peers.
    The Values are all set to None. This is so that BGP peer objects or any
    other data can later be assigned as values if desired.

    {'172.29.2.25': None, '172.29.1.22': None, '172.29.2.29': None}
    '''
    bgp_ipv4_peers = {}
    oid = oids.map['bgpPeerRemoteAddr']
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    snmp_data = snmp_data.rstrip().split('\n')
    for data in snmp_data:
        peer = data.split(' ')[-1].rstrip()
        # Assign None value to key; the netlib module uses this dictionary to
        # store BGP peer objects
        bgp_ipv4_peers[peer] = None
    return bgp_ipv4_peers

def get_bgp_ipv4_peer_status(hostname, peer_addr, snmp_comm):
    '''
    Takes a hostname and peer address (as a string), and returns a dictionary
    with two keys, 'state' and 'admin'. Possible values for 'state' are 'idle',
    'connect', 'active', 'opensent', 'openconfirm', and 'established'. Possiblew
    values for 'admin' are 'shut' and 'up'.

    {'state': 'established', 'admin': 'up'}
    '''
    bgp_state_map = {
        '1': 'idle',
        '2': 'connect',
        '3': 'active',
        '4': 'opensent',
        '5': 'openconfirm',
        '6': 'established',
    }
    bgp_admin_map = {
        '1': 'shut',
        '2': 'up',
    }
    ipv4_peer_status = {}
    oid = oids.map['bgpPeerState'] + '.' + peer_addr
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    result = snmp_data.split(' ')[-1].rstrip()
    ipv4_peer_status['state'] = bgp_state_map[result]
    oid = oids.map['bgpPeerAdminStatus'] + '.' + peer_addr
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    result = snmp_data.split(' ')[-1].rstrip()
    ipv4_peer_status['admin'] = bgp_admin_map[result]
    return ipv4_peer_status

def get_routes(hostname, protocol, snmp_comm):
    '''
    IOS only

    Results for JunOS are somewhat inconsistent.  Better to use salt or PyEZ:
     sudo salt -s -G 'os:junos' napalm.rpc get-route-information protocol=direct
    Then use 'get_junos_routes.py' to parse the output.

    Takes a hostname and routing protocol and returns a list of IPv4Network
    objects.

    Possible protocol values are 'connected', 'static', 'ospf', and 'bgp'.

    ***** Run this on a host with a full BGP table at your OWN RISK. *****

    [IPv4Network('0.0.0.0/0'), IPv4Network('10.251.1.0/24'),...
    '''
    prefixes = []
    proto_map = {
        '2': 'connected',
        '3': 'static',
        '13': 'ospf',
        '14': 'bgp'
    }
    oid = oids.map['ipCidrRouteProto']
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    if snmp_data is None:
        return None, None
    else:
        snmp_data = snmp_data.split('\n')
    # ...1.2.1.4.24.4.1.7.192.168.25.0.255.255.255.0.0.172.30.2.2 = INTEGER: 14
    re_route = re.compile(
      r'((\d+\.){3}\d+)\.((\d+\.){3}\d+)\.0\.(\d+\.){3}\d+\s=\sINTEGER:\s(\d+)')
    for line in snmp_data:
        route_match = re_route.search(line)
        if(route_match):
            network = route_match.group(1)
            netmask = route_match.group(3)
            proto_num = route_match.group(6)
            if proto_map[proto_num] == protocol:
                prefix = '/'.join([network, netmask])
                prefix_obj = ipaddress.ip_network(prefix)
                prefixes.append(prefix_obj)
    return prefixes

def get_cdp_data(hostname, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE
    Returns a dictionary where the key values are local interface names and the
    values are a tuple containing the CDP neighbor hostname and neighbor
    interface.

    {'gi1/0/1': ('lf-01.foo.example.net', 'gi1/0/23'),....
    '''
    cdp_data = {}
    cdp_run_oid   = oids.map['cdpGlobalRun']
    cdp_nei_oid   = oids.map['cdpCacheDeviceId']
    cdp_ports_oid = oids.map['cdpCacheDevicePort']
    intf_name_oid = oids.map['ifName']
    cdp_run_status = snmpbulkwalk(hostname, cdp_run_oid, snmp_comm, split=True)
    assert cdp_run_status != None
    if cdp_run_status[0].endswith('INTEGER: 1'):
        #print('cdp enabled!', hostname)
        pass
    else:
        print('{0} does not appear to support CDP.'.format(hostname))
        return False
    cdp_nei_data = snmpbulkwalk(hostname, cdp_nei_oid, snmp_comm, split=True)
    re_cdp_nei   = re.compile(r'(\d+\.\d+)\s=\sSTRING:\s"(\S+)"')
    re_cdp_intf  = re.compile(r'\s=\sSTRING:\s"(\S+)"')
    re_intf_name = re.compile(r'\s=\sSTRING:\s"(\S+)"')
    for line in cdp_nei_data:
        cdp_nei_match = re_cdp_nei.search(line)
        if cdp_nei_match:
            cdp_idx = cdp_nei_match.group(1)
            cdp_nei = cdp_nei_match.group(2)
            cdp_nei_intf_oid = '.'.join([cdp_ports_oid, cdp_idx])
            cdp_intf_data = snmpbulkwalk(
              hostname, cdp_nei_intf_oid, snmp_comm, split=True)
            cdp_intf_match = re_cdp_intf.search(cdp_intf_data[0])
            if cdp_intf_match:
                cdp_intf = cdp_intf_match.group(1).replace(
                  'GigabitEthernet', 'gi')
            intf_idx = cdp_idx.split('.')[0]
            intf_oid = '.'.join([intf_name_oid, intf_idx])
            intf_name_data = snmpbulkwalk(
              hostname, intf_oid, snmp_comm, split=True)
            intf_name_match = re_intf_name.search(intf_name_data[0])
            if intf_name_match:
                intf_name = intf_name_match.group(1).lower()
            cdp_data[intf_name] = (cdp_nei, cdp_intf)
    return cdp_data

def get_intf_maps(hostname, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Takes a hostname and returns two OrderedDict dictionaries, allowing easy
    conversion between interface names and index numbers.

    Cisco IOS:
    >>> intf_name_map, intf_index_map = get_intf_maps(hostname, snmp_comm)
    >>> intf_id_map['et1/1']
    '436207616'
    >>> intf_name_map['436207616'] 
    'ethernet1/1'

    Juniper example dictionaries:

    (OrderedDict([('fxp0', '1'),...('reth0.4050', '584'),...
    (OrderedDict([('1', 'fxp0'),...('584', 'reth0.4050'),...
    '''
    oid = oids.map['ifName']
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    if snmp_data is None:
        return None, None
    else:
        snmp_data = snmp_data.split('\n')
        intf_name_map = collections.OrderedDict()
        intf_id_map = collections.OrderedDict()
        re_intf_id = re.compile(
          r'\.(\d+)\s=\sSTRING:\s(\S+)', re.IGNORECASE)
        for line in snmp_data:
            intf_id_match = re_intf_id.search(line)
            if(intf_id_match):
                intf_id = intf_id_match.group(1)
                intf_name = intf_id_match.group(2)
                if intf_name.startswith('"') and intf_name.endswith('"'):
                    intf_name = intf_name[1:-1]
                # for our Nexus friends
                if 'Ethernet' in intf_name:
                    intf_parts = intf_name.split('hernet')
                    intf_name = ''.join(intf_parts)
                intf_name_map[intf_id] = intf_name.lower()
                intf_id_map[intf_name.lower()] = intf_id
        return intf_name_map, intf_id_map

def get_serial_num(hostname, snmp_comm, software=False):
    '''
    IOS, NX-OS

    Returns the serial number for IOS and NX-OS network hosts. The 'software'
    can be passed as 'ios' or 'nxos', otherwise an additional SNMP call will be
    made to determine the system type.
    '''
    if software == False:
        software = get_sysinfo(hostname, snmp_comm)[3]
    if software == 'nxos':
        snmp_data = snmpget(
          hostname, oids.map['nxos_ser_num'], snmp_comm)
        snmp_data = snmp_data.split('"')
        serial_num = snmp_data[-2]
    elif software == 'ios':
        snmp_data = snmpbulkwalk(
          hostname, oids.map['ios_ser_num'], snmp_comm)
        serial_num = snmp_data.split('STRING: ')[1].splitlines()[0]
        serial_num = serial_num.strip('"')
    return serial_num

def get_sysinfo(hostname, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Returns four strings: the configured hostname, hardware platform, software
    version, and software type. Possible software types are 'eos', 'nxos',
    'iosxe', and 'junos'.

    ('ifc-fw-01', 'srx550 internet router', '12.3X48-D30.7', 'junos')
    '''
    try:
        snmp_data = snmpget(hostname, oids.map['sysDescr'], snmp_comm)
    except:
        print('Unable to get snmp data.')
        return None, None, None, None
    if ('Cisco NX-OS' in snmp_data):
        platform = snmp_data.split('STRING: ')[1].split(',')[0]
        version = snmp_data.split('ersion ')[1].split(',')[0]
        software = 'nxos'
    elif ('Cisco IOS' in snmp_data):
        platform = snmp_data.split('STRING: ')[1].split(',')[0].lstrip('"')
        version = snmp_data.split('ersion ')[1].split(',')[0]
        software = 'ios'
    elif ('IOS-XE' in snmp_data):
        # SNMPv2-MIB::sysDescr.0 = STRING: Cisco IOS Software, IOS-XE Software,
        # Catalyst 4500 L3 Switch  Software (cat4500e-UNIVERSALK9-M), Version
        # 03.07.00.E RELEASE SOFTWARE (fc4)
        iosxe_match = re_version_iosxe.search(snmp_data)
        if iosxe_match:
            platform = iosxe_match.group(1)
            version = iosxe_match.group(2)
        software = 'iosxe'
    elif ('Juniper' in snmp_data):
        platform = snmp_data.split('Inc. ')[1].split(',')[0]
        version = snmp_data.split('JUNOS ')[1].split(',')[0]
        software = 'junos'
    else:
        return False
    snmp_data = snmpget(hostname, oids.map['sysName'], snmp_comm)
    sysname = snmp_data.rstrip().split(' ')[-1].lower()
    if sysname.startswith('"') and sysname.endswith('"'):
        sysname = sysname[1:-1]
    sysname = sysname.split('.')[0]
    if (sysname != hostname):
        print(
          'Warning! "{0}" does not match sysName query result: "{1}"'.format(
          hostname, sysname))
    return sysname, platform, version, software

def get_uptime(hostname, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS
    Returns the system uptime and SNMP engine uptime as a tuple.  Accuracy of
    the data is not always consistent, so the value of this function is
    questionable.
    '''
    oid1 = oids.map['sysUpTime']
    oid2 = oids.map['snmpEngineTime']
    snmp_data = snmpbulkwalk(hostname, oid1, snmp_comm)
    snmp_data = snmp_data.rstrip().split(' ')
    sysuptime = ' '.join(snmp_data[-3:])
    snmp_data = snmpbulkwalk(hostname, oid2, snmp_comm)
    seconds = int(snmp_data.split('INTEGER: ')[1].rstrip())
    days = seconds // 86400
    seconds_remain = seconds % 86400
    hours = seconds_remain // 3600
    if hours < 10:
        hours = '0' + str(hours)
    seconds_remain = seconds_remain % 3600
    minutes = seconds_remain  // 60
    if minutes < 10:
        minutes = '0' + str(minutes)
    seconds = seconds_remain % 60
    if seconds < 10:
        seconds = '0' + str(seconds)
    snmpuptime = '{0} {1}, {2}:{3}:{4}'.format(
      days, 'days', hours, minutes, seconds)
    return (sysuptime, snmpuptime)

def get_vlan_list(hostname, snmp_comm):
    '''
    IOS, NX-OS
    Returns two dictionaries, a mapping of vlan numbers to names and a mapping
    of vlan names to numbers.  Ignores reserved VLANs 1002-1005.

    {'4038': '"X:172.31.251.0/29:LB_INTERCO_DMZ"',...}
    {'"X:172.31.251.0/29:LB_INTERCO_DMZ"': '4038',,...}
    '''
    oid = oids.map['vlan_list']
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    vlan_names = {}
    ignore_list = ['1002', '1003', '1004', '1005']
    if snmp_data is None:
        return None, None
    else:
        snmp_data = snmp_data.split('\n')
        re_vlan = re.compile(r'\.(\d+)\s=\sSTRING:\s(\S+)', re.IGNORECASE)
        for line in snmp_data:
            vlan_match = re_vlan.search(line)
            if(vlan_match):
                vlan_num  = str(vlan_match.group(1))
                if vlan_num in ignore_list:
                    continue
                vlan_name = str(vlan_match.group(2))
                vlan_names[vlan_name] = vlan_num
        vlan_nums = {v: k for k, v in vlan_names.items()}
        return vlan_nums, vlan_names

def get_vlan_mac_port(hostname, vlan_num, snmp_comm):
    '''
    Takes a hostname and VLAN number and searches for all MAC addresses in the
    VLAN.  For each MAC address found within the VLAN, add a dictionary key
    equal to the port ID where the MAC was found and append the a tuple of the
    the MAC address and VLAN number to the value which is a list.  Return the
    dictionary.

    For example, in VLAN 4038 two MAC addresses were found, one on port ID 3 and
    one on port ID 13.
    {'13': [('0010.dbff.4000', 4038)], '3': [('0050.5695.406e', 4038)]}

    Do not confuse the port ID with the ifindex.

    aubcore01#sh mac address-table dynamic vlan 4038
          Mac Address Table
    -------------------------------------------

    Vlan    Mac Address       Type        Ports
    ----    -----------       --------    -----
    4038    0010.dbff.4000    DYNAMIC     Gi1/0/13 <---
    4038    0050.5695.406e    DYNAMIC     Gi1/0/3  <---
    Total Mac Addresses for this criterion: 2

    '''
    vlan_num = str(vlan_num)
    oid = oids.map['vlan_mac_port']
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm, vlan_num)
    vlan_mac_ports = {}
    if snmp_data is None:
        return None, None
    else:
        snmp_data = snmp_data.split('\n')
        re_vlan_mac_port = re.compile(
          r'((\.\d+){6})\s=\sINTEGER:\s(\d+)', re.IGNORECASE)
        for line in snmp_data:
            vlan_mac_port_match = re_vlan_mac_port.search(line)
            if(vlan_mac_port_match):
                decimal_mac = vlan_mac_port_match.group(1)
                port_id     = vlan_mac_port_match.group(3)
                hex_mac = dec_to_hex_mac(decimal_mac)
                mac_vlan = (hex_mac, vlan_num)
                try:
                    vlan_mac_ports[port_id].append(mac_vlan)
                except:
                    vlan_mac_ports[port_id] = [mac_vlan]
        return vlan_mac_ports

def get_base_ports(hostname, snmp_comm):
    '''
    Returns a dictionary of port ID to ifindex key/value mappings.

    {'14': '10114', '17': '10117', '30': '10202',...}
    '''
    base_ports = {}
    oid = oids.map['BaseMappingPort']
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    snmp_data = snmp_data.split('\n')
    # iso.3.6.1.4.1.9.9.276.1.5.1.1.1.10116 = INTEGER: 16
    re_base_port= re.compile(r'\.(\d+)\s=\sINTEGER:\s(\d+)')
    for line in snmp_data:
        base_port_match = re_base_port.search(line)
        if base_port_match:
            intf_base_port = base_port_match.group(1)
            intf_integer   = base_port_match.group(2)
            base_ports[intf_integer] = intf_base_port
    return base_ports

# need to optimize this to only return CIDR which can then be split if needed
#{'1000101': {'ipv4': ('10.234.194.12', '31', '10.234.194.12/31'), 'ipv6':
#('2a01:0111:0000:106a:00b7:0000:0000:0000', '126',

def get_all_intf_status(hostname, snmp_comm):
    '''
    IOS, NX-OX, IOS-XE, JunOS

    Returns a dictionary where the keys are ifindices and the value is a
    dictionary containing two key/value pairs: 'admin' and 'link'.  The possible
    values are up and down.

    {'10103': {'admin': 'up', 'link': 'up'},...}
    '''
    intf_index_status = {}
    def get_status(oid_name, intf_index_status):
        if 'Admin' in oid_name:
            status = 'admin'
        elif 'Oper' in oid_name:
            status = 'link'
        else:
            raise ValueError('OID name must be ifAdminStatus or ifOperStatus.')
        oid = oids.map[oid_name]
        snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
        snmp_data = snmp_data.split('\n')
        # iso.3.6.1.2.1.2.2.1.7.10117 = INTEGER: 1
        re_intf_status = re.compile(r'\.(\d+)\s=\sINTEGER:\s(\d+)')
        for line in snmp_data:
            intf_status_match = re_intf_status.search(line)
            if intf_status_match:
                intf_index = str(intf_status_match.group(1))
                intf_status = int(intf_status_match.group(2))
                if (intf_status == 1):
                    intf_status = 'up'
                elif (intf_status == 2):
                    intf_status = 'down'
                elif (intf_status == 6):
                    intf_status = 'empty'
                try:
                    intf_index_status[intf_index][status] = intf_status
                except Exception as e:
                    intf_index_status[intf_index] = {status: intf_status}
        #return intf_index_status
    for oid_name in ['ifAdminStatus', 'ifOperStatus']:
        get_status(oid_name, intf_index_status)
    return intf_index_status

def get_intf_status(hostname, intf_index, option, snmp_comm):
    '''
    IOS, NX-OX, IOS-XE, JunOS

    Takes the ifindex and an option of 'admin' or 'oper' and returns either the
    admin or operating (protocol) status of the interface.
    '''
    if (option == 'admin'):
        oid = oids.map['ifAdminStatus'] + '.' + intf_index
    elif (option == 'oper'):
        oid = oids.map['ifOperStatus'] + '.' + intf_index
    snmp_data = snmpget(hostname, oid, snmp_comm)
    status = int(snmp_data.split()[-1])
    if (status == 1):
        intf_status = 'up'
    elif (status == 2):
        intf_status = 'down'
    elif (status == 6):
        intf_status = 'empty'
    else: 
        intf_status = status
    return intf_status

def get_intf_desc(hostname, intf_index, snmp_comm):
    '''
    Takes the interface index and returns the interface description for the
    interface.
    '''
    oid = oids.map['ifAlias'] + '.' + intf_index
    snmp_data = snmpget(hostname, oid, snmp_comm)
    intf_desc = snmp_data.split(' ')[-1].rstrip()
    if intf_desc.startswith('"') and intf_desc.endswith('"'):
        intf_desc = intf_desc[1:-1]
    return intf_desc

def get_all_intf_desc(hostname, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Returns a dictionary of interface descriptions for all interfaces where the
    key/value pairs are ifindex/description.

    {'10103': 'Q:lf-01:Gi0/47', '10128': 'NO_DESC',...}

    If the description is empty then the value is set to NO_DESC.
    '''
    oid = oids.map['ifAlias']
    intf_index_desc = {}
    snmp_data = snmpbulkwalk(hostname, oid, snmp_comm)
    snmp_data = snmp_data.split('\n')
    # iso.3.6.1.2.1.31.1.1.1.18.10119 = STRING: "IMG DATA0"
    # iso.3.6.1.2.1.31.1.1.1.18.10107 = ""
    re_intf_desc = re.compile(r'\.(\d+)\s=\s(STRING:\s)?(.+)')
    for line in snmp_data:
        intf_desc_match = re_intf_desc.search(line)
        if intf_desc_match:
            intf_index = intf_desc_match.group(1)
            intf_desc  = intf_desc_match.group(3)
            if intf_desc.startswith('"') and intf_desc.endswith('"'):
                intf_desc = intf_desc[1:-1]
                if len(intf_desc) == 0:
                    intf_desc = 'NO_DESC'
            else:
                intf_desc = None
            intf_index_desc[intf_index] = intf_desc
    return intf_index_desc

def get_intf_input_octets(hostname, intf_index, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Takes the hostname and ifindex and returns the value of the interface's
    input throughput counter in octets of data.
    '''
    input_octets_oid = (oids.map['ifHCInOctets'] + '.' + intf_index)
    result = snmpget(hostname, input_octets_oid, snmp_comm)
    input_octets = int(result.split(' ')[-1].rstrip())
    return input_octets

def get_intf_input_ucast_pkt(hostname, intf_index, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Takes the hostname and ifindex and returns the value of the interface's
    input counter value.
    '''
    input_ucast_packets_oid = (oids.map['ifHCInUcastPkts'] + '.' + intf_index)
    result = snmpget(hostname, input_ucast_packets_oid, snmp_comm)
    input_ucast_packets = int(result.split(' ')[-1].rstrip())
    return input_ucast_packets

def get_intf_input_errors(hostname, intf_index, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Takes the hostname and ifindex of an interface and returns the input error
    counter value.
    '''
    input_octets_oid = (oids.map['ifInErrors'] + '.' + intf_index)
    result = snmpget(hostname, input_octets_oid, snmp_comm)
    input_errors = int(result.split(' ')[-1].rstrip())
    return input_errors

def get_intf_input_counters(hostname, intf_index, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Takes a hostname and ifindex and returns a dictionary with the hostname as
    the single key and a value of nested dictionaries.  The first nested
    dictionary has a key of the ifindex and its value is the next nested
    dictionary whose keys are the name of the OID that was polled and the value
    is a tuple where the first value is the counter value returned by the host
    and the second value is the time the value was received.

    >>> snmp.get_input_counters(hostname, intf_index, snmp_comm)
   {'aubcore01': {
      '10122': {
        'input_octets': (1666051390163, 1594107846.9434793),
        'input_errors': (16, 1594107847.3509867),
        'input_packets': (7165406182, 1594107847.1457753)}}}
    '''
    counter_data = {}
    counter_data[hostname] = {}
    input_octets = get_intf_input_octets(hostname, intf_index, snmp_comm)
    now = time.time()
    counter_data[hostname][intf_index] = {'input_octets': (input_octets, now)}
    input_packets = get_intf_input_ucast_pkt(hostname, intf_index, snmp_comm)
    now = time.time()
    data = {'input_packets': (input_packets, now)}
    counter_data[hostname][intf_index].update(data)
    input_errors = get_intf_input_errors(hostname, intf_index, snmp_comm)
    now = time.time()
    data = {'input_errors': (input_errors, now)}
    counter_data[hostname][intf_index].update(data)
    return counter_data

def get_intf_bw(hostname, intf_index, snmp_comm):
    '''
    IOS, NX-OS, IOS-XE, JunOS

    Takes a hostname and ifindex and returns the bandwidth of the interface in
    bits per second.  If the 'bandwidth' command is specified under the
    interface then this is the value that is returned, otherwise it is the
    default speed of the interface.
    '''
    oid = oids.map['ifHighSpeed'] + '.' + intf_index
    snmp_data = snmpget(hostname, oid, snmp_comm)
    intf_bw = snmp_data.rstrip().split()[-1]
    intf_bw = int(intf_bw) * 1000000
    return intf_bw

