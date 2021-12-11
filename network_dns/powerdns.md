# Network Reverse DNS Project
DNS independence is sometimes a good thing.  Nothing beats a locally available copy of all your forward and reverse DNS records.  A recent, very high-visibility outage helps prove the point.

Another problem is arises from DNS administrative boundaries.  In a previous role, I found that every reverse record I wanted added for network IP addresses required a cumbersome ticket submission process to a separate department that controlled authoritative access of reverse zone files.  Due to the frequency of new provisioning and changes in the network environment, this situation was not tenable.

There are certainly good arguments for not having parallel DNS systems.  However, DNS is not the tool to ensure that you don't have IP address conflicts.  In general, the only systems that really need reverse address info are those systems you are using for network access and troubleshooting.  It's nice if those systems can also resolve PTR records for application servers, but that can also easily be done in a separate terminal from a system that can resolve those addresses.  What I primarily needed was to be able to get valid host and interface information when running traceroutes through the network or when faced with a long list of IP addresses that I needed to identify.

I set out on a mission to find a lightweight, easily configurable non-fancy DNS server that could just "serve records" efficiently as an authoritative name server for zone files containing my entire network's PTR records.

I also wanted something that has an actively maintained Debian package (no I don't care about CentOS, really, I don't...) to make installation and updating easy.  Finally, the name server needed to be authoritative but also serve as a resolver so that our infrastructure servers can just point to a single name server for all their DNS needs.  The end result of this design is that a host that uses the DNS server that is created can perform all necessary forward DNS resolution, because the only forward records it is authoritative to are in a subdomain which is dedicated to only network hosts.  The only drawback is that the PTR records that it is authoritative for will be missing PTR records for all hosts that are not part of the configuration backups that the `dns_gen_records.py` script parses.  If you have some important PTR records that aren't in your network backups, you can statically declare them in the customizable `ipdb.py`.

My first choice for this project was Knot but I found the documentation to be poor and the setup not that intuitive which means after a few hours of struggling with it, I still didn't have a working name server.  So it was time to move on.  Maybe the documentation is better now.  I wrote this a couple years ago.

My next choice was <a href="https://www.powerdns.com/" target="_blank">PowerDNS</a>.  The documentation still isn't great, but I found it to be better than Knot.  The slightly better documentation combined with the fact that the setup of using a BIND-style zone file backend meant that I was able to stumble my way through the setup and configuration without too much effort.  This wiki page attempts to describe everything I did to get it set up and working, should this task ever need to be repeated.

# Package Installation
Install the packages:

`sudo apt-get install pdns-server pdns-tools`

<u>Note</u>: There is a package called `pdns-recursor` which does not need to be installed as it is a package to use if you only want a recursor and not an authoritative name server.  The `pdns-server` package contains both authoritative and recursor capabilities.

With the default installation you will immediately see a couple processes running:

```
root      1305  0.0  0.2 127056  6068 ?        Ssl  Feb17   0:03 /usr/sbin/pdns_server --daemon --guardian=yes
pdns      1307  0.0  0.8 607928 18220 ?        Sl   Feb17   0:04 /usr/sbin/pdns_server-instance --daemon --guardian=yes
```

A single Systemd service `pdns` can be used to start and stop these.  While PowerDNS provides a utility `pdns_control` to perform most reload and refresh operations, you may find the need to completely restart the service on occasion.

`sudo systemctl stop pdns`

`sudo systemctl start pdns`

or

`sudo systemctl restart pdns`

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

By default the `pdns.simplebind.conf` file should contain the path to the `bind-config` file.

```
root@netns01:/etc/powerdns# cat /etc/powerdns/pdns.d/pdns.simplebind.conf
launch+=bind
bind-config=/etc/powerdns/bindbackend.conf
```

The `/etc/powerdns/bindbackend.conf` file will initially be empty.  This is the file where we add the equivalent of a BIND-style `named.conf`.  While you could change the `bind-config` option in `pdns.simplebind.conf` to point to a different filename like `named.conf` there really is no reason to so I left the default naming of `bindbackend.conf`.

BIND's `named.conf` supports a wide range of options and directives of which many (most?) are not understood or supported by PowerDNS.  In most cases the unsupported options will simply be ignored which allows someone who wants to migrate an existing BIND name server to PowerDNS to simply copy over the entire `named.conf` and the relevant portions will be understood and used.  From the PowerDNS documentation:

*The BIND backend parses a BIND-style named.conf and extracts information about zones from it. It makes no attempt to honour other configuration flags, which you should configure (when available) using the PowerDNS native configuration.*

For our use case we simply create the contents of `bindbackend.conf` from scratch and the configuration for each zone we want to serve is quite simple.  Please note that in this example, I used db.172 so I could put all records for 172.16/12 in a single zone file.  This is because I knew i did not need this server to be able to resolve any public records in 172/8 that fall outside of the 172.16/12 private range.  The script provided in this project expicitly declares all of the /16 ranges that are part of 172.16/12. You can easily modify the `ipdb.py` file to use a single db.172 zone file as I did.

Your bind configuration file needs to contain a declaration for each zone for which your name server will be authoritative.  Follow this example, and make sure the zone files are placed in the declared locations.  Note, the `/etc/powerdns/zones/` directory does not exist by default and is the directory I created to place my zone files.

```
root@netns01:/etc/powerdns# cat bindbackend.conf
zone "foo.example.net" in {
  type master;
  file "/etc/powerdns/zones/db.foo.example.net";
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

## The Zone Files

### The Current Model

In this first version 1.0 of the Network DNS server, I just wanted to keep things simple and get it working quickly.   The `foo.example.net` and `192.168.in-addr.arpa` zones will likely not need to change, however `10.in-addr.arpa` and `172.in-addr.arpa` will probably evolve into different forms.

Right now, it's just easier to have every 10.x PTR record in a single zone file.  More on this later.

As for 172.16.0.0/12 addresses, we know that there have been some addresses accidentally assigned outside of that range.  Again, it's easier for now just to put everything starting with 172.x into a single zone file.  The next step is probably to update my script to produce a /16 zonefile for each /16 in 172.16/12 and a /16 for each range where the accidental IP addresses were assigned.  Again, more on this later.

192.168.0.0/16 can likely remain unchanged for at least as long as we are running our own standalone DNS and don't care about resolving non-network IP addresses in that range.

As you can see in the `bindbackend.conf` file, the zones files are here:

```
root@netns01:~# ls -1 /etc/powerdns/zones/
db.10
db.172
db.192.168
db.foo.example.net
```

### Format

The first several lines of each zone file are exactly the same.  The `@` character makes this possible.  In our custom setup the glue record (last line below) isn't really necessary, but I've left it in place for good practice.

```
$TTL 4h
@ IN SOA netns01.foo.example.net. admin.example.com. (
     1     ; Serial
     3h    ; Refresh after 3 hours
     1h    ; Retry after 1 hour
     1w    ; Expire after 1 week
     1h )  ; Negative caching TTL of 1 hour

@              IN NS     netns01.foo.example.net.
ns1            IN A      192.0.2.1
```

At this point I haven't bothered trying to optimize any of the cache values and may look at doing this in the future.  I also haven't yet implemented actually using the serial number but this will probably come at the point we decide versioning on these zone files and is a topic for discussion.

Below these lines, each zone file simply contains the host records.  Statically declared records are added first, then the dynamically generated hosts records for the reverse zones only.  The script does not generate any forward DNS records for hostnames since it doesn't know which of the many IP addresses available on a system should be used for access.  This functionality is certainly possible if you use a consistent naming convention on the interface that should be used for access.  This is left as an exercise for the reader.


## Serving the Data

Of course restarting the pdns service will pick up any configuration changes that you have made to zones and for our purposes right now, it's not a big deal to do that.  But when you are running production DNS servers that lots of clients rely on, with possibly hundreds of queries per second coming in, you don't want to restart the entire service since it could have an impact on production DNS traffic.  The `pdns_control` utility can be used to gracefully add zones or re-read the contents of existing zone files.

You can see the current status of one or all zones with the `bind-domain-status` option which optionally takes an argument of the domain to check.  Otherwise it shows the status for all domains.

`pdns_control bind-domain-status [domain]`

```
ajbabson@netns01:~$ sudo pdns_control bind-domain-status
172.in-addr.arpa:       parsed into memory at 2020-02-18 17:02:29 +0100
10.in-addr.arpa:        parsed into memory at 2020-02-18 17:02:29 +0100
192.168.in-addr.arpa: [rejected]         error at 2020-02-18 17:02:29 +0100 parsing '192.168.in-addr.arpa.' from file '/etc/powerdns/zones/db.192.168': Trying to insert non-zone data, name='net.arkadin.lan.', qtype=SOA, zone='192.168.in-addr.arpa.'
foo.example.net:        parsed into memory at 2020-02-18 17:02:29 +0100
```

Above we see that there is an error with 192.168.in-addr.arpa.  After fixing the error, I used the following command to reload the zone.

`pdns_control bind-reload-now {domain}`

```
ajbabson@netns01:~$ sudo pdns_control bind-reload-now 192.168.in-addr.arpa
192.168.in-addr.arpa:   parsed into memory at 2020-02-19 10:01:09 +0100
ajbabson@netns01:~$ sudo pdns_control bind-domain-status 192.168.in-addr.arpa
192.168.in-addr.arpa:   parsed into memory at 2020-02-19 10:02:27 +0100
```

A less detailed option is `list-zones`.  For some reason I haven't yet figured out, it lists each zone twice.  Maybe this is a "feature"...

```
ajbabson@netns01:~$ sudo pdns_control list-zones
172.in-addr.arpa.
10.in-addr.arpa.
192.168.in-addr.arpa.
foo.example.net.
172.in-addr.arpa.
10.in-addr.arpa.
192.168.in-addr.arpa.
foo.example.net.
All zonecount:8
```

If you want to reload all existing zones you can use:

`pdns_control reload`

This will not add new zones but will reload all existing zones.

To load a new zone, you must of course add the new zone declarations to `bindbackend.conf` and the zone files to the `/etc/powerdns/zones` directory.  Then you can either add them one by one using:

`pdns_control bind-add-zone {domain} {zone_file}`

```
ajbabson@pnetns01:~$ sudo pdns_control bind-add-zone net.arkadin.lan db.net.arkadin.lan
Already loaded
```

Or you can load all new zones with `pdns_control rediscover`.  Again, the distinction is one of operational control.   In a sensitive production environnment it's probably safer to load new zones one by one and do verification.  In our environment the `rediscover` option is usually easier and safe enough.

Check the `pdns_control` man pages for additional information.

## Automating Zone File Creation

The `dns_gen_records.py` script will parse a directory of network configurations and print to STDOUT a list of PTR records in a format that can be directly added to a BIND style zone file.  Note that it does not print out the SOA section that is required at the top of the zone file so be careful not to overwrite that section when updating a zone file.

The idea for now is that the full list of PTR records can be generated periodically and inserted into each reverse zone file over the existing records.  There is the opportunity also to have a cron job periodically pull updated configs from atlrancid01 and for the script to automatically update the reverse zone files.

This script does not produce any forward records.  The forward zone for `net.arkadin.lan` must be maintained by hand but this is actually much less work than maintaining the reverse records.  Additional controls around serial number and versioning of the zone files needs to be put into place after further discussion on the subject.

