import time
import os
import re
from datetime import datetime, timedelta
from run_agent import agent_run


# 原始 Suricata fast.log
FAST_LOG_PATH = "/home/student/745_project/fast.log"

# 采集出来的新 fast.log
# 这个文件只保存本轮采集到的 alert
OUTPUT_FAST_LOG_PATH = "/home/student/745_project/collected_fast.log"

# 初始读取范围：参考时间往前多少分钟
# 也是每轮采集结束后的暂停时间
BEFORE_MINUTES = 2

# 这个暂时保留，如果你还想要前后窗口
AFTER_MINUTES = 2

# 触发 alert 后，持续采集多少秒
COLLECT_SECONDS = 60

# system = 使用当前系统时间作为参考时间
# log = 使用 fast.log 里最新日志时间作为参考时间，适合 pcap/lab
TIME_MODE = "log"

# 是否启动时读取已有 fast.log 的最近 BEFORE_MINUTES 内容
READ_EXISTING_ON_START = True

# fast.log 时间格式：
# 09/02/2023-22:29:46.706728
TIME_PATTERN = re.compile(
    r"^(\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2}\.\d+)"
)


def parse_fast_log_time(line):
    """
    从 fast.log 一行中解析时间
    """
    match = TIME_PATTERN.match(line)

    if not match:
        return None

    time_str = match.group(1)

    try:
        return datetime.strptime(time_str, "%m/%d/%Y-%H:%M:%S.%f")
    except ValueError:
        return None


def get_reference_time_from_lines(lines):
    """
    根据 TIME_MODE 获取参考时间
    system: 当前系统时间
    log: 日志中最新的时间
    """
    if TIME_MODE == "system":
        return datetime.now()

    latest_time = None

    for line in lines:
        log_time = parse_fast_log_time(line)

        if log_time is None:
            continue

        if latest_time is None or log_time > latest_time:
            latest_time = log_time

    if latest_time is not None:
        return latest_time

    return datetime.now()


def is_alert_line(line):
    """
    判断这一行是不是 Suricata alert
    fast.log 中 alert 一般都有 [**]
    """
    return "[**]" in line


def filter_recent_logs(lines, reference_time):
    """
    只保留 reference_time - BEFORE_MINUTES 到 reference_time + AFTER_MINUTES 的日志
    """
    start_time = reference_time - timedelta(minutes=BEFORE_MINUTES)
    end_time = reference_time + timedelta(minutes=AFTER_MINUTES)

    matched = []

    for line in lines:
        log_time = parse_fast_log_time(line)

        if log_time is None:
            continue

        if start_time <= log_time <= end_time:
            matched.append(line)

    return matched


def read_all_lines(log_path):
    """
    读取整个 fast.log
    """
    if not os.path.exists(log_path):
        return []

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()


def read_new_lines(log_path, last_position):
    """
    从上次读取的位置继续读取新增内容。
    这个方法适合 /mnt/d 这种 WSL Windows 挂载路径，避免 readline 报错。
    """
    current_size = os.path.getsize(log_path)

    # fast.log 被清空或重新生成
    if current_size < last_position:
        last_position = 0

    if current_size == last_position:
        return [], last_position

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(last_position)
        new_data = f.read()
        last_position = f.tell()

    new_lines = new_data.splitlines()
    return new_lines, last_position


def write_collected_fast_log(lines):
    """
    把本轮采集到的日志写入新的 collected_fast.log 文件
    """
    with open(OUTPUT_FAST_LOG_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip() + "\n")

    print(f"[+] Collected logs saved to: {OUTPUT_FAST_LOG_PATH}")
    print(f"[+] Total collected alerts: {len(lines)}")


def send_to_ids_or_ai(lines):
    """
    这里是占位函数。
    后面你可以把 collected logs 发给 AI 分析模块，
    或者传给你的 IDS analysis / incident response 模块。
    """
    print("[+] Sending collected logs to analysis module...")

    for line in lines[:5]:
        print("[SAMPLE]", line)

    if len(lines) > 5:
        print(f"[+] ... {len(lines) - 5} more lines")


def collect_logs_for_period(log_path, last_position, first_alert_line):
    """
    进入采集阶段：
    从检测到第一条 alert 开始，持续采集 COLLECT_SECONDS 秒。
    """
    print("[+] Alert detected. Entering log collection stage...")
    print(f"[+] Collection duration: {COLLECT_SECONDS} seconds")
    print("-" * 80)

    collected_lines = []

    if first_alert_line:
        collected_lines.append(first_alert_line)

    collection_start = time.time()
    collection_end = collection_start + COLLECT_SECONDS

    while time.time() < collection_end:
        try:
            new_lines, last_position = read_new_lines(log_path, last_position)

            for line in new_lines:
                if is_alert_line(line):
                    collected_lines.append(line)
                    print("[COLLECTING]", line.strip())

            time.sleep(1)

        except OSError as e:
            print(f"[-] OSError while collecting log: {e}")
            time.sleep(1)

    print("-" * 80)
    print("[+] Log collection stage finished.")

    return collected_lines, last_position


def cooldown_with_processing(collected_lines):
    """
    采集结束后进入暂停阶段。

    顺序：
    1. 开始暂停
    2. 暂停期间生成 collected_fast.log
    3. 暂停期间发送给分析模块
    4. 暂停结束后继续从原来的 last_position 往后读取

    注意：
    这里不会跳到 fast.log 文件末尾。
    所以暂停期间产生的新 alert 不会被 skip，
    会在暂停结束后继续被读取。
    """
    cooldown_seconds = BEFORE_MINUTES * 60

    print(f"[+] IDS monitor paused for {BEFORE_MINUTES} minutes.")
    print("[+] Processing collected logs during cooldown...")
    print("[+] New alerts generated during cooldown will be processed after cooldown.")
    print("-" * 80)

    cooldown_start = time.time()

    # 暂停期间生成 collected_fast.log
    write_collected_fast_log(collected_lines)

    # 暂停期间发送给分析模块
    # send_to_ids_or_ai(collected_lines)
    agent_run()

    # 计算处理已经花了多久
    elapsed = time.time() - cooldown_start
    remaining = cooldown_seconds - elapsed

    if remaining > 0:
        print(f"[+] Remaining cooldown time: {int(remaining)} seconds")
        time.sleep(remaining)

    print("[+] Cooldown finished. Resuming monitoring...")
    print("[+] Alerts generated during cooldown will now be read.")
    print("-" * 80)


def monitor_fast_log(log_path):
    print("[+] IDS monitor started")
    print(f"[+] Monitoring file: {log_path}")
    print(f"[+] Output collected log: {OUTPUT_FAST_LOG_PATH}")
    print(f"[+] Time mode: {TIME_MODE}")
    print(f"[+] Initial read window: reference time - {BEFORE_MINUTES} minutes")
    print(f"[+] Collection duration: {COLLECT_SECONDS} seconds")
    print(f"[+] Cooldown after collection: {BEFORE_MINUTES} minutes")
    print("-" * 80)

    while not os.path.exists(log_path):
        print(f"[-] Log file not found: {log_path}")
        time.sleep(2)

    # 启动时先定位文件末尾位置
    last_position = os.path.getsize(log_path)

    # 启动时读取 fast.log 中最近 BEFORE_MINUTES 的日志
    if READ_EXISTING_ON_START:
        all_lines = read_all_lines(log_path)
        reference_time = get_reference_time_from_lines(all_lines)
        recent_lines = filter_recent_logs(all_lines, reference_time)

        print(f"[+] Reference time: {reference_time}")
        print(f"[+] Existing recent logs found: {len(recent_lines)}")

        # 如果启动时最近日志里已经有 alert，直接触发采集
        for line in recent_lines:
            if is_alert_line(line):
                print("[INITIAL ALERT]", line.strip())

                collected_lines, last_position = collect_logs_for_period(
                    log_path=log_path,
                    last_position=last_position,
                    first_alert_line=line
                )

                cooldown_with_processing(collected_lines)

                break

    print("[+] Waiting for new Suricata alerts...")
    print("-" * 80)

    while True:
        try:
            new_lines, last_position = read_new_lines(log_path, last_position)

            for line in new_lines:
                if not is_alert_line(line):
                    continue

                log_time = parse_fast_log_time(line)

                if log_time is None:
                    continue

                # 实时监控阶段：
                # 一旦发现新的 alert，就进入采集阶段
                print("[TRIGGER ALERT]", line.strip())

                collected_lines, last_position = collect_logs_for_period(
                    log_path=log_path,
                    last_position=last_position,
                    first_alert_line=line
                )

                cooldown_with_processing(collected_lines)

                # cooldown 后跳出当前 for，重新进入 while 继续监控
                break

            time.sleep(1)

        except OSError as e:
            print(f"[-] OSError while reading log: {e}")
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[+] IDS monitor stopped.")
            break


if __name__ == "__main__":
    monitor_fast_log(FAST_LOG_PATH)
