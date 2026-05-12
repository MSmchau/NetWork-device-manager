import { useEffect, useState } from 'react';
import { Table, Tag, Button, Space, Select, Popconfirm, message } from 'antd';
import { CloudDownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { getBackups, triggerBackup, deleteBackup } from '../api/backup';
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

  const load = async () => {
    setLoading(true);
    try {
      const [devRes, backupRes] = await Promise.all([
        getDevices({ page_size: 200 }),
        getBackups({ page_size: 200 }),
      ]);
      setDevices(devRes.data.items || []);
      setData(backupRes.data.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleTrigger = async () => {
    if (!selectedDevice) return;
    try {
      const res = await triggerBackup(selectedDevice);
      if (res.data.success) {
        message.success('备份成功');
      } else {
        message.error('备份失败');
      }
      load();
    } catch {
      message.error('备份操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteBackup(id);
      message.success('备份记录已删除');
      load();
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
      width: 80,
      render: (_: any, r: BackupItem) => (
        <Popconfirm title="确定删除该备份记录？" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>选择设备：</span>
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
          <Button type="primary" icon={<CloudDownloadOutlined />} disabled={!selectedDevice} onClick={handleTrigger}>
            触发备份
          </Button>
        </Space>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} pagination={{ pageSize: 10 }} />
    </>
  );
}
