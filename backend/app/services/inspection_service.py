import logging
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.config import settings, DEVICE_TYPE_MAP

logger = logging.getLogger(__name__)

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
    """根据设备类型建立 SSH 连接，支持多厂商"""
    net_type = DEVICE_TYPE_MAP.get(device.device_type, "hp_comware")
    device_info = {
        "device_type": net_type,
        "host": device.ip,
        "username": device.username,
        "password": device.password,
        "port": getattr(device, "port", None) or settings.DEVICE_SSH_PORT,
        "timeout": settings.DEVICE_SSH_TIMEOUT,
    }
    try:
        return ConnectHandler(**device_info)
    except NetMikoTimeoutException:
        logger.warning("SSH 连接超时: %s:%s (%s)", device.ip, device_info["port"], getattr(device, "device_type", "unknown"))
        return None
    except NetMikoAuthenticationException:
        logger.warning("SSH 认证失败: %s 用户名/密码错误", device.ip)
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
        up = output.count("up")
        down = output.count("down")
        status = "pass" if down == 0 else ("warning" if down < 5 else "fail")
        return {"name": "interfaces", "status": status, "detail": f"接口: {up} up, {down} down"}
    elif check_name == "hardware":
        normal = output.count("Normal") + output.count("ok") + output.count("OK")
        status = "pass" if normal > 0 else "warning"
        return {"name": "hardware", "status": status, "detail": "硬件状态正常" if normal > 0 else "部分硬件异常"}
    elif check_name == "uptime":
        lines = [l.strip() for l in output.split("\n") if l.strip()]
        uptime_line = lines[0] if lines else "未知"
        return {"name": "uptime", "status": "pass", "value": uptime_line, "detail": f"运行时间: {uptime_line}"}
    return {"name": check_name, "status": "pass", "detail": "检查完成"}
