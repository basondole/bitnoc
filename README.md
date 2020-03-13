# bitnoc

### Dependacies
- Python 3.7 or later
- Python virtual environment

## Installation
These instructions assume you already have python installed and python vitual environment module installed

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
(bitnoc) [root@basondole bitnoc]# python3 run.py 
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
