# bitnoc

## Installation

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

basondole → c:\Users\u\Desktop\basohub\github
cd bitnoc

basondole → c:\Users\u\Desktop\basohub\github\bitnoc
ls
app.py  application  core  other  requirements.txt  windows
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

(bitnoc) basondole → c:\Users\u\Desktop\basohub\github\bitnoc
