#!/usr/bin/env python3

map = {
    'dot1dBasePortIfIndex': '1.3.6.1.2.1.17.1.4.1.2',
    'BaseMappingPort': '1.3.6.1.4.1.9.9.276.1.5.1.1.1',
    'bgpLocalAs': '1.3.6.1.2.1.15.2',
    # append prefix.mask (e.g., 0.0.0.0.0) to query paths
    'bgp4PathAttrPeer': '1.3.6.1.2.1.15.6.1.1',
    'bgpPeerState': '1.3.6.1.2.1.15.3.1.2',
    'bgpPeerAdminStatus': '1.3.6.1.2.1.15.3.1.3',
    'bgpPeerRemoteAddr': '1.3.6.1.2.1.15.3.1.7',
    'bgpPeerHoldTime': '1.3.6.1.2.1.15.3.1.18',
    'bgpPeerKeepAlive': '1.3.6.1.2.1.15.3.1.19',
    'bgpPeerHoldTimeConfigured': '1.3.6.1.2.1.15.3.1.20',
    'bgpPeerKeepAliveConfigured': '1.3.6.1.2.1.15.3.1.21',
    'cdpGlobalRun': '1.3.6.1.4.1.9.9.23.1.3.1',
    'cdpCacheDevicePort': '1.3.6.1.4.1.9.9.23.1.2.1.1.7',
    'cdpCacheDeviceId': '1.3.6.1.4.1.9.9.23.1.2.1.1.6',
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysUpTime': '1.3.6.1.2.1.1.3',
    'uptime': '1.3.6.1.2.1.1.3',                          # alias
    'lldp_ifindex': '1.0.8802.1.1.2.1.3.7.1.3',           # doesn't work on mx
    'lldp_neighbor': '1.0.8802.1.1.2.1.4.1.1.9',
    'lldp_neighbor_intf': '1.0.8802.1.1.2.1.4.1.1.7',
    'ipAdEntNetMask': '1.3.6.1.2.1.4.20.1.3',             # connected intfs
    'ipCidrRouteProto': '1.3.6.1.2.1.4.24.4.1.7',         # routing table
    # ipCidrRouteProto INTEGER key -> 2 : local; 13 : ospf; 14 : bgp
    'ipNetToPhysicalPhysAddress': '1.3.6.1.2.1.4.35.1.4', # ARP current
    'ipNetToMediaPhysAddress': '1.3.6.1.2.1.4.22.1.2',    # ARP deprecated
    'ifName': '1.3.6.1.2.1.31.1.1.1.1',
    'ifAlias': '1.3.6.1.2.1.31.1.1.1.18',		  # description on intf
    'mx_mem': '1.3.6.1.4.1.2636.3.1.13.1.11.9.1.0.0',
    'nxos_ser_num': '1.3.6.1.2.1.47.1.1.1.1.11.10',
    'ios_ser_num': '1.3.6.1.2.1.47.1.1.1.1.11',
    'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
    'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
    'ifHCInOctets': '1.3.6.1.2.1.31.1.1.1.6',
    'ifHCInUcastPkts': '1.3.6.1.2.1.31.1.1.1.7',
    'ifHighSpeed': '1.3.6.1.2.1.31.1.1.1.15',             # + ifindex
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14',                 # + ifindex
    'ipAddressIfIndex': '1.3.6.1.2.1.4.34.1.3',           # + ifindex
    'ipAddressPrefix': '1.3.6.1.2.1.4.34.1.5',            # + ifindex
    'snmpEngineTime': '1.3.6.1.6.3.10.2.1.3.0',
    'snmpuptime':     '1.3.6.1.6.3.10.2.1.3.0',           # > sysUpTime
    'vlan_list': '1.3.6.1.4.1.9.9.46.1.3.1.1.4.1',
    'vlan_mac_port': '1.3.6.1.2.1.17.4.3.1.2',
}
