import { useEffect, useState } from 'react';
import { Table, Tag, Space, Select, Button, message } from 'antd';
import { getAlarms, handleAlarm } from '../api/alarm';
import { getDevices } from '../api/device';

interface AlarmItem {
  id: number;
  device_id: number;
  alarm_type: string;
  level: string;
  message: string;
  is_handled: boolean;
  created_at: string;
}

const levelColor: Record<string, string> = {
  critical: 'red',
  warning: 'orange',
  info: 'blue',
};

const levelText: Record<string, string> = {
  critical: '严重',
  warning: '警告',
  info: '信息',
};

export default function AlarmPage() {
  const [data, setData] = useState<AlarmItem[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [levelFilter, setLevelFilter] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [devRes, alarmRes] = await Promise.all([
        getDevices({ page_size: 200 }),
        getAlarms({ page_size: 200 }),
      ]);
      setDevices(devRes.data.items || []);
      setData(alarmRes.data.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleMark = async (id: number) => {
    try {
      await handleAlarm(id);
      message.success('告警已处理');
      load();
    } catch {
      message.error('操作失败');
    }
  };

  const deviceMap = Object.fromEntries(devices.map((d) => [d.id, d]));

  const filtered = levelFilter
    ? data.filter((r) => r.level === levelFilter)
    : data;

  const columns = [
    {
      title: '设备',
      render: (_: any, r: AlarmItem) => deviceMap[r.device_id]?.name || `ID: ${r.device_id}`,
    },
    { title: '类型', dataIndex: 'alarm_type' },
    {
      title: '级别',
      dataIndex: 'level',
      render: (v: string) => <Tag color={levelColor[v]}>{levelText[v] || v}</Tag>,
    },
    { title: '告警内容', dataIndex: 'message', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'is_handled',
      render: (v: boolean) => <Tag color={v ? 'default' : 'volcano'}>{v ? '已处理' : '未处理'}</Tag>,
    },
    { title: '时间', dataIndex: 'created_at', width: 180 },
    {
      title: '操作',
      width: 100,
      render: (_: any, r: AlarmItem) => (
        !r.is_handled ? (
          <Button size="small" type="primary" onClick={() => handleMark(r.id)}>处理</Button>
        ) : null
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>级别筛选：</span>
          <Select
            style={{ width: 140 }}
            placeholder="全部级别"
            allowClear
            onChange={(val) => setLevelFilter(val || null)}
          >
            <Select.Option value="critical">严重</Select.Option>
            <Select.Option value="warning">警告</Select.Option>
            <Select.Option value="info">信息</Select.Option>
          </Select>
        </Space>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={filtered}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </>
  );
}
