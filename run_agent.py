import subprocess
from pathlib import Path
import json


FAST_LOG_PATH = "/home/student/745_project/collected_fast.log"
SLACK_SOC_TARGET = "channel:C0BBUL7A4BF"
SLACK_PERSONAL_TARGET = "channel:D0BCSAPKCV6"


def run_command(command):
    return subprocess.run(command, text=True, capture_output=True)


def check_openclaw_gateway_status(print_output=True):
    print("[INFO] Checking OpenClaw gateway status...")

    result = run_command([
        "openclaw",
        "gateway",
        "status"
    ])

    if result.returncode != 0:
        print("[WARN] Failed to check OpenClaw gateway status:")
        print(result.stderr)
        return False

    status_output = result.stdout

    if print_output:
        print(status_output)

    required_indicators = [
        "Runtime: running",
        "Connectivity probe: ok",
        "Service: systemd user (enabled)"
    ]

    missing = [
        indicator for indicator in required_indicators
        if indicator not in status_output
    ]

    if missing:
        print("[WARN] OpenClaw gateway is not fully ready.")
        print("[WARN] Missing indicators:")
        for item in missing:
            print(f"  - {item}")
        return False

    print("[INFO] OpenClaw gateway is already running and reachable.")
    return True


def restart_openclaw_gateway():
    print("[INFO] Restarting OpenClaw gateway...")

    result = run_command([
        "openclaw",
        "gateway",
        "restart"
    ])

    if result.returncode != 0:
        print("[ERROR] Failed to restart OpenClaw gateway:")
        print(result.stderr)
        return False

    print("[INFO] OpenClaw gateway restart command completed.")
    return True


def ensure_openclaw_gateway_ready():
    """
    First check gateway status.
    If it is already running, do nothing.
    If it is not running or not reachable, restart it and check again.
    """

    if check_openclaw_gateway_status(print_output=True):
        return True

    print("[INFO] Gateway is not ready. Trying to restart it...")

    if not restart_openclaw_gateway():
        return False

    print("[INFO] Re-checking OpenClaw gateway status after restart...")

    return check_openclaw_gateway_status(print_output=True)


def build_prompt(log_path):
#     return f"""
# Use skill ids_log_analysis.

# Analyze this single log file:
# {log_path}

# Follow the skill's required output format exactly.
# After the analysis, send the final result to Slack channel `soc` and also send it to my personal Slack destination.

# Attach the analyzed log file to the Slack replies. If additional report artifacts are useful, also include `analysis.md` and `analysis.json`.

# Follow the skill's required output format exactly.
# """.strip()

    return f"""
Use skill ids_log_analysis.

Analyze this single log file:
{log_path}

Required actions:
1. Perform the analysis.
2. Format the result exactly as required.
3. Send the final analysis to Slack channel #soc.
4. Also send the same result to Slack user idevelper1994.
5. Attach the original analyzed log file.
6. If generated, also attach analysis.md and analysis.json.
7. Report delivery success or failure for each target.

    """.strip()


# def run_openclaw_agent(prompt_text):
#     print("[INFO] Sending prompt to OpenClaw agent...")
#     command = [
#     "openclaw",
#     "agent",
#     "--agent", "main",
#     "--message", prompt_text,
#     "--deliver",
#     "--reply-channel", "slack",
#     "--reply-to", "#soc",
#     "--json"
#     ]

#     result = run_command(command)

#     if result.returncode != 0:
#         print("[ERROR] OpenClaw agent failed:")
#         print(result.stderr)
#         return result

#     print("[INFO] OpenClaw agent result:")
#     print(result.stdout)

#     return result




def run_openclaw_agent(prompt_text):
    print("[INFO] Sending prompt to OpenClaw agent...")
    command = [
        "openclaw",
        "agent",
        "--agent", "main",
        "--message", prompt_text,
        "--json",
    ]

    result = run_command(command)

    if result.returncode != 0:
        print("[ERROR] OpenClaw agent failed:")
        print(result.stderr)
        return result

    print("[INFO] OpenClaw agent result:")
    print(result.stdout)
    return result


def send_slack_message_with_log(target, analysis_text, log_path):
    command = [
        "openclaw",
        "message",
        "send",
        "--channel", "slack",
        "--target", target,
        "--message", analysis_text,
        "--media", str(log_path),
        "--json",
    ]
    return run_command(command)


# def extract_analysis_text(agent_stdout):
#     try:
#         data = json.loads(agent_stdout)
#     except json.JSONDecodeError:
#         return agent_stdout.strip()

#     if isinstance(data, dict):
#         for key in ["finalText", "text", "message", "output"]:
#             value = data.get(key)
#             if isinstance(value, str) and value.strip():
#                 return value.strip()

#     return agent_stdout.strip()

def extract_analysis_text(agent_stdout):
    try:
        data = json.loads(agent_stdout)
    except json.JSONDecodeError:
        return agent_stdout.strip()

    def find_text(obj):
        if isinstance(obj, dict):
            for key in ["finalText", "text", "message", "output", "content"]:
                value = obj.get(key)
                if isinstance(value, str) and value.strip():
                    if value.strip().startswith("[GPT analyzed]:") or "Summary of Activity" in value:
                        return value.strip()

            for value in obj.values():
                result = find_text(value)
                if result:
                    return result

        elif isinstance(obj, list):
            for item in obj:
                result = find_text(item)
                if result:
                    return result

        return None

    result = find_text(data)
    if result:
        return result

    raise ValueError("Could not extract analysis text from OpenClaw JSON output")



# def send_slack_message_with_log(target, analysis_text, log_path):
#     command = [
#         "openclaw",
#         "message",
#         "send",
#         "--channel", "slack",
#         "--reply-to", "#soc",
#         "--target", target,
#         "--message", analysis_text,
#         "--media", str(log_path),
#         "--json"
#     ]
#     return run_command(command)    


# if __name__ == "__main__":
#     log_file = Path(FAST_LOG_PATH)

#     if not log_file.exists():
#         print(f"[ERROR] log file not found: {FAST_LOG_PATH}")
#     else:
#         if ensure_openclaw_gateway_ready():
#             prompt = build_prompt(FAST_LOG_PATH)
#             run_openclaw_agent(prompt)
#         else:
#             print("[ERROR] OpenClaw gateway is not ready. Analysis was not started.")

def agent_run(log_path=FAST_LOG_PATH):
    log_file = Path(log_path)

    if not log_file.exists():
        print(f"[ERROR] log file not found: {log_path}")
        return False

    if ensure_openclaw_gateway_ready():
        prompt = build_prompt(log_path)
        agent_result  = run_openclaw_agent(prompt)





        if agent_result.returncode != 0:
            print(agent_result.stderr)
        else:
            analysis_text = extract_analysis_text(agent_result.stdout)

            soc_result = send_slack_message_with_log(
                SLACK_SOC_TARGET,
                analysis_text,
                FAST_LOG_PATH
            )

            personal_result = send_slack_message_with_log(
                SLACK_PERSONAL_TARGET,
                analysis_text,
                FAST_LOG_PATH
            )

            print("SOC:", soc_result.stdout or soc_result.stderr)
            print("PERSONAL:", personal_result.stdout or personal_result.stderr)




        return True

    print("[ERROR] OpenClaw gateway is not ready. Analysis was not started.")
    return False


if __name__ == "__main__":
    agent_run()
