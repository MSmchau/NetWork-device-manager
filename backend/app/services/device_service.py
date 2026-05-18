import os, datetime, logging
from app.config import settings, DEVICE_TYPE_MAP
from app.services.inspection_service import device_connect

logger = logging.getLogger(__name__)

# 各厂商 CPU/内存查询命令映射
STATUS_COMMANDS = {
    "hp_comware": {"cpu": "display cpu-usage", "mem": "display memory"},
    "huawei": {"cpu": "display cpu-usage", "mem": "display memory"},
    "cisco_ios": {"cpu": "show processes cpu", "mem": "show memory"},
    "ruijie_os": {"cpu": "show cpu", "mem": "show memory statistics"},
}

def _parse_cpu(output, net_type):
    for line in output.split("\n"):
        if "%" in line:
            try:
                return float(line.split("%")[0].split()[-1])
            except ValueError:
                pass
    return 0.0

def _parse_mem(output, net_type):
    for line in output.split("\n"):
        if "%" in line:
            try:
                return float(line.split("%")[0].split()[-1])
            except ValueError:
                pass
    return 0.0

def get_device_status(device):
    net_type = DEVICE_TYPE_MAP.get(device.device_type, "hp_comware")
    conn = device_connect(device)
    if not conn:
        return {"online": False, "cpu": 0, "mem": 0}
    try:
        cmds = STATUS_COMMANDS.get(net_type, STATUS_COMMANDS["hp_comware"])
        cpu_out = conn.send_command(cmds["cpu"])
        mem_out = conn.send_command(cmds["mem"])
        cpu = _parse_cpu(cpu_out, net_type)
        mem = _parse_mem(mem_out, net_type)
        return {"online": True, "cpu": cpu, "mem": mem}
    except Exception as e:
        logger.error("获取设备 %s(%s) 状态异常: %s", device.name, device.ip, e)
        return {"online": False, "cpu": 0, "mem": 0}
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass

# 各厂商配置备份命令映射
BACKUP_COMMANDS = {
    "hp_comware": "display current-configuration",
    "huawei": "display current-configuration",
    "cisco_ios": "show running-config",
    "ruijie_os": "show running-config",
}

def backup_config(device):
    """备份设备配置，支持多厂商"""
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
    conn = device_connect(device)
    if not conn:
        return False, ""
    try:
        net_type = DEVICE_TYPE_MAP.get(device.device_type, "hp_comware")
        cmd = BACKUP_COMMANDS.get(net_type, "display current-configuration")
        dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{device.name}_{dt}.cfg"
        path = os.path.join(settings.BACKUP_DIR, filename)
        out = conn.send_command(cmd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        return True, path
    except Exception as e:
        return False, str(e)
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass
