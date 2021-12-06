#!/usr/bin/env python3

import argparse
import os
import sys
import ipaddress
sys.path.insert(0, '../')
import modules.filelib as flib
import modules.parsers as parse
import re

parser = argparse.ArgumentParser(
  formatter_class = argparse.RawDescriptionHelpFormatter,
  epilog = ('''\
Parse network hosts configurations and print a list of three columns consisting
of the hostname, interface, and connected subnet.

The script checks for the location of configs in the following order:

1. A path provided the --dir argument
2. A path provided in the environment variable $CONF_DIR
3. Default path is /var/rancid/all_configs/

By default, all IP addresses are printed.  You can limit the report with one of
the --pub and --priv options.

examples:
    conn_subnet_report.py
    conn_subnet_report.py --pub
    conn_subnet_report.py --priv
    conn_subnet_report.py --regex='*ams100*'
    conn_subnet_report.py --priv --dir='/tmp/configs/'

      '''))
parser.add_argument(
  "--pub", help="Find public IP addresses.", action="store_true")
parser.add_argument(
  "--priv", help="Find private IP addresses.", action="store_true")
parser.add_argument(
  "--dir", help="Alternate directory where network host configs are located.")
parser.add_argument(
  "--regex", help="Limit to specific hostnames.")

args = parser.parse_args()

if not args.priv and not args.pub:
    all_ip = True
else:
    all_ip = False

if args.dir:
    conf_dir = args.dir
else:
    conf_dir = os.environ.get('CONF_DIR')
    if conf_dir == None:
        conf_dir = '/var/rancid/all_configs/'

if not args.regex:
    regex = '*'
else:
    regex = args.regex

strip_domain = '.service-now.com'

configs = flib.get_config_list(conf_dir, regex)
ip_dict = {}

# for some reason the ipaddress module does not count this as private
cgnat_net = ipaddress.ip_network('100.64.0.0/10')

for hostname, conf_path, platform in configs:
    hostname = hostname.replace(strip_domain, '')
    config_lines = []
    with open(conf_path, encoding='utf-8') as fh:
        config_lines = fh.readlines()
    host_ip_dict = {hostname: {}}
    E = enumerate(config_lines)
    parse.parse_any(hostname, platform, E, host_ip_dict) 
    ip_dict.update(host_ip_dict)

for hostname, intfs in sorted(ip_dict.items()):
    for intf, ip_addrs in intfs.items():
        if len(ip_addrs) < 1:
            continue
        for (ip_addr, netmask) in ip_addrs:
           if re.search(r'(mgmt|hsrp|vrrp)', str(netmask)):
               continue
           subnet = '/'.join([ip_addr, str(netmask)])
           subnet_obj = ipaddress.ip_network(subnet, strict=False)
           if all_ip:
               print(hostname, intf, subnet_obj)
           elif subnet_obj.is_private and args.priv:
               print(hostname, intf, subnet_obj)
           elif subnet_obj.is_global and args.pub:
               print(hostname, intf, subnet_obj)
           elif subnet_obj.overlaps(cgnat_net) and args.priv:
               print(hostname, intf, subnet_obj)
           else:
               continue
               #print('skipping subnet {0}'.format(subnet_obj))

