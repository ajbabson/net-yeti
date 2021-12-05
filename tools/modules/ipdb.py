
import re

# add the destination directory to save the zone files
zone_dir = 'zones/'

# add your custom SOA to add to the top of each zone file
soa = """$TTL 4h
@ IN SOA ns1.example.com. admin.example.com. (
     1     ; Serial
     3h    ; Refresh after 3 hours
     1h    ; Retry after 1 hour
     1w    ; Expire after 1 week
     1h )  ; Negative caching TTL of 1 hour

@              IN NS     ns1.example.com.
ns1            IN A      192.0.2.0
"""

# add one regex for each network you want to match
#
# these are fake public ranges for illustrative purposes 
# imagine you have two RIPE allocations and one APNIC
# RIPE  192.0.2.0/24
# RIPE  198.51.100.0/24
# APNIC 203.0.113.0/24
# replace these with your own public ranges and the appropriate description
# the description doesn't matter as long as it matches what you put in the
# zones list below this section
re_ripe1_v4   = re.compile(r'^(192\.0\.2\.\d+)')
re_ripe2_v4   = re.compile(r'^(198\.51\.100\.\d+)')
re_apnic1_v4  = re.compile(r'^(203\.0\.113\.\d+)')
# RFC 1918
re_10_v4      = re.compile(r'^(10\.\d+\.\d+\.\d+)')
re_172_16_v4  = re.compile(r'^(172\.16\.\d+\.\d+)')
re_172_17_v4  = re.compile(r'^(172\.17\.\d+\.\d+)')
re_172_18_v4  = re.compile(r'^(172\.18\.\d+\.\d+)')
re_172_19_v4  = re.compile(r'^(172\.19\.\d+\.\d+)')
re_172_20_v4  = re.compile(r'^(172\.20\.\d+\.\d+)')
re_172_21_v4  = re.compile(r'^(172\.21\.\d+\.\d+)')
re_172_22_v4  = re.compile(r'^(172\.22\.\d+\.\d+)')
re_172_23_v4  = re.compile(r'^(172\.23\.\d+\.\d+)')
re_172_24_v4  = re.compile(r'^(172\.24\.\d+\.\d+)')
re_172_25_v4  = re.compile(r'^(172\.25\.\d+\.\d+)')
re_172_26_v4  = re.compile(r'^(172\.26\.\d+\.\d+)')
re_172_27_v4  = re.compile(r'^(172\.27\.\d+\.\d+)')
re_172_28_v4  = re.compile(r'^(172\.28\.\d+\.\d+)')
re_172_29_v4  = re.compile(r'^(172\.29\.\d+\.\d+)')
re_172_30_v4  = re.compile(r'^(172\.30\.\d+\.\d+)')
re_172_31_v4  = re.compile(r'^(172\.31\.\d+\.\d+)')
re_192_168_v4 = re.compile(r'^(192\.168\.\d+\.\d+)')

# Each tuple should be the name of the zone file you want to write
# and the regex that matches the IP range that will go in the zone file.
# The regex variable must be declared in the section above.
zones = [
    # public
    ('db.192.0.2', re_ripe1_v4),
    ('db.198.51.100', re_ripe2_v4),
    ('db.203.0.113', re_apnic1_v4),
    # RFC 1918
    ('db.10', re_10_v4),
    ('db.172.16', re_172_16_v4),
    ('db.172.17', re_172_17_v4),
    ('db.172.18', re_172_18_v4),
    ('db.172.19', re_172_19_v4),
    ('db.172.20', re_172_20_v4),
    ('db.172.21', re_172_21_v4),
    ('db.172.22', re_172_22_v4),
    ('db.172.23', re_172_23_v4),
    ('db.172.24', re_172_24_v4),
    ('db.172.25', re_172_25_v4),
    ('db.172.26', re_172_26_v4),
    ('db.172.27', re_172_27_v4),
    ('db.172.28', re_172_28_v4),
    ('db.172.29', re_172_29_v4),
    ('db.172.30', re_172_30_v4),
    ('db.172.31', re_172_30_v4),
    ('db.192.168', re_192_168_v4)
]

# Add to this dict any records that are not contained in your network config
# backups.
# The key must match the name of a zone file declared in the zones list above.
# The value should be the exact text as you want it to appear at the top of the
# zone file just below the SOA.  This is an optional section and can be removed
# as long as the static records = {} declaration remains in place as an empty
# dict.
static_records = {
    'db.10': """
; servers - manually added
2.1.0          IN PTR    abc-server-01.example.com.
6.1.0          IN PTR    abc-server-02.example.com.
14.1.0         IN PTR    xyz-server-01.example.com.
18.1.0         IN PTR    xyz-server-02.example.com.
""",
    'db.172.16': """
; links - manually added
0.1            IN PTR    link1.example.com.
1.1            IN PTR    link2.example.com.
2.1            IN PTR    link3.example.com.
3.1            IN PTR    link4.example.com.
""",
    'db.192.168': """
; loopbacks - manually added
0.1            IN PTR    loopback0.example.com.
1.1            IN PTR    loopback1.example.com.
2.1            IN PTR    loopback2.example.com.
3.1            IN PTR    loopback3.example.com.
"""
}
