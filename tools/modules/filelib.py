#!/usr/bin/env python3

from os import listdir
from os import path
import re

def get_config_list(conf_dir):
    '''
    Get a list of all Rancid network backup configurations and return a list of
    (filename, platform) tuples.
    '''
    config_list = []
    contents = listdir(conf_dir)
    for i in contents:
        fullpath = '/'.join([conf_dir, i])
        if i.startswith('.'):
            continue
        elif path.isfile(fullpath):
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
                    platform = rancid_type_match.group(1)
                else:
                    platform = 'unknown'
            config_list.append((i, platform))
    return config_list

def get_configs(conf_dir):
    '''
    Return a dictionary of (hostname, platform):[config_lines]
    key = tuple and value = list
    '''
    # modify as needed
    unsupported = ['opengear', 'foundry']
    configs = {}
    config_list = get_config_list(conf_dir)
    for conf_name, platform in config_list:
        if platform in unsupported:
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

