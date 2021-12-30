#!/usr/bin/env python3

import argparse
import json
from os import path
from os import stat
from os import getenv
import sys
import time
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

All data is pulled from Rancid backups.  The first time you run the script it
could take up to one minute to parse all the necessary configs.  That data will
be written to ~/.conn_subnets.json.  This file will be used for each subsequent
run of the script, greatly improving performance.

If your ~/.conn_subnets.json file is older than 24 hours, the script will
automatically refresh the data.  You can force a refresh of the data parsed from
the configs by deleting ~/.conn_subnets.json.

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
    conn_subnet_report.py --regex='*edge*'
    conn_subnet_report.py --priv --dir='/tmp/configs/'

The script will write a json file of data to the current directory which will be
used for subsequent runs of the script to improve performance.  This data will be
refreshed if the timestamp is more than 24 hours old.
      '''))
parser.add_argument(
  "--pub", help="Find public IP addresses.", action="store_true")
parser.add_argument(
  "--priv", help="Find private IP addresses.", action="store_true")
parser.add_argument(
  "--dir", help="Alternate directory where network host configs are located.")
parser.add_argument(
  "--regex", help="Limit to specific hostnames.")

userhome = getenv('HOME')
subnet_json = '/'.join([userhome, '.conn_subnets.json'])

args = parser.parse_args()

if not args.priv and not args.pub:
    all_ip = True
else:
    all_ip = False

if args.dir:
    conf_dir = args.dir
else:
    conf_dir = flib.get_conf_dir()

# glob everything if no regex provided
if not args.regex:
    regex = '*'
else:
    regex = args.regex

# the ipaddress module does not count this as private, but I would like to
cgnat_net = ipaddress.ip_network('100.64.0.0/10')

def pull_from_configs():
    strip_domain = '.example.net'
    configs = flib.get_config_list(conf_dir, regex)
    if len(configs) == 0:
        print("No configs found.")
    ip_dict = {}
    for hostname, conf_path, platform in configs:
        hostname = hostname.replace(strip_domain, '')
        config_lines = []
        with open(conf_path, encoding='utf-8') as fh:
            config_lines = fh.readlines()
        host_ip_dict = {hostname: {}}
        E = enumerate(config_lines)
        parse.parse_any(hostname, platform, E, host_ip_dict) 
        ip_dict.update(host_ip_dict)
    return ip_dict

def refresh_data():
    ip_dict = pull_from_configs()
    # only write the file if no regex was provided and it's a full dump
    if not args.regex:
        with open(subnet_json, 'wt') as f:
            f.write(json.dumps(ip_dict))
    return ip_dict

if not path.isfile(subnet_json):
    ip_dict = refresh_data()
else:
    delta = time.time() - path.getctime(subnet_json)
    #          one day
    if delta > 86400:
        ip_dict = refresh_data()
    else:
        with open(subnet_json, 'rt') as f:
            ip_dict = json.load(f)    

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
