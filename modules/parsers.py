#!/usr/bin/env python3

import re
import sys
import modules.shared_regex as rgx

def ios(hostname, E, host_ip_dict):
    def parse_intf(intf, E):
        intf_dict = {intf: []}
        while True:
            (num, line) = next(E)
            # standard ip address or secondary
            ios_intf_ip_v4_match = rgx.ios_intf_ip_v4.search(line)
            if ios_intf_ip_v4_match:
                ip_v4 = ios_intf_ip_v4_match.group(1)
                netmask = ios_intf_ip_v4_match.group(3)
                # convert from 255.255.255.x format to CIDR
                netmask = sum(bin(int(x)).count('1') for x in netmask.split('.'))
                netmask = str(netmask)
                intf_dict[intf].append((ip_v4, netmask))
            # hsrp
            nhrp_ip_v4_match = rgx.nhrp_ip_v4.search(line)
            if nhrp_ip_v4_match:
                nhrp_ip_v4 = nhrp_ip_v4_match.group(3)
                intf_dict[intf].append((nhrp_ip_v4, 'hsrp'))
            if re.search('^!?$', line):
                return intf_dict
    while True:
        try:
            (num, line) = next(E)
        except StopIteration as e:
            return host_ip_dict
        ios_intf_match = rgx.ios_intf.search(line)
        if ios_intf_match:
            # just take the first two letters
            intf_name = ios_intf_match.group(2)[:2].lower()
            intf_num = ios_intf_match.group(3)
            intf = ''.join([intf_name, intf_num])
            intf_dict = parse_intf(intf, E)
            host_ip_dict[hostname].update(intf_dict)

def nxos(hostname, E, host_ip_dict):
    def parse_intf(intf, E):
        intf_dict = {intf: []}
        while True:
            (num, line) = next(E)
            # standard ip address or secondary
            nxos_intf_ip_v4_match = rgx.nxos_intf_ip_v4.search(line)
            if nxos_intf_ip_v4_match:
                ip_v4, netmask = nxos_intf_ip_v4_match.group(1).split('/')
                intf_dict[intf].append((ip_v4, netmask))
            # no hsrp support at this time
            if re.search('^cli', line):
                return intf_dict
            if re.search('^\w?$', line):
                return intf_dict
    while True:
        try:
            (num, line) = next(E)
        except StopIteration as e:
            return host_ip_dict
        ios_intf_match = rgx.ios_intf.search(line)
        if ios_intf_match:
            # just take the first two letters
            intf_name = ios_intf_match.group(2)[:2].lower()
            intf_num = ios_intf_match.group(3)
            intf = ''.join([intf_name, intf_num])
            intf_dict = parse_intf(intf, E)
            host_ip_dict[hostname].update(intf_dict)

def junos(hostname, E, host_ip_dict):
    def parse_intfs(E):
        debug = False
        intfs_dict = {}
        while True:
            (num, line) = next(E)
            junos_intf_match = rgx.junos_intf.search(line)
            junos_irb_match  = re.search(r'\sirb\s{', line)
            junos_unit_match = re.search(r'\sunit\s(\d+)\s{', line)
            junos_intf_ip_v4_match = rgx.junos_intf_ip_v4.search(line)
            junos_vrrp_v4_match = rgx.junos_vrrp_v4.search(line)
            if junos_intf_match:
                intf = junos_intf_match.group(1)
                full_intf = intf
                intfs_dict[intf] = []
            elif junos_irb_match:
                intf = 'irb'
                full_intf = intf
                intfs_dict[intf] = []
            elif junos_unit_match:
                # sometimes units will be detected in member ranges that can be
                # ignored for now
                unit = junos_unit_match.group(1)
                try:
                    full_intf = '.'.join([intf, unit])
                except UnboundLocalError as e:
                    continue
                intfs_dict[full_intf] = []
            elif junos_intf_ip_v4_match:
                ip_v4, netmask = junos_intf_ip_v4_match.group(1).split('/')
                intfs_dict[full_intf].append((ip_v4, netmask))
            elif junos_vrrp_v4_match:
                vrrp_ip_v4 = junos_vrrp_v4_match.group(1)
                intfs_dict[full_intf].append((vrrp_ip_v4, 'vrrp'))
            elif re.search('^}$', line):
                return intfs_dict
    def parse_nodes(E, node):
        # yes, massively redundant to the parse_intfs function above but trying
        # to combine the two got too convoluted, so lesser of two evils...
        intfs_dict = {}
        while True:
            (num, line) = next(E)
            junos_intf_match = rgx.junos_intf.search(line)
            junos_unit_match = re.search(r'\sunit\s(\d+)\s{', line)
            junos_intf_ip_v4_match = rgx.junos_intf_ip_v4.search(line)
            if junos_intf_match:
                intf = junos_intf_match.group(1)
                full_intf = intf
                intfs_dict[intf] = []
            elif junos_unit_match:
                # sometimes units will be detected in member ranges that can be
                # ignored for now
                unit = junos_unit_match.group(1)
                full_intf = '.'.join([node, intf, unit])
                intfs_dict[full_intf] = []
            elif junos_intf_ip_v4_match:
                ip_v4, netmask = junos_intf_ip_v4_match.group(1).split('/')
                intfs_dict[full_intf].append((ip_v4, netmask))
            elif re.search('^\s\s\s\s}$', line):
                return intfs_dict
    while True:
        try:
            (num, line) = next(E)
        except StopIteration as e:
            return host_ip_dict
        if line.startswith('interfaces {'):
            intfs_dict = parse_intfs(E)
            host_ip_dict[hostname].update(intfs_dict)
        else:
            junos_node_match = rgx.junos_node.search(line)
            if junos_node_match:
                node = junos_node_match.group(1)
                while True:
                    (num, line) = next(E)
                    if 'interfaces {' in line:
                        intfs_dict = parse_nodes(E, node)
                        host_ip_dict[hostname].update(intfs_dict)
                        break                        

def netscr(hostname, E, host_ip_dict):
    while True:
        try:
            (num, line) = next(E)
        except StopIteration as e:
            return host_ip_dict
        netscr_intf_ip_v4_match = rgx.netscr_intf_ip_v4.search(line)
        if netscr_intf_ip_v4_match:
            intf = netscr_intf_ip_v4_match.group(1)
            is_mgmt_ip = netscr_intf_ip_v4_match.group(2)
            if is_mgmt_ip:
                intf = '-'.join([intf, 'mgmt'])
                ip_v4 = netscr_intf_ip_v4_match.group(3)
                netmask = 'mgmt'
            else:
                ip_v4, netmask = netscr_intf_ip_v4_match.group(3).split('/')
            host_ip_dict[hostname].update({intf: [(ip_v4, netmask)]})

def cumulus(hostname, E, host_ip_dict):
    def parse_intf(intf, E):
        intf_dict = {intf: []}
        while True:
            (num, line) = next(E)
            cumul_intf_ip_v4_match = rgx.cumul_intf_ip_v4.search(line)
            if cumul_intf_ip_v4_match:
                ip_v4, netmask = cumul_intf_ip_v4_match.group(1).split('/')
                intf_dict[intf].append((ip_v4, netmask))
            # vrrp
            cumul_vrrp_v4_match = rgx.cumul_vrrp_v4.search(line)
            if cumul_vrrp_v4_match:
                vrrp_ip_v4 = cumul_vrrp_v4_match.group(1)
                intf_dict[intf].append((vrrp_ip_v4, 'vrrp'))
            if re.search('^$', line):
                return intf_dict
    while True:
        try:
            (num, line) = next(E)
        except StopIteration as e:
            return host_ip_dict
        cumul_intf_match = rgx.cumul_intf.search(line)
        if cumul_intf_match:
            # just take the first two letters
            intf = cumul_intf_match.group(1)
            intf_dict = parse_intf(intf, E)
            host_ip_dict[hostname].update(intf_dict)

def parse_any(hostname, platform, E, host_ip_dict):
    if platform == 'cumulus':
        cumulus(hostname, E, host_ip_dict)
    if platform == 'juniper':
        junos(hostname, E, host_ip_dict)
    if platform == 'cisco':
        ios(hostname, E, host_ip_dict)
    if platform == 'cisco-nx':
        nxos(hostname, E, host_ip_dict)
    if platform == 'netscreen':
        netscr(hostname, E, host_ip_dict)
