# bitnoc

This framework povides efficient and easier ways to perform common operational tasks in the service provider edge and core network.

The functionality offered provides simple means to execute common time consuming; when caried out with conventional methods; and critical tasks. Embeded subsystems that consume API to interface with some popular network systems such as Solarwinds Orion NMS and Netdot help to bridge the gap between systems and databases hence forth providing seemless workflows.

### Example use case
A service activation tickets would require an operator to
- Check an IP Address Management (IPAM) tool for available address space
- Reserve an address space in IP Address Management (IPAM) tool
- Consult existing vlan database to make sure you get a free vlan-id
- Configure the L3 gateway interface
- Configure traffic policing to ensure access to/from the service is billed accordingly
- Update monitoring system

It is obvious here that some kind of automation would be beneficial for this repetitive task.
The best part is, the user does not need to know the underlying CLI command for any particular vendor, everything is a mouse click away.

### Key features
-    Quickly deploy new service by collecting data from your IT infrastructure in a few minutes.
-    Maintain consistent configuration and data records for your infrastructure databases
-    Issue commands to all network devices at once via centralized interface to quickly pinpoint issues or gather information.
-    Automatically schedule bandwidth changes for different services at any time
-    Get email alerts on bandwidth changes performed automatically
-    Store and archive logs for audit and tracking purposes
-    Interface with existing systems with supported APIs
-    Get simple access to relevant data from your entire network
-    Easy to setup and requires no costly training for installation and user education

### Tools available
-    Service search
-    VLAN operations
-    IPv4 operations
-    Service provisioning
-    BGP session monitoring
-    Services auditing
-    Burst packages management
-    Bandwidth on demand management
-    Network diagram generation for link state protocols (ISIS & OSPF)
-    Report generation for customers services availbale on PE routers
-    Configuration archiving

### Service search
The search can be performed against a vlan-id, service description or ipv4 address.
The tool uses an algorithm to search for interesting sections of running/active configuration in each active edge router in the network.

### IPv4 & VLANs operations
Offers the ability to query all active edge routers in the network and find out if an IPv4 prefix or its subnet has been used.
Helps in identifying rogue IPv4 addresses configured in the network consequently resolving address and routing conflicts in the network.
Allows an operator to locate the edge at which a certain vlan-id has been used.
On edge routers with high customer density this tools automates the task of finding free vlans to use for new service provisioning.

### Service provisioning
Auto provisioning of internet and L2MPLS services on edge routers on a single click.
Automatically assigns a vlan-id and IPv4 addresses from IPAM and adds node to NPM for monitoring.
Drastically reduces the amount of time (at least 50%) an administrator would use to gather config details and extra time to update documentation/monitoring databases

> ### Burst packages management (in development)
Offers a client-server relation between the client application running on admin workstation and the server hosting the clients database and config changes.
Network admin can easily make use of this unified interface to manage burst clients in a user friendly manner.
Offers ability to view clients and their packages, add or remove clients and moving clients between packages.

> ### Bandwidth on demand management (in development)
Admin can add and schedule bandwidth changes to be carried out or reverted at a later time without requiring manual intervention.
User has the ability to view scheduled bandwidth changes and to delete or modify them.
Offloads manual tracking of temporary bandwidth change requests that is not very efficient.

#### Supported platforms
-    JunOS 11.4R9 and later
-    Cisco IOS 12 and later, IOS XE
-    NETCONF is required for all devices except those running native IOS where SSH is used.

#### Consumable APIs
-    Solarwinds Orion Swis
-    Netdot REST

# Application architecture
![bitnoc building blocks](https://user-images.githubusercontent.com/50369643/76944900-d7425d80-6912-11ea-917b-5dae40a663c4.png)

# Installation
These instructions assume you already have python installed and python vitual environment module installed

### Dependacies
- Python 3.7 or later
- Python virtual environment

### Windows OS

Clone this repository
<pre>
basondole → c:\Users\u\Desktop\basohub\github
git clone https://github.com/basondole/bitnoc
Cloning into 'bitnoc'...
remote: Enumerating objects: 116, done.
remote: Counting objects: 100% (116/116), done.
remote: Compressing objects: 100% (85/85), done.
remote: Total 116 (delta 28), reused 113 (delta 25), pack-reused 0
Receiving objects: 100% (116/116), 639.25 KiB | 824.00 KiB/s, done.
Resolving deltas: 100% (28/28), done.
</pre>

Verify the file structure
<pre>
basondole → c:\Users\u\Desktop\basohub\github
cd bitnoc

basondole → c:\Users\u\Desktop\basohub\github\bitnoc
ls
app.py  application  core  other  requirements.txt  windows

basondole → c:\Users\u\Desktop\basohub\github\bitnoc
tree
.
├── README.md
├── application
│   ├── __init__.py
│   ├── database
│   │   ├── devices.yml
│   │   └── user.db
│   ├── forms.py
│   ├── models.py
│   ├── static
│   │   ├── css
│   │   │   ├── bootstrap.min.css
│   │   │   ├── docs.min.css
│   │   │   └── fontawesome.all.css
│   │   ├── images
│   │   │   ├── default
│   │   │   │   └── router.gif
│   │   │   ├── paul-icon.ico
│   │   │   └── svg
│   │   │       └── bootstrap.svg
│   │   ├── jquery
│   │   │   ├── jquery-3.3.1.min.js
│   │   │   └── jquery-ui.js
│   │   ├── js
│   │   │   ├── bootstrap.min.js
│   │   │   ├── d3.v4.min.js
│   │   │   ├── jquery.validate.min.js
│   │   │   └── popper.min.js
│   │   └── miserables.json
│   └── templates
│       ├── home.html
│       ├── html
│       │   └── bgp-neighbor-monitor-table.html
│       ├── json
│       │   └── rasimu.json
│       ├── layout.html
│       ├── login.html
│       ├── register.html
│       ├── renders
│       │   └── text-output.html
│       ├── view-bgp-neighbor-monitor.html
│       ├── view-network-diagram.html
│       ├── view-service-audit.html
│       └── view-text-output.html
├── core
│   ├── NetdotOrion.py
│   ├── __init__.py
│   ├── bgp_summary.py
│   ├── config_backup.py
│   ├── find_vlan_duo.py
│   ├── find_vlan_uno.py
│   ├── get_intf_cisco_summary.py
│   ├── get_intf_summary.py
│   ├── link_state.py
│   ├── locate_ip.py
│   ├── locate_name.py
│   ├── locate_vlan.py
│   ├── send_command.py
│   └── service_provision.py
├── other
│   ├── Essential.py
│   ├── __init__.py
│   ├── cryptoengine.py
│   └── getDeviceData.py
├── requirements.txt
├── run.py
└── windows
    ├── Command.py
    ├── Devices.py
    ├── Settings.py
    └── __init__.py

16 directories, 54 files
</pre>

Create a python virtual environment
<pre>
basondole → c:\Users\u\Desktop\basohub\github\bitnoc
python -m venv bitnoc

basondole → c:\Users\u\Desktop\basohub\github\bitnoc
ls
app.py  application  bitnoc  core  other  requirements.txt  windows

basondole → c:\Users\u\Desktop\basohub\github\bitnoc
bitnoc\Scripts\activate
</pre>

Install the required python packages
<pre>
(bitnoc) basondole → c:\Users\u\Desktop\basohub\github\bitnoc
pip install -r requirements.txt
Collecting bcrypt==3.1.7 (from -r requirements.txt (line 1))
.
.
Successfully installed Flask-1.1.1 Flask-Bcrypt-0.7.1 ...
</pre>

Run the application with python
<pre>
(bitnoc) basondole → c:\Users\u\Desktop\basohub\github\bitnoc
python run.py
 * Serving Flask app "application" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: XXX-XXX-XXX
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 </pre>

Open the browser and access <code>http://127.0.0.1:5000/</code> or <code>http://localhost:5000/</code>
Once the web portal loads complete the setup by

- Click sign up to create a user account and you will be redirected to a settings page.
- Set Path to device database: as <code>./application/database/</code>
- Specify the ssh authentication server with its port number.
- Save the settings and you will be redirected back to the login page
- Create a user account via the sign up link. 
> Note: The username and password must be the same as the credentials used for ssh access to your network.

It may take a minute for a user to be registered as the server tries to verify the user credentials against the specified authentication server.
> Note: this installation will only be availbale on local host, further windows firewall tweaking must be done to allow external
connection to access the server


### Installation on CentOS
Clone the git repo
<pre>
[root@basondole ~]# git clone https://github.com/basondole/bitnoc
Cloning into 'bitnoc'...
remote: Enumerating objects: 175, done.
remote: Counting objects: 100% (175/175), done.
remote: Compressing objects: 100% (123/123), done.
remote: Total 175 (delta 67), reused 147 (delta 45), pack-reused 0
Receiving objects: 100% (175/175), 659.23 KiB | 710.00 KiB/s, done.
Resolving deltas: 100% (67/67), done.
</pre>

Create a virtual environment and install required packages
<pre>
[root@basondole ~]# cd bitnoc/

[root@basondole bitnoc]# python3 -m venv bitnoc

[root@basondole bitnoc]# source bitnoc/bin/activate

(bitnoc) [root@basondole bitnoc]# pip3 install -r requirements.txt
Collecting bcrypt==3.1.7 (from -r requirements.txt (line 1))
.
.
  Running setup.py install for PyYAML ... done
  Running setup.py install for Flask-Bcrypt ... done
  Running setup.py install for SQLAlchemy ... done
  Running setup.py install for future ... done
  Running setup.py install for ipaddr ... done
  Running setup.py install for IPy ... done
  Running setup.py install for ncclient ... done
  Running setup.py install for nxapi-plumbing ... done
  Running setup.py install for pyIOSXR ... done
  Running setup.py install for pyeapi ... done
  Running setup.py install for orionsdk ... done
  Running setup.py install for pynetdot ... done
  Running setup.py install for yamlordereddictloader ... done
Successfully installed Flask-1.1.1 Flask-Bcrypt-0.7.1 Flask-Login-0.5.0 ...
(bitnoc) [root@basondole bitnoc]#
</pre>

> If you run the server at this point as <code>python run.py</code>, you will notice that the server is only available from your own computer, not from any other in the network. This is the default because in debugging mode a user of the application can execute arbitrary Python code on your computer. If you have debug disabled or trust the users on your network, you can make the server publicly available.

You need to make some changes to make it run on your machines IP address.
Edit the file <code>run.py</code>
and change the line <code>app.run(debug=True)</code>
to <code>app.run(host= '0.0.0.0',debug=True)</code>

Bitnoc runs on port 5000. You need to allow external connection to your server on this port for the app to be available
on other hosts in your network.
By default centos wont be listening to this port, to change this default behavior

Add the port by editing the file <code>/etc/services</code>
<pre>
[root@basondole bitnoc]# cat /etc/services | grep bitnoc
flask-bitnoc    5000/tcp                        # Flask Bitnoc
</pre>

Open firewall ports. In this installation, the app will only be accessible from the host <code>10.18.17.28/32</code>
Therefore the port <code>5000</code> will only be opened for this host
<pre>
[root@basondole bitnoc]# firewall-cmd --permanent --zone=public --add-rich-rule='
>   rule family="ipv4"
>   source address="10.18.17.28/32"
>   port protocol="tcp" port="5000" accept'
success

[root@basondole bitnoc]# firewall-cmd --reload
success
</pre>

Verify the zone
<pre>
[root@basondole bitnoc]# cat /etc/firewalld/zones/public.xml
&lt;?xml version="1.0" encoding="utf-8"?&gt;
&lt;zone&gt;
  &lt;short&gt;Public&lt;/short&gt;
  &lt;description&gt;
    For use in public areas. You do not trust the other computers on networks to not harm your computer.
    Only selected incoming connections are accepted.
  &lt;/description&gt;
  &lt;service name="tftp"/&gt;
  &lt;service name="dhcpv6-client"/&gt;
  &lt;service name="ssh"/&gt;
  &lt;rule family="ipv4"&gt;
    &lt;source address="10.18.17.28/32"/&gt;
    &lt;port protocol="tcp" port="5000"/&gt;
    &lt;accept/&gt;
  &lt;/rule&gt;
&lt;/zone&gt;
[root@basondole bitnoc]#
</pre>

Check newly added port status
<pre>
[root@basondole bitnoc]# iptables-save | grep 5000
-A IN_public_allow -p tcp -m tcp --dport 5000 -m conntrack --ctstate NEW,UNTRACKED -j ACCEPT
</pre>

Confirm the port is open by doing a nmap scan from the host <code>10.18.17.28</code> to the server <code>10.21.2.8</code>
<pre>
basondole → C:\Users\u
nmap -n -p 5000 10.21.2.8
Starting Nmap 7.80 ( https://nmap.org ) at 2020-03-13 19:29 E. Africa Standard Time
Nmap scan report for 10.21.2.8
Host is up (0.0021s latency).

PORT     STATE SERVICE
5000/tcp open  upnp

Nmap done: 1 IP address (1 host up) scanned in 2.59 seconds
</pre>

Run the app
<pre>
(bitnoc) [root@basondole bitnoc]# python run.py
 * Serving Flask app "application" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: XXX-XXX-XXX
 </pre>
 </pre>

 Browse any of the IP configured on this server to access the application from the host <code>10.18.17.28</code>  
 http://10.21.2.8:5000

### Start application on boot
## supervisord
<pre>
sudo yum install supervisor
sudo nano /etc/supervisor/conf.d/bitnoc.conf or sudo nano /etc/supervisord.conf
[program:bitnoc]
directory=/home/paul/bitnoc
command=/home/paul/bitnoc/bitnoc/bin/python3 run.py
user=Paul
autostart=True
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/bitnoc/bitnoc.err.log
stdout_logfile=/var/log/bitnoc/bitnoc.out.log

sudo mkdir -p /var/log/bitnoc/
sudo touch /var/log/bitnoc/bitnoc.err.log
sudo touch /var/log/bitnoc/bitnoc.out.log

sudo supervisorctl reload or sudo service supervisord start
sudo systemctl status supervisord.service
sudo systemctl enable supervisord
</pre>
