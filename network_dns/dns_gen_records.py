#!/usr/bin/env python3

import argparse
import os,sys
import re
import sys
sys.path.insert(0, '../')
import modules.filelib as flib
import modules.parsers as parse
import ipdb

parser = argparse.ArgumentParser(
  formatter_class = argparse.RawDescriptionHelpFormatter,
  epilog = ('''\
Parse network hosts configurations and print BIND style reverse zone files
for RFC1918 IP addresses based on the following address classes:

a: 10.0.0.0/8
b: 172.16.0.0/12
c: 192.168.0.0/16
public: 185.37.220.0/22, 77.111.208.0/22, 192.206.95.0/24, 103.214.228.0/24

Network host configurations are parsed to obtain the IP address data so you must
provide a directory with a configuration file for each host you want to process.

The script checks for the location of configs in the following order:

1. A path provided the --dir argument
2. A path provided in the environment variable $CONF_DIR
3. A path provided in a file named ~/.conf_dir
4. Default path is ./configs/

The easiest is just to run the script while logged in to atlrancid01 and use the
default path.

Zone files will be written to the ./zones directory.

examples:
    dns_gen_records.py a
    dns_gen_records.py b
    dns_gen_records.py c --out
    dns_gen_records.py public

    dns_gen_records.py loop --dir='/home/me/configs/NETWORK/'

      '''))
parser.add_argument(
  "ptr_class", help="Which class of addresses to process: a, b, or c.")
parser.add_argument(
  "--dir", help="Alternate directory where network host configs are located.")
parser.add_argument("--out", help="Print to stdout.", action="store_true")

# records to manually add to zone files
zonedb_statics = ipdb.static_records.keys()

# zone files will be written here
if not os.path.isdir(ipdb.zone_dir):
    os.mkdir(ipdb.zone_dir)

# import zone definitions and initialize db_dict
db_dict = {}
for zonefile, ip_regex in ipdb.zones:
    db_dict[zonefile] = {'zone':  zonefile}

args = parser.parse_args()

# don't forget the trailing .
domain = 'foo.example.net.'

if args.dir:
    conf_dir = args.dir
else:
    conf_dir = flib.get_conf_dir()

def gen_reverse_zone(db_dict):
    zone = db_dict.pop('zone')
    if len(db_dict) == 0:
        print('No records found that match {0}.'.format(zone))
        return False
    print('writing', ipdb.zone_dir + zone)
    with open(ipdb.zone_dir + zone, 'wt') as fh:
        fh.write('{0}'.format(ipdb.soa))
        if zone in zonedb_statics:
            records = ipdb.static_records[zone]
            fh.write('{0}'.format(records))
        fh.write('\n; Auto-generated section - NETWORK\n')
        for ip_addr, records in sorted(db_dict.items()):
            octet1, octet2, octet3, octet4 = ip_addr.split('.')
            for record in records:
                # don't print netscreen -2 standby unless it's mgmt
                if not 'mgmt' in record:
                    match_pri = re.search(r'(\w+fw0\d)-1(.*)', record)
                    if match_pri:
                        record = match_pri.group(1) + match_pri.group(2)
                    elif re.search(r'fw0\d-2', record):
                        continue
                if len(zone.split('.')) == 2:
                    ptr = '.'.join([octet4, octet3, octet2])
                elif len(zone.split('.')) == 3:
                    ptr = '.'.join([octet4, octet3])
                elif len(zone.split('.')) == 4:
                    ptr = octet4
                host = '.'.join([record, domain])
                if args.out:
                    print('{0:<15}IN PTR    {1}'.format(ptr, host.lower()))
                fh.write('{0:<15}IN PTR    {1}\n'.format(ptr, host.lower()))

configs = flib.get_config_list(conf_dir)

ip_dict = {}

for hostname, conf_path, platform in configs:
    host_ip_dict = {hostname: {}}
    if os.path.isfile(conf_path):
        with open(conf_path, encoding='utf-8') as fh:
            config_lines = fh.readlines()
    else:
        print("Hmmm, {0} doesn't appear to be a file.".format(fullpath))
    E = enumerate(config_lines)
    parse.parse_any(hostname, platform, E, host_ip_dict) 
    ip_dict.update(host_ip_dict)

def update_dict(zonefile, hostname, intf, ip_addr, ip_mask):
    record = '-'.join([hostname, intf])
    record = re.sub('[./]', '-', record)
    if ip_mask == 'hsrp':
        record += '-hsrp'
    if ip_mask == 'vrrp':
        record += '-vrrp'
    try:
        db_dict[zonefile][ip_addr].append(record)
    except KeyError as e:
        db_dict[zonefile].update({ip_addr: [record]})

for hostname, intfs in ip_dict.items():
    for intf, ip_addrs in intfs.items():
        if len(ip_addrs) < 1:
            continue
        for (ip_addr, ip_mask) in ip_addrs:
            for zonefile, ip_regex in ipdb.zones:
                ip_match = ip_regex.search(ip_addr)
                if ip_match:
                    ip_range = ip_match.group(1)
                    update_dict(zonefile, hostname, intf, ip_addr, ip_mask)

if args.ptr_class == 'a':
    for zonedb, zonedata in db_dict.items():
        if re.search(r'^db\.10$', zonedb):
            gen_reverse_zone(db_dict[zonedb])
elif args.ptr_class == 'b':
    for zonedb, zonedata in db_dict.items():
        if re.search(r'^db\.172\.(1[6-9]|2[0-9]|3[01])$', zonedb):
            gen_reverse_zone(db_dict[zonedb])
elif args.ptr_class == 'c':
    for zonedb, zonedata in db_dict.items():
        if re.search(r'^db\.192\.168', zonedb):
            gen_reverse_zone(db_dict[zonedb])
elif args.ptr_class == 'public':
    for zonedb, zonedata in db_dict.items():
        if re.search(r'^db\.(10|192\.168)$', zonedb):
            continue
        elif re.search(r'^db\.172\.(1[6-9]|2[0-9]|3[01])$', zonedb):
            continue
        else:
            gen_reverse_zone(db_dict[zonedb])
elif args.ptr_class == 'all':
    for zonedb, zonedata in db_dict.items():
        gen_reverse_zone(db_dict[zonedb])
# hidden option - provide hostname and get a dump of IP info
elif ip_dict.get(args.ptr_class):
    print(ip_dict[args.ptr_class])
else:
    print('Sorry, try again.')

