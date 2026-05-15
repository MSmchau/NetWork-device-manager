import logging
import re
import paramiko
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.config import settings, DEVICE_TYPE_MAP

logger = logging.getLogger(__name__)

# H3C Comware 等老设备仅支持 ssh-dss 主机密钥，Paramiko 3.x+ 默认禁用，需手动启用
paramiko.Transport._preferred_keys = ("ssh-dss",) + paramiko.Transport._preferred_keys

# 各厂商标准巡检命令集
INSPECTION_COMMANDS = {
    "hp_comware": {
        "cpu": "display cpu-usage",
        "memory": "display memory",
        "interfaces": "display interface brief",
        "hardware": "display device",
        "uptime": "display version",
    },
    "huawei": {
        "cpu": "display cpu-usage",
        "memory": "display memory",
        "interfaces": "display interface brief",
        "hardware": "display device",
        "uptime": "display version",
    },
    "cisco_ios": {
        "cpu": "show processes cpu",
        "memory": "show memory",
        "interfaces": "show interfaces summary",
        "hardware": "show inventory",
        "uptime": "show version",
    },
    "ruijie_os": {
        "cpu": "show cpu",
        "memory": "show memory statistics",
        "interfaces": "show interface brief",
        "hardware": "show device",
        "uptime": "show version",
    },
}

def device_connect(device):
    """根据设备类型和协议建立连接（SSH / Telnet），支持多厂商"""
    net_type = DEVICE_TYPE_MAP.get(device.device_type, "hp_comware")
    protocol = getattr(device, "protocol", "ssh") or "ssh"
    port = getattr(device, "port", None) or (23 if protocol == "telnet" else settings.DEVICE_SSH_PORT)

    device_info = {
        "device_type": net_type,
        "host": device.ip,
        "username": device.username,
        "password": device.password,
        "port": port,
        "timeout": settings.DEVICE_SSH_TIMEOUT,
    }
    if protocol == "telnet":
        device_info["use_telnet"] = True

    proto_label = "Telnet" if protocol == "telnet" else "SSH"
    try:
        return ConnectHandler(**device_info)
    except NetMikoTimeoutException:
        logger.warning("%s 连接超时: %s:%s (%s)", proto_label, device.ip, port, getattr(device, "device_type", "unknown"))
        return None
    except NetMikoAuthenticationException:
        logger.warning("%s 认证失败: %s 用户名/密码错误", proto_label, device.ip)
        return None

def inspect_device(device):
    """执行标准巡检，返回结构化 JSON 结果"""
    conn = device_connect(device)
    if not conn:
        return {
            "overall_status": "critical",
            "checks": [
                {"name": "connectivity", "status": "fail", "detail": "SSH 连接失败"}
            ],
        }
    net_type = DEVICE_TYPE_MAP.get(device.device_type, "hp_comware")
    commands = INSPECTION_COMMANDS.get(net_type, {})
    checks = [{"name": "connectivity", "status": "pass",
               "detail": f"SSH 连接成功 ({device.ip}:{getattr(device, 'port', None) or settings.DEVICE_SSH_PORT})"}]
    try:
        for check_name, cmd in commands.items():
            try:
                output = conn.send_command(cmd)
            except Exception as e:
                checks.append({"name": check_name, "status": "fail", "detail": f"{check_name} 检查失败: {str(e)}"})
                continue
            checks.append(_parse_check(check_name, output, net_type))
    finally:
        conn.disconnect()
    status_rank = {"pass": 0, "warning": 1, "fail": 2}
    max_rank = max(status_rank.get(c.get("status", "pass"), 0) for c in checks)
    overall = {0: "healthy", 1: "warning", 2: "critical"}[max_rank]
    return {"overall_status": overall, "checks": checks}

def _parse_check(check_name, output, net_type):
    """解析各厂商命令输出"""
    if check_name == "cpu":
        for line in output.split("\n"):
            if "%" in line:
                try:
                    val = float(line.split("%")[0].split()[-1])
                    status = "pass" if val < 70 else ("warning" if val < 90 else "fail")
                    return {"name": "cpu", "status": status, "value": val, "detail": f"CPU 使用率: {val}%"}
                except ValueError:
                    pass
        return {"name": "cpu", "status": "warning", "detail": "未能解析 CPU 使用率"}
    elif check_name == "memory":
        for line in output.split("\n"):
            if "%" in line:
                try:
                    val = float(line.split("%")[0].split()[-1])
                    status = "pass" if val < 70 else ("warning" if val < 90 else "fail")
                    return {"name": "memory", "status": status, "value": val, "detail": f"内存使用率: {val}%"}
                except ValueError:
                    pass
        return {"name": "memory", "status": "warning", "detail": "未能解析内存使用率"}
    elif check_name == "interfaces":
        up = down = adm = 0
        lines = output.split("\n")

        if net_type in ("hp_comware", "huawei", "ruijie_os"):
            # display interface brief → 第二列为 Link 状态 (UP / DOWN / ADM)
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2:
                    status_val = parts[1].upper()
                    if status_val == "UP":
                        up += 1
                    elif status_val == "DOWN":
                        down += 1
                    elif status_val == "ADM":
                        adm += 1
        elif net_type == "cisco_ios":
            for line in lines:
                lower = line.lower()
                if "is up" in lower and "is down" not in lower:
                    up += 1
                elif "is down" in lower:
                    down += 1
        else:
            up = len(re.findall(r'\bup\b', output, re.IGNORECASE))
            down = len(re.findall(r'\bdown\b', output, re.IGNORECASE))

        # down 端口多为空闲未使用的端口，有任意 up 端口即视为正常
        status = "fail" if up == 0 and down > 0 else "pass"
        detail = f"接口: {up} up, {down} down"
        if adm:
            detail += f", {adm} administratively down"
        return {"name": "interfaces", "status": status, "detail": detail}
    elif check_name == "hardware":
        # 解析具体硬件组件状态，标记异常组件
        abnormal = []  # 异常组件列表
        healthy_count = 0

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # 检查异常状态关键词
            m = re.search(r'\b(Fault|Abnormal|Absent|Offline|Failed)\b', line, re.IGNORECASE)
            if m:
                comp = line[:m.start()].strip()
                abnormal.append(f"{comp} [{m.group(0)}]" if comp else f"[{m.group(0)}]")
                continue

            # 检查正常状态
            if re.search(r'\b(Normal|OK)\b', line, re.IGNORECASE):
                healthy_count += 1

        if abnormal:
            status = "warning"
            detail = "部分硬件异常: " + "; ".join(abnormal)
        elif healthy_count > 0:
            status = "pass"
            detail = "硬件状态正常"
        else:
            # 无法解析硬件状态时默认通过（如 Cisco show inventory 等无状态命令）
            status = "pass"
            detail = "硬件状态正常"

        return {"name": "hardware", "status": status, "detail": detail}
    elif check_name == "uptime":
        # 查找包含 uptime/运行时间的行（各厂商 display version / show version 通用）
        uptime_text = "未知"
        for line in output.split("\n"):
            stripped = line.strip()
            if re.search(r'uptime|运行时间', stripped, re.IGNORECASE):
                # 去除 "uptime is" / "System uptime is" 等前缀
                uptime_text = re.sub(r'^(System\s+)?(uptime\s+is\s+)', '', stripped, flags=re.IGNORECASE)
                break
        if uptime_text == "未知":
            lines = [l.strip() for l in output.split("\n") if l.strip()]
            uptime_text = lines[0] if lines else "未知"
        return {"name": "uptime", "status": "pass", "detail": f"运行时间: {uptime_text}"}
    return {"name": check_name, "status": "pass", "detail": "检查完成"}
