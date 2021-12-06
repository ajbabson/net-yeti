#!/usr/bin/env python3

import modules.shared_regex as rgx
import glob
from os import path
from os import environ
from os import getenv
import re

def get_conf_dir():
    conf_dir = environ.get('CONF_DIR')
    if conf_dir:
        return conf_dir
    userhome = getenv('HOME')
    conf_dir_var = '/'.join([userhome, '.conf_dir'])
    if path.isfile(conf_dir_var):
        with open(conf_dir_var, 'rt') as fh:
            conf_dir = fh.readlines()
            for line in conf_dir:
                if line.startswith('#'):
                    continue
                else:
                    conf_dir = line.rstrip()
        if path.isdir(conf_dir):
            return conf_dir
    return 'configs/'

def get_config_list(conf_dir, regex='*'):
    '''
    Get a list of all Rancid network backup configurations and return a list of
    (filename, vendor) tuples.
    '''
    config_list = []
    contents = glob.glob(conf_dir + regex)
    for fullpath in contents:
        hostname = fullpath.split('/')[-1]
        if hostname.startswith('.'):
            continue
        elif path.isfile(fullpath):
            if path.getsize(fullpath) == 0:
                continue
            # encoding='utf-8' avoids UnicodeDecodeError when a conf file has
            # unicode characters
            with open(fullpath, encoding='utf-8') as fh:
                firstline = fh.readline()
                # possible rancid type matches seen
                # (acme|Brocade|cisco|cisco-nx|Dell|force10|foundry|juniper|
                # netscreen|opengear)
                rancid_type_match = re.search(
                  r'RANCID-CONTENT-TYPE:\s(\S+)', firstline)
                if rancid_type_match:
                    vendor = rancid_type_match.group(1)
                else:
                    vendor = 'unknown'
            config_list.append((hostname, fullpath, vendor))
    return config_list

def get_configs(conf_dir):
    '''
    Return a dictionary of (hostname, platform):[config_lines]
    key = tuple and value = list
    '''
    configs = {}
    config_list = get_config_list(conf_dir)
    for conf_name, platform in config_list:
        if re.search('opengear|foundry', platform):
            continue
        config_lines = []
        fullpath = '/'.join([conf_dir, conf_name])
        with open(fullpath, encoding='utf-8') as fh:
            config_lines = fh.readlines()
        for line in config_lines:
            hostname_match = re.search('host-?name\s(\S+)', line)
            if hostname_match:
                hostname = hostname_match.group(1).rstrip(';')
                if configs.get(hostname):
                    print('Skipping duplicate hostname: {0}'.format(hostname))
                    print(': {0}'.format(c))
                else:
                    configs[(hostname, platform)] = config_lines
                break
    return configs

def get_facts(conf_dir, inc_config=False):
    '''
    Return a dictionary in the format:

    facts[hostname] = {'vendor' : vendor,  'model': model,
                       'version': version, 'config': [config_lines]}

    The config is set to None unless explicitly requested.
    '''
    facts = {}
    config_list = get_config_list(conf_dir)
    for hostname, fullpath, vendor in config_list:
        #if re.search('arista|bigip', vendor):
        if 'juniper' not in vendor:
            continue
        config_lines = []
        with open(fullpath, encoding='utf-8') as fh:
            config_lines = fh.readlines()
        for line in config_lines:
            #hostname_match = re.search('host-?name\s(\S+)', line)
            hostname_match = re.search('Hostname:\s(\S+)', line)
            if hostname_match:
                hostname = hostname_match.group(1).lower()
                #hostname = hostname_match.group(1).rstrip(';')
                if facts.get(hostname):
                    continue
                    print('Skipping duplicate hostname: {0}'.format(hostname))
                else:
                    facts[hostname] = {'vendor' : vendor, 'model': '', \
                                       'version': '', 'config'  : None}
                    if (inc_config):
                        facts[hostname]['config'] = config_lines
            model_match = rgx.model.search(line)
            if model_match:
                model = model_match.group(1)
                facts[hostname]['model'] = model
            version_match = rgx.junos_version.search(line)
            if version_match:
                version = version_match.group(1)
                facts[hostname]['version'] = version
                break
            srx_version_match = rgx.srx_version.search(line)
            if srx_version_match:
                version = srx_version_match.group(1)
                facts[hostname]['version'] = version
                break
            ex_version_match = rgx.ex_version.search(line)
            if ex_version_match:
                version = ex_version_match.group(1)
                facts[hostname]['version'] = version
                break
            qfx3500_version_match = rgx.qfx3500_version.search(line)
            if qfx3500_version_match:
                version = qfx3500_version_match.group(1)
                facts[hostname]['version'] = version
                break
        #if len(facts[hostname]['version']) < 1:
        #    print('HOST:', hostname)
        #    quit()
    return facts

#def get_rancid_version(confg):

# Hostname: STORSW-001a.IAD100
# Model: qfx5200-32c-32q
# Junos: 15.1X53-D232.3
# SRX
# JUNOS Software Release [12.3X48-D90.2]
# Model: qfx3500s
# JUNOS Base OS boot [12.3X50-D41.1]
# JUNOS Base OS Software Suite [12.3X50-D41.1]


# hostname ASW-003B.IAD101
# !Chassis type: Nexus 3048 - a NXOS router
# !Software: kickstart: version 6.0(2)U6(6)
# !Software: system: version 6.0(2)U6(6)

