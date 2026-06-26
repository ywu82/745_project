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
Please read and use this file:

/home/allen/.openclaw/workspace/ids-analysis/ids_log_analysis.md

This file is a specification for an IDS/SIEM/log-analysis skill. Please configure it as a usable OpenClaw skill.

Requirements:

1. Create the skill directory:
/home/allen/.openclaw/workspace/skills/ids-analysis/

2. Create the main skill file:
/home/allen/.openclaw/workspace/skills/ids-analysis/SKILL.md

3. `SKILL.md` must include YAML frontmatter:
name: ids-analysis
description: Analyze IDS, SIEM, Suricata, Zeek, firewall, DNS, and security logs with cautious SOC-style reporting.

4. Convert the core content from `ids_log_analysis.md` into `SKILL.md`. Do not blindly copy the whole file. Keep these requirements:
- Act as a SOC analyst.
- Support directory input, single log file input, multiple log file input, and raw log content.
- The final output must start with `[GPT analyzed]:`.
- Do not overclaim that an attack is confirmed unless the logs clearly prove it.
- Clearly separate evidence from inference.
- Explain the limitations of the available logs.
- Provide practical mitigation recommendations.
- The skill should work well when called from Python through `openclaw agent --message` to analyze a specified log file.

5. If the original file is too long, place the detailed rules here:
/home/allen/.openclaw/workspace/skills/ids-analysis/references/ids_log_analysis.md

Then make `SKILL.md` explain when to read that reference file.

6. After creating the skill, verify:
- `SKILL.md` exists.
- The YAML frontmatter is valid.
- The skill name is `ids-analysis`.
- The description is clear enough for the agent to trigger this skill for IDS/log-analysis tasks.

7. Finally, tell me which files you created or modified, and show me the recommended prompt I should use later to analyze a log file with this skill.

```
