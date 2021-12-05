
import re

zone_dir = 'zones/'

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

# regex to match the networks you want to match
re_apnic1_v4  = re.compile(r'^(103\.214\.228\.\d+)')
re_ripe1_v4   = re.compile(r'^(185\.37\.22[0-3]\.\d+)')
re_ripe2_v4   = re.compile(r'^(77\.111\.2(0[89]|1[01])\.\d+)')
re_arin1_v4   = re.compile(r'^(192\.206\.95\.\d+)')
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

zones = [
    ('db.185.37', re_ripe1_v4),
    ('db.77.111', re_ripe2_v4),
    ('db.192.206.95', re_arin1_v4),
    ('db.103.214.228', re_apnic1_v4),
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

static_records = {
    'db.10': """
; servers - manually added
2.1.0          IN PTR    abc-bastion-01.example.com.
6.1.0          IN PTR    abc-bastion-02.example.com.
14.1.0         IN PTR    xyz-bastion-01.example.com.
18.1.0         IN PTR    xyz-bastion-02.example.com.
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
