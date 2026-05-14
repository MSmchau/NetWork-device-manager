import { useEffect, useState } from 'react';
import { Table, Tag, Button, Space, Select, Popconfirm, message, Switch, InputNumber, Card, Divider } from 'antd';
import { CloudDownloadOutlined, DeleteOutlined, PlayCircleOutlined, ClockCircleOutlined, EyeOutlined } from '@ant-design/icons';
import { getBackups, triggerBackup, triggerBackupAll, deleteBackup, getSchedule, updateSchedule, getDownloadUrl } from '../api/backup';
import { getDevices } from '../api/device';

interface BackupItem {
  id: number;
  device_id: number;
  filename: string;
  status: string;
  created_at: string;
}

export default function BackupPage() {
  const [data, setData] = useState<BackupItem[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [backingUp, setBackingUp] = useState(false);
  const [backingUpAll, setBackingUpAll] = useState(false);

  // 定时备份状态
  const [schedEnabled, setSchedEnabled] = useState(false);
  const [schedInterval, setSchedInterval] = useState(3600);
  const [scheduleLoading, setScheduleLoading] = useState(false);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [devRes, backupRes, schedRes] = await Promise.all([
        getDevices({ page_size: 200 }),
        getBackups({ page_size: 200 }),
        getSchedule(),
      ]);
      setDevices(devRes.data.items || []);
      setData(backupRes.data.items || []);
      setSchedEnabled(schedRes.data.enabled);
      setSchedInterval(schedRes.data.interval || 3600);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  const handleTrigger = async () => {
    if (!selectedDevice) return;
    setBackingUp(true);
    try {
      const res = await triggerBackup(selectedDevice);
      if (res.data.success) {
        message.success('备份成功');
      } else {
        message.error('备份失败');
      }
      loadAll();
    } catch {
      message.error('备份操作失败');
    } finally {
      setBackingUp(false);
    }
  };

  const handleTriggerAll = async () => {
    setBackingUpAll(true);
    try {
      const res = await triggerBackupAll();
      message.success(`全部备份完成：成功 ${res.data.success} 台，失败 ${res.data.failed} 台`);
      loadAll();
    } catch {
      message.error('批量备份失败');
    } finally {
      setBackingUpAll(false);
    }
  };

  const handleScheduleToggle = async (checked: boolean) => {
    setScheduleLoading(true);
    try {
      const res = await updateSchedule({ enabled: checked, interval: schedInterval });
      setSchedEnabled(res.data.enabled);
      message.success(`定时备份已${checked ? '开启' : '关闭'}`);
    } catch {
      message.error('操作失败');
    } finally {
      setScheduleLoading(false);
    }
  };

  const handleIntervalChange = async (value: number | null) => {
    if (!value || value < 60) return;
    setSchedInterval(value);
    if (schedEnabled) {
      setScheduleLoading(true);
      try {
        await updateSchedule({ enabled: true, interval: value });
        message.success(`备份间隔已设为 ${value} 秒`);
      } catch {
        message.error('更新间隔失败');
      } finally {
        setScheduleLoading(false);
      }
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteBackup(id);
      message.success('备份记录已删除');
      loadAll();
    } catch {
      message.error('删除失败');
    }
  };

  const deviceMap = Object.fromEntries(devices.map((d) => [d.id, d]));

  const columns = [
    {
      title: '设备',
      render: (_: any, r: BackupItem) => deviceMap[r.device_id]?.name || `ID: ${r.device_id}`,
    },
    { title: '文件名', dataIndex: 'filename', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      render: (v: string) => <Tag color={v === '成功' ? 'green' : 'red'}>{v}</Tag>,
    },
    { title: '时间', dataIndex: 'created_at', width: 180 },
    {
      title: '操作',
      width: 150,
      render: (_: any, r: BackupItem) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => window.open(getDownloadUrl(r.id), '_blank')}>
            查看
          </Button>
          <Popconfirm title="确定删除该备份记录？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      {/* 手动备份区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <span style={{ fontWeight: 500 }}>手动备份：</span>
          <Select
            style={{ width: 240 }}
            placeholder="请选择设备触发备份"
            allowClear
            onChange={(val) => setSelectedDevice(val || null)}
          >
            {devices.map((d) => (
              <Select.Option key={d.id} value={d.id}>{d.name} ({d.ip})</Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<CloudDownloadOutlined />}
            disabled={!selectedDevice}
            loading={backingUp}
            onClick={handleTrigger}
          >
            触发备份
          </Button>
          <Button
            icon={<PlayCircleOutlined />}
            loading={backingUpAll}
            onClick={handleTriggerAll}
          >
            全部备份
          </Button>
        </Space>
      </Card>

      {/* 定时备份区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <span style={{ fontWeight: 500 }}>定时备份：</span>
          <Switch
            checked={schedEnabled}
            loading={scheduleLoading}
            onChange={handleScheduleToggle}
            checkedChildren="已开启"
            unCheckedChildren="已关闭"
          />
          <span style={{ color: '#666' }}>间隔：</span>
          <InputNumber
            min={60}
            max={86400}
            step={300}
            value={schedInterval}
            onChange={handleIntervalChange}
            addonAfter="秒"
            disabled={scheduleLoading}
            style={{ width: 160 }}
          />
          <span style={{ color: '#999', fontSize: 12 }}>
            {schedEnabled
              ? `约每 ${Math.round(schedInterval / 60)} 分钟自动备份全部设备`
              : '定时备份已关闭'}
          </span>
        </Space>
      </Card>

      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} pagination={{ pageSize: 10 }} />
    </>
  );
}
