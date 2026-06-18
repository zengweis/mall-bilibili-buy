#!/usr/bin/env python3
"""
NTP时间同步 + 精准定时触发器
用法: from timer import ntp_time, wait_until
"""

import time
import struct
import socket


# ==================== NTP 时间同步 ====================

NTP_SERVERS = [
    "ntp.aliyun.com",
    "ntp.tencent.com",
    "time.apple.com",
    "pool.ntp.org",
]
NTP_PORT = 123
NTP_EPOCH = 2208988800  # 1970-01-01 00:00:00


def _ntp_request(server: str, timeout: float = 2.0) -> float:
    """向NTP服务器请求时间，返回Unix时间戳"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    # NTP请求包 (48字节, 头部3字节 = 0x1B 表示客户端请求)
    packet = b'\x1b' + b'\x00' * 47

    try:
        sock.sendto(packet, (server, NTP_PORT))
        data, _ = sock.recvfrom(1024)
        # 提取传输时间戳 (第40-48字节)
        t = struct.unpack('!12I', data)[10]
        return t - NTP_EPOCH
    except Exception:
        return None
    finally:
        sock.close()


def ntp_time(fast: bool = True) -> float:
    """
    获取NTP同步后的当前时间
    fast=True: 只请求1个服务器
    fast=False: 请求多个取平均
    """
    times = []
    servers = NTP_SERVERS[:1] if fast else NTP_SERVERS

    for s in servers:
        t = _ntp_request(s, timeout=1.5)
        if t:
            times.append(t)

    if times:
        offset = sum(t - time.time() for t in times) / len(times)
        return time.time() + offset
    else:
        print("⚠️ NTP失败，使用本地时间")
        return time.time()


# ==================== 定时触发器 ====================

def wait_until(
    target_time: float,
    lead_ms: int = 200,
    check_interval: float = 0.01,
) -> float:
    """
    精准等待到目标时间
    :param target_time: 目标Unix时间戳
    :param lead_ms: 提前多少ms开始忙等 (越小越准但占CPU)
    :param check_interval: 提前期之前的检查间隔
    :return: 实际触发时间
    """
    target = target_time - lead_ms / 1000.0

    while True:
        now = time.time()
        if now >= target:
            break
        remaining = target - now
        if remaining > 1.0:
            time.sleep(0.5)
        elif remaining > 0.1:
            time.sleep(0.01)
        else:
            # 最后阶段: 忙等(busy-wait)精准到毫秒
            while time.time() < target_time:
                pass
            break

    return time.time()


def wait_until_ntp(
    target_time: float,
    lead_ms: int = 200,
) -> dict:
    """
    NTP同步 + 精准等待
    返回: {"trigger_time": 实际触发时间, "offset_ms": NTP偏差, "drift_ms": 实际偏差}
    """
    # Step 1: NTP同步
    ntp_now = ntp_time(fast=True)
    offset_ms = (ntp_now - time.time()) * 1000
    print(f"🕐 NTP同步: 偏差={offset_ms:+.1f}ms")

    # Step 2: 计算等待时间
    local_target = target_time - (ntp_now - time.time())
    wait_seconds = local_target - time.time()
    print(f"⏳ 倒计时: {wait_seconds:.1f}s")

    # Step 3: 等待
    trigger = wait_until(local_target, lead_ms=lead_ms)
    drift = (trigger - target_time) * 1000

    result = {
        "trigger_time": trigger,
        "offset_ms": offset_ms,
        "drift_ms": drift,
    }
    print(f"🎯 触发! drift={drift:+.1f}ms")
    return result


# ==================== 倒计时显示 ====================

def countdown(target_time: float):
    """带显示的倒计时"""
    import sys
    while True:
        remaining = target_time - time.time()
        if remaining <= 0:
            print(f"\r🎯 开抢!                    ")
            break
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        ms = int((remaining % 1) * 100)
        print(f"\r⏳ {mins:02d}:{secs:02d}.{ms:02d}  ", end="", flush=True)
        time.sleep(0.05)


if __name__ == "__main__":
    # 测试: 5秒后触发
    print("NTP时间同步测试\n")
    target = ntp_time() + 5
    countdown(target)
    result = wait_until_ntp(target)
    print(f"结果: {result}")
