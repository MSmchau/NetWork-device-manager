import { useEffect, useState, useCallback } from 'react';
import { Table, Button, Tag, Space, Popconfirm, message } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { getDevices, getDeviceStats, createDevice, updateDevice, deleteDevice, refreshDevice } from '../api/device';
import { triggerInspect } from '../api/inspection';
import { triggerBackup } from '../api/backup';
import DeviceFormModal from '../components/DeviceFormModal';
import DeviceStats from '../components/DeviceStats';

interface Device {
  id: number;
  name: string;
  ip: string;
  port: number;
  is_online: boolean;
  cpu_usage: number;
  mem_usage: number;
  device_type: string;
}

export default function DevicePage() {
  const [data, setData] = useState<Device[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [devRes, statsRes] = await Promise.all([
        getDevices({ page_size: 200 }),
        getDeviceStats(),
      ]);
      setData(devRes.data.items || []);
      setStats(statsRes.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = () => {
    setEditing(null);
    setModalOpen(true);
  };

  const handleEdit = (record: Device) => {
    setEditing(record);
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDevice(id);
      message.success('设备已删除');
      load();
    } catch {
      message.error('删除失败');
    }
  };

  const handleInspect = async (id: number) => {
    try {
      await triggerInspect(id);
      message.success('巡检已触发，请查看巡检记录');
    } catch {
      message.error('巡检触发失败');
    }
  };

  const handleBackup = async (id: number) => {
    try {
      const res = await triggerBackup(id);
      if (res.data.success) {
        message.success('备份成功');
      } else {
        message.error('备份失败');
      }
    } catch {
      message.error('备份操作失败');
    }
  };

  const handleRefresh = async (id: number) => {
    try {
      await refreshDevice(id);
      message.success('设备状态已刷新');
      load();
    } catch {
      message.error('刷新失败');
    }
  };

  const handleModalOk = async (values: any) => {
    try {
      if (editing) {
        await updateDevice(editing.id, values);
        message.success('设备已更新');
      } else {
        await createDevice(values);
        message.success('设备已添加');
      }
      setModalOpen(false);
      load();
    } catch {
      message.error(editing ? '设备更新失败' : '设备添加失败');
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name' },
    { title: 'IP', dataIndex: 'ip' },
    { title: '端口', dataIndex: 'port', render: (v: number) => v || 22 },
    {
      title: '状态',
      render: (_: any, r: Device) => (
        <Tag color={r.is_online ? 'green' : 'red'}>
          {r.is_online ? '在线' : '离线'}
        </Tag>
      ),
    },
    { title: 'CPU', dataIndex: 'cpu_usage', render: (v: number) => `${v ?? 0}%` },
    { title: '内存', dataIndex: 'mem_usage', render: (v: number) => `${v ?? 0}%` },
    {
      title: '操作',
      width: 320,
      render: (_: any, r: Device) => (
        <Space>
          <Button size="small" onClick={() => handleRefresh(r.id)}>刷新</Button>
          <Button size="small" onClick={() => handleEdit(r)}>编辑</Button>
          <Button size="small" onClick={() => handleInspect(r.id)}>巡检</Button>
          <Button size="small" type="primary" onClick={() => handleBackup(r.id)}>备份</Button>
          <Popconfirm title="确定删除该设备？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <DeviceStats data={stats} />
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加设备
        </Button>
        <Button icon={<ReloadOutlined />} onClick={load} style={{ marginLeft: 8 }}>
          刷新列表
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} pagination={{ pageSize: 10 }} />
      <DeviceFormModal open={modalOpen} editing={editing} onCancel={() => setModalOpen(false)} onOk={handleModalOk} />
    </>
  );
}
