"""解析器测试：验证 CPU、内存、接口、硬件、运行时间等命令输出解析"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.inspection_service import _parse_check


def test_parse_cpu_pass():
    output = "CPU usage: 23.5%"
    result = _parse_check("cpu", output, "hp_comware")
    assert result["status"] == "pass"
    assert result["value"] == 23.5


def test_parse_cpu_warning():
    output = "CPU usage: 75.0%"
    result = _parse_check("cpu", output, "hp_comware")
    assert result["status"] == "warning"


def test_parse_cpu_fail():
    output = "CPU usage: 95.0%"
    result = _parse_check("cpu", output, "hp_comware")
    assert result["status"] == "fail"


def test_parse_memory():
    output = "Memory usage: 45.2%"
    result = _parse_check("memory", output, "hp_comware")
    assert result["status"] == "pass"
    assert result["value"] == 45.2


def test_parse_interfaces_h3c():
    """H3C display interface brief 输出解析"""
    output = """Brief information on interface(s) under route mode:
Link: ADM - administratively down; Stby - standby
Interface            Link Protocol Main IP         Description
GE1/0/1              UP   up       10.0.0.1        -
GE1/0/2              DOWN down     -               -
GE1/0/3              UP   up       10.0.0.2        Uplink
GE1/0/4              ADM  down     -               shutdown"""
    result = _parse_check("interfaces", output, "hp_comware")
    # UP=2, DOWN=1, ADM=1(不计入down)
    assert "2 up" in result["detail"]
    assert "1 down" in result["detail"]
    assert result["status"] == "pass"


def test_parse_interfaces_all_down():
    """所有端口都 down 时应该 fail"""
    output = """Interface            Link Protocol Main IP
GE1/0/1              DOWN down     -
GE1/0/2              DOWN down     -"""
    result = _parse_check("interfaces", output, "hp_comware")
    assert result["status"] == "fail"


def test_parse_hardware_pass():
    """display device 输出包含 Normal"""
    output = """Slot No.   Board Type          Status
1          Main Processing Unit Normal
2          Interface Module     Normal"""
    result = _parse_check("hardware", output, "hp_comware")
    assert result["status"] == "pass"
    assert result["detail"] == "硬件状态正常"


def test_parse_hardware_fault():
    """display device 输出包含 Fault"""
    output = """Slot No.   Board Type          Status
1          Main Processing Unit Normal
2          Interface Module     Fault"""
    result = _parse_check("hardware", output, "hp_comware")
    assert result["status"] == "warning"
    assert "Fault" in result["detail"]


def test_parse_hardware_fallback_pass():
    """Cisco show inventory 无状态关键词时默认通过"""
    output = """NAME: "GigabitEthernet0/0", DESCR: "Gigabit Ethernet"
PID: WS-C2960X-24PS-L"""
    result = _parse_check("hardware", output, "cisco_ios")
    assert result["status"] == "pass"


def test_parse_uptime():
    """display version 中提取 uptime 行"""
    output = """H3C Comware Software, Version 7.1.070, Release 6126P20
Copyright (c) 2004-2023 New H3C Technologies Co., Ltd.
uptime is 2 weeks, 3 days, 4 hours, 10 minutes"""
    result = _parse_check("uptime", output, "hp_comware")
    assert "2 weeks" in result["detail"] or "运行时间" in result["detail"]


def test_parse_uptime_no_uptime_line():
    """无 uptime 行时回退取第一行"""
    output = """Unknown device version string
some other output"""
    result = _parse_check("uptime", output, "hp_comware")
    assert "Unknown" in result["detail"]


def test_parse_cpu_unparseable():
    """无法解析 CPU 时返回 warning"""
    result = _parse_check("cpu", "no percentage sign here", "hp_comware")
    assert result["status"] == "warning"
