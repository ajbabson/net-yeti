# Reverse DNS

Accurate reverse DNS should be considered a requirement for operating network
infrastructure.  This should be a zero touch process, from adding new records,
modifying existing ones, and deleting records for IP addresses that no longer 
exist in the network.

This script can parse your network configuration backups and generate reverse
zone files that can be used by any BIND-style DNS server.  I used PowerDNS in
the past and have left documentation on that process in this repository.
However, significant changes have occurred in PowerDNS since the document was
created, and it needs to be updated, which I haven't yet had time or compelling
reason to do.  I leave the deprecated document available for reference in case
it can be of use, mainly because it describes the zero-touch process I used to
maintain reverse DNS.


