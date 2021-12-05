<!-- TITLE: Network DNS Project -->
<!-- SUBTITLE: How to set up and run a BIND-like PowerDNS Server -->
<!-- CREATOR: ababson -->
<!-- MODIFIED: ababson 25/05/20 -->
# Network DNS Project
I set out on a mission to find a lightweight, easily configurable non-fancy DNS server that could just "serve records" efficiently as an authoritative name server for:

- `net.arkadin.lan`
- The parts of `10.in-addr.arpa` that generally contain network IP addresses, usually the highest /29 in each /24.
- `16.172.in-addr.arpa` Network should own all of this since it is reserved for link addressing and not end hosts, although some legacy end hosts use it.
- `168.192.in-addr.arpa` Network should own all of this since it is reserved for loopback addressing, although there is a possibility in the future delegating sub zone files for server/host loopbacks.

I also wanted something that has an actively maintained Debian package (no I don't care about CentOS, really, I don't...) to make installation and updating easy.  Finally, the name server needed to be authoritative but also serve as a resolver so that our infrastructure servers can just point to a single name server for all their DNS needs.  My first choice was Knot but I found the documentation to be poor and the setup not that intuitive which means after a few hours of struggling with it, I still didn't have a working name server.  So it was time to move on.

My next choice was <a href="https://www.powerdns.com/" target="_blank">PowerDNS</a>.  The documentation still isn't great, but I found it to be better than Knot.  The slightly better documentation combined with the fact that the setup of using a BIND-style zone file backend meant that I was able to stumble my way through the setup and configuration without too much effort.  This wiki page attempts to describe everything I did to get it set up and working, should this task ever need to be repeated.

# Package Installation
Install the packages:

`sudo apt-get install pdns-server`
`sudo apt-get install pdns-tools`

<u>Note</u>: There is a package called `pdns-recursor` which does not need to be installed as it is a package to use if you only want a recursor and not an authoritative name server.  The `pdns-server` package contains both authoritative and recursor capabilities.

With the default installation you will immediately see a couple processes running:

```
root      1305  0.0  0.2 127056  6068 ?        Ssl  Feb17   0:03 /usr/sbin/pdns_server --daemon --guardian=yes
pdns      1307  0.0  0.8 607928 18220 ?        Sl   Feb17   0:04 /usr/sbin/pdns_server-instance --daemon --guardian=yes
```

A single Systemd service `pdns` can be used to start and stop these.  While PowerDNS provides a utility `pdns_control` to perform most reload and refresh operations, you may find the need to completely restart the service on occasion.

`sudo service pdns stop`
`sudo service pdns start`
or
`sudo service pdns restart`
# Configuration
## pdns.conf

A few changes need to be made to the main configuration file `/etc/powerdns/pdns.conf`.  Everything that follows already exists in commented form in the pdns.conf file.  You just need to specify the change you want an uncomment as appropriate.

### Authorize Zone Transfers 

You can authorize clients to perform zone file transfers with this option:

`allow-axfr-ips=10.100.19.21/32`

### Specify the Back End

This line specifies the back end to use for the zone data.  Yes, you can use all sorts of <a href="https://doc.powerdns.com/authoritative/backends/" target="_blank">fancy things</a> for your back end data.  But why use more than you need?   In our case plain text BIND-style zone files will work just fine.

`launch=bind`

### Make Authoritative

The following option makes your server act as a master although in theory it's possible to add domains to your BIND configuration file as `slave`.   However, I did not enter into those details since the goal for this server is to be a master for all the domains it serves authoritatively.

`master=yes`

### Enable Recursion

By default, recursion for clients is not allowed but it can be enabled here.

`allow-recursion=10.0.1.0/24,10.100.19.20/31,10.115.137.0/24`

You must also specify a name server to query for recursive requests.  If you don't do this, recursive requests will not work.  I simply chose the first one from the local `/etc/resolv.conf`.  

`recursor=10.115.131.1`

It will not allow you to specify two recursors and while I at first thought this seemed like a lack of redundancy, the fact is that you would typically not deploy a single name server and your secondary PowerDNS name server would be a backup and have a different recursor.

### Rereading Configuration

According to the documentation, you can reload the options in `pdns.conf` using `pdns_control cycle`.  However, I was not able to get this to work and had to restart the `pdns` service after making changes to `pdns.conf`.

## BIND (bindbackend.conf)

I don't recall if these files are created during the initial installation or if they are added after you set `launch=bind` in `pdns.conf` and then restart the service, but regardless, the following file was automatically created with the following contents:

```
root@pa2dns01:/etc/powerdns# cat /etc/powerdns/pdns.d/pdns.simplebind.conf
launch+=bind
bind-config=/etc/powerdns/bindbackend.conf
```

The `/etc/powerdns/bindbackend.conf` file was also created but was empty.  This is the file where we add the equivalent of a BIND-style `named.conf`.  While you could change the `bind-config` option in `pdns.simplebind.conf` to point to a different filename like `named.conf` there really is no reason to so I left the default naming of `bindbackend.conf`.

BIND's `named.conf` supports a wide range of options and directives of which many (most?) are not understood or supported by PowerDNS.  In most cases the unsupported options will simply be ignored which allows someone who wants to migrate an existing BIND name server to PowerDNS to simply copy over the entire `named.conf` and the relevant portions will be understood and used.  From the PowerDNS documentation:

*The BIND backend parses a BIND-style named.conf and extracts information about zones from it. It makes no attempt to honour other configuration flags, which you should configure (when available) using the PowerDNS native configuration.*

For our use case we simply create the contents of `bindbackend.conf` from scratch and the configuration for each zone we want to serve is quite simple.

```
root@pa2dns01:/etc/powerdns# cat bindbackend.conf
zone "net.arkadin.lan" in {
  type master;
  file "/etc/powerdns/zones/db.net.arkadin.lan";
};

zone "10.in-addr.arpa" in {
  type master;
  file "/etc/powerdns/zones/db.10";
};

zone "172.in-addr.arpa" in {
  type master;
  file "/etc/powerdns/zones/db.172";
};

zone "192.168.in-addr.arpa" in {
  type master;
  file "/etc/powerdns/zones/db.192.168";
};
```

All we have to do is declare each zone, say that we want to serve it as master, and then provide a path to the zone file.

## The Zone Files

### The Current Model

In this first version 1.0 of the Network DNS server, I just wanted to keep things simple and get it working quickly.   The `net.arkadin.lan` and `192.168.in-addr.arpa` zones will likely not need to change, however `10.in-addr.arpa` and `172.in-addr.arpa` will probably evolve into different forms.

Right now, it's just easier to have every 10.x PTR record in a single zone file.  More on this later.

As for 172.16.0.0/12 addresses, we know that there have been some addresses accidentally assigned outside of that range.  Again, it's easier for now just to put everything starting with 172.x into a single zone file.  The next step is probably to update my script to produce a /16 zonefile for each /16 in 172.16/12 and a /16 for each range where the accidental IP addresses were assigned.  Again, more on this later.

192.168.0.0/16 can likely remain unchanged for at least as long as we are running our own standalone DNS and don't care about resolving non-network IP addresses in that range.

As you can see in the `bindbackend.conf` file, the zones files are here:

```
root@pa2dns01:~# ls -1 /etc/powerdns/zones/
db.10
db.172
db.192.168
db.net.arkadin.lan
```

### Format

The first several lines of each zone file are exactly the same.  The `@` character makes this possible.  In our custom setup the glue record (last line below) isn't really necessary, but I've left it in place for good practice.

```
$TTL 4h
@ IN SOA pa2dns01.net.arkadin.lan. nio.arkadin.com. (
     1     ; Serial
     3h    ; Refresh after 3 hours
     1h    ; Retry after 1 hour
     1w    ; Expire after 1 week
     1h )  ; Negative caching TTL of 1 hour

@              IN NS     pa2dns01.net.arkadin.lan
pa2dns01       IN A      10.124.23.53
```

At this point I haven't bothered trying to optimize any of the cache values and may look at doing this in the future.  I also haven't yet implemented actually using the serial number but this will probably come at the point we decide versioning on these zone files and is a topic for discussion.

Below these lines, each zone file simply contains the host records.  Here's an example from each of the four zone files:

```
# db.10 - reverse record for 10.100.125.254
254.125.100    IN PTR    atlcore02-vl125-hsrp.net.arkadin.lan

# db.172 - reverse record for 172.16.0.2
2.0.16         IN PTR    shiixrt01-gi0-0-1-2603.net.arkadin.lan

# db.192.168 - reverse record for 192.168.4.1
1.4            IN PTR    tau-bl-01-lo0-1.net.arkadin.lan

# db.net.arkadin.lan - forward record
atl-bastion-01    IN  A      10.0.1.2
```

## Serving the Data

Of course restarting the pdns service will pick up any configuration changes that you have made to zones and for our purposes right now, it's not a big deal to do that.  But when you are running production DNS servers that lots of clients rely on, with possibly hundreds of queries per second coming in, you don't want to restart the entire service since it could have an impact on production DNS traffic.  The `pdns_control` utility can be used to gracefully add zones or re-read the contents of existing zone files.

You can see the current status of one or all zones with the `bind-domain-status` option which optionally takes an argument of the domain to check.  Otherwise it shows the status for all domains.

`pdns_control bind-domain-status [domain]`

```
ababson@pa2dns01:~$ sudo pdns_control bind-domain-status
172.in-addr.arpa:       parsed into memory at 2020-02-18 17:02:29 +0100
10.in-addr.arpa:        parsed into memory at 2020-02-18 17:02:29 +0100
192.168.in-addr.arpa: [rejected]         error at 2020-02-18 17:02:29 +0100 parsing '192.168.in-addr.arpa.' from file '/etc/powerdns/zones/db.192.168': Trying to insert non-zone data, name='net.arkadin.lan.', qtype=SOA, zone='192.168.in-addr.arpa.'
net.arkadin.lan:        parsed into memory at 2020-02-18 17:02:29 +0100
```

Above we see that there is an error with 192.168.in-addr.arpa.  After fixing the error, I used the following command to reload the zone.

`pdns_control bind-reload-now {domain}`

```
ababson@pa2dns01:~$ sudo pdns_control bind-reload-now 192.168.in-addr.arpa
192.168.in-addr.arpa:   parsed into memory at 2020-02-19 10:01:09 +0100
ababson@pa2dns01:~$ sudo pdns_control bind-domain-status 192.168.in-addr.arpa
192.168.in-addr.arpa:   parsed into memory at 2020-02-19 10:02:27 +0100
```

A less detailed option is `list-zones`.  For some reason I haven't yet figured out, it lists each zone twice.  Maybe this is a "feature"...

```
ababson@pa2dns01:~$ sudo pdns_control list-zones
172.in-addr.arpa.
10.in-addr.arpa.
192.168.in-addr.arpa.
net.arkadin.lan.
172.in-addr.arpa.
10.in-addr.arpa.
192.168.in-addr.arpa.
net.arkadin.lan.
All zonecount:8
```

If you want to reload all existing zones you can use:

`pdns_control reload`

This will not add new zones but will reload all existing zones.

To load a new zone, you must of course add the new zone declarations to `bindbackend.conf` and the zone files to the `/etc/powerdns/zones` directory.  Then you can either add them one by one using:

`pdns_control bind-add-zone {domain} {zone_file}`

```
ababson@pa2dns01:~$ sudo pdns_control bind-add-zone net.arkadin.lan db.net.arkadin.lan
Already loaded
```

Or you can load all new zones with `pdns_control rediscover`.  Again, the distinction is one of operational control.   In a sensitive production environnment it's probably safer to load new zones one by one and do verification.  In our environment the `rediscover` option is usually easier and safe enough.

Check the `pdns_control` man pages for additional information.

## Automating Zone File Creation

The `dns_gen_records.py` script will parse a directory of network configurations and print to STDOUT a list of PTR records in a format that can be directly added to a BIND style zone file.  Note that it does not print out the SOA section that is required at the top of the zone file so be careful not to overwrite that section when updating a zone file.

The idea for now is that the full list of PTR records can be generated periodically and inserted into each reverse zone file over the existing records.  There is the opportunity also to have a cron job periodically pull updated configs from atlrancid01 and for the script to automatically update the reverse zone files.

This script does not produce any forward records.  The forward zone for `net.arkadin.lan` must be maintained by hand but this is actually much less work than maintaining the reverse records.  Additional controls around serial number and versioning of the zone files needs to be put into place after further discussion on the subject.

```
ababson@atlnetutil01:tools(master)$ ./dns_gen_records.py -h
usage: dns_gen_records.py [-h] [--dir DIR] ptr_class

positional arguments:
  ptr_class   Which class of addresses to process: host, link, or loop.

optional arguments:
  -h, --help  show this help message and exit
  --dir DIR   Directory where network host configs are located.

Parse network hosts configurations and print BIND style reverse zone files
for RFC1918 IP addresses based on the following address classes:

host: 10.0.0.0/8
link: 172.0.0.0/8 (due to misuse of addresses, the entire 172/8 is checked)
loop: 192.168.0.0/16

Network host configurations are parsed to obtain the IP address data so you must
provide a directory with a configuration file for each host you want to process.

By default the script checks your home directory for a .conf_dir file which
contains the path to the network configurations.

ababson@atlnetutil01:~$ cat .conf_dir
/home/ababson/configs/NETWORK/configs

examples:
    dns_gen_records.py host
    dns_gen_records.py link
    dns_gen_records.py loop

    dns_gen_records.py loop --dir='/home/ababson/configs/NETWORK/configs'
```
