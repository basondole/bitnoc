# bitnoc

### Dependacies
- Python 3.7 or later
- Python virtual environment

## Installation
These instructions assume you already have python installed and python vitual environment module installed

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
│   │   │   ├── d3.v3.min.js
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
│       ├── logical-view-with-interfaces.html
│       ├── login.html
│       ├── register.html
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

15 directories, 55 files
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
 * Debugger PIN: 111-496-829
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 </pre>
 
 Open the browser and access <code>http://127.0.0.1:5000/</code> or <code>http://localhost:5000/</code>
 
