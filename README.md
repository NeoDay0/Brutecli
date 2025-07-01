
# Brutecli
auto brute forcer 
🎯 What It Does
Feature	Details
Protocols	SSH, FTP, HTTP form-based logins
Word-lists	50× common usernames & passwords baked into the code
Load custom -U users.txt / -P rockyou.txt lists any time
Wizard UI	Launch the script with no arguments for an interactive menu—perfect for quick one-off tests
Batch mode	Feed a YAML file with multiple jobs: brutecli.py -B tasks.yaml --loop (re-runs forever with delay)
No hard deps	Falls back to plain text if termcolor is missing; imports heavy libs only when needed
Packaging	Single-file script blends perfectly into a PyInstaller binary (-F) for drop-n-run deployments
🛠 Requirements

    Python 3.8+

    Optional (recommended):

        paramiko – SSH support

        requests – HTTP form testing

        PyYAML – batch/automation

        termcolor – pretty colours

    Kali / Debian / Ubuntu: install the distro packages and avoid the PEP 668 “externally-managed” error

    sudo apt update
    sudo apt install python3-termcolor python3-paramiko python3-requests python3-yaml

Or use a venv:

python3 -m venv venv
source venv/bin/activate
pip install termcolor paramiko requests pyyaml

🚀 Quick Start

# 1. Clone
git clone https://github.com/yourname/brutecli.git
cd brutecli

# 2. Run the wizard
python brutecli.py

Sample session:

 ____                 _          ____ _     ___ 
| __ )  ___  __ _  __| | ___ _ _| __ ) |   |_ _|
|  _ \ / _ \/ _` |/ _` |/ _ \ '__|  _ \ |    | | 
| |_) |  __/ (_| | (_| |  __/ |  | |_) | |___| | 
|____/ \___|\__,_|\__,_|\___|_|  |____/|_____|___|

Protocol (ssh / ftp / http) [ssh]: 
Target host/IP: 10.0.0.12
Threads [4]: 8
Timeout seconds [5]: 
Single username (blank = userlist): root
Custom passlist file (blank = built-in): rockyou-top100.txt
SSH port [22]: 
[•] 100 combos → SSH 10.0.0.12 (8 threads)
[+] root:P@ssw0rd
[✓] Finished in 1.2 s

💻 Command-line Examples

# SSH with built-in lists
python brutecli.py ssh 192.168.56.10 -t 8

# FTP, custom passwords, built-in users
python brutecli.py ftp ftp.target.com -P rockyou.txt

# HTTP form, fixed user, baked-in passwords
python brutecli.py http https://site/login --username admin --success Welcome

Batch automation

# tasks.yaml
- protocol: ssh
  target: 192.168.56.10
  username: root
  passlist: mini_pw.txt
  port: 22
  threads: 4
  timeout: 5

- protocol: http
  target: intranet
  url: https://intranet.local/login
  userlist: corp_users.txt
  passlist: mini_pw.txt
  user_field: user
  pass_field: pass
  success: "Dashboard"
  threads: 6
  timeout: 5

python brutecli.py -B tasks.yaml --loop --delay 300   # every 5 min forever

📦 Build a Stand-alone Binary

pip install pyinstaller
pyinstaller -F brutecli.py        # yields dist/brutecli  (or brutecli.exe)

The binary contains all imported libraries and your word-lists—no Python needed on the target box.
🤝 Contributing

    Fork & branch: git checkout -b feature/my-cool-idea

    Hack away—stick to 4-space indents and keep zero external deps unless strictly necessary.

    PR into dev branch with a clear description and usage notes.

Bug reports → Issues tab.
Feature chat → Discussions.
