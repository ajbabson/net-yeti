#!/usr/bin/env python3

import argparse
import json
import time
from os import getenv
from os import environ
from os import path
import sys
sys.path.insert(0, '../')
import modules.filelib as flib

parser = argparse.ArgumentParser(
  formatter_class = argparse.RawDescriptionHelpFormatter,
  epilog = ('''\
Retrieve information about Juniper models and OS versions from Rancid backups.
Any Rancid backup more than 10 days old is ignored.

With no arguments, a summary is provided of all platform and version
combinations, with a host count at the end of each (platform, version) tuple
and a grand total of all Juniper hosts at the end.

Use the model and version flags alone or in combination to extract granular
information, including hostnames.  The model and version arguments are treated
as regular expressions.

example:
   os_version_report.py
   os_version_report.py -v 14 (will match 14 anywhere in the code version)
   os_version_report.py -m 'mx[12]04'
   os_version_report.py -m qfx -v '14\.1'
   os_version_report.py --model qfx --version '17\.3R3'
   os_version_report.py --model qfx --version '17\.3R3.*\.3'
   os_version_report.py -m '(mx|qfx)' -v '14\.'
      '''))
parser.add_argument("-m", "--model", help="Hardware model to match")
parser.add_argument("-v", "--version", help="JunOS version to match")
parser.add_argument("--dir", help=
'''
Directory where configs are located.  This overrides the environmental
variable $CONF_DIR (checked first) and the default /var/rancid/all_configs/.
'''
)
args = parser.parse_args()

userhome = getenv('HOME')
os_json = '/'.join([userhome, '.os.json'])

if args.dir:
    conf_dir = args.dir
else:
    conf_dir = environ.get('CONF_DIR')
    if conf_dir == None:
        conf_dir = '/var/rancid/all_configs/'

def refresh_data():
    host_facts = flib.get_facts(conf_dir)
    with open(os_json, 'wt') as f:
        f.write(json.dumps(host_facts))
    return host_facts

if not path.isfile(os_json):
    host_facts = refresh_data()
else:
    delta = time.time() - path.getctime(os_json)
    #          one day
    if delta > 86400:
        host_facts = refresh_data()
    else:
        with open(os_json, 'rt') as f:
            host_facts = json.load(f)

fact_summary = {}
# ('qfx5100-96s-8q', '17.3R3-S7.2') 34
versions = {}
# 18.4R3-S1.3 [('edge01', 'mx10003'), ('edge02', 'mx10003')]
models = {}
# ex4200-48t [('12.3R5.7', 'mgmt01'), ('12.3R5.7', 'mgmt02')]

for k, v in host_facts.items():
    try:
        fact_summary[(v['model'], v['version'])] += 1
    except KeyError as e:
        fact_summary[(v['model'], v['version'])] = 1
    try:
        versions[v['version']].append((k, v['model']))
    except:
        versions[v['version']] = [(k, v['model'])]
    try:
        models[v['model']].append((v['version'], k))
    except:
        models[v['model']] = [(v['version'], k)]


if args.version and not args.model:
    for k, v in versions.items():
        if re.search(args.version, k):
            [ print('{0:<20} {1:<17} {2}'.format(host, model, k)) for host, model in v ]
elif args.model and not args.version:
    for k, v in models.items():
        if re.search(args.model.lower(), k):
            print('==========\n', k, '\n==========')
            [ print('{0:<20} {1}'.format(host, model)) for model, host in v ]
elif args.version and args.model:
    for k, v in versions.items():
        if re.search(args.version, k):
            for host, model in v:
                if re.search(args.model.lower(), model):
                    print('{0:<20} {1:<15} {2}'.format(host, k, model))
else:
    total = 0
    for k, v in sorted(fact_summary.items()):
        total = v + total
        print(k, v)
    print('TOTAL:', total)
