import { useEffect, useState } from 'react';
import { Table, Tag, Drawer, Descriptions, Button, Space, Select } from 'antd';
import { getDevices } from '../api/device';
import { getInspectionHistory, getInspectionReport } from '../api/inspection';

interface InspectionRecordItem {
  id: number;
  device_id: number;
  overall_status: string;
  summary: string;
  created_at: string;
}

const statusColor: Record<string, string> = {
  healthy: 'green',
  warning: 'orange',
  critical: 'red',
  pending: 'default',
};

const statusText: Record<string, string> = {
  healthy: '正常',
  warning: '告警',
  critical: '严重',
  pending: '进行中',
};

export default function InspectionPage() {
  const [records, setRecords] = useState<InspectionRecordItem[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [report, setReport] = useState<any>(null);

  const loadDevices = async () => {
    const res = await getDevices();
    setDevices(res.data.items || []);
  };

  const loadRecords = async (deviceId: number) => {
    const res = await getInspectionHistory(deviceId);
    setRecords(res.data.items || []);
  };

  useEffect(() => { loadDevices(); }, []);

  useEffect(() => {
    if (selectedDevice) loadRecords(selectedDevice);
    else setRecords([]);
  }, [selectedDevice]);

  const showReport = async (recordId: number) => {
    const res = await getInspectionReport(recordId);
    setReport(res.data);
    setDrawerOpen(true);
  };

  const deviceMap = Object.fromEntries(devices.map((d) => [d.id, d]));

  const columns = [
    {
      title: '设备',
      render: (_: any, r: InspectionRecordItem) => deviceMap[r.device_id]?.name || `ID: ${r.device_id}`,
    },
    { title: '巡检时间', dataIndex: 'created_at' },
    {
      title: '状态',
      dataIndex: 'overall_status',
      render: (v: string) => <Tag color={statusColor[v]}>{statusText[v]}</Tag>,
    },
    { title: '摘要', dataIndex: 'summary' },
    {
      title: '操作',
      render: (_: any, r: InspectionRecordItem) => (
        <Button size="small" onClick={() => showReport(r.id)}>查看详情</Button>
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
            placeholder="请选择设备查看巡检记录"
            allowClear
            onChange={(val) => setSelectedDevice(val || null)}
          >
            {devices.map((d) => (
              <Select.Option key={d.id} value={d.id}>{d.name} ({d.ip})</Select.Option>
            ))}
          </Select>
        </Space>
      </div>
      <Table rowKey="id" columns={columns} dataSource={records} pagination={{ pageSize: 10 }} />

      <Drawer
        title="巡检报告"
        width={600}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {report?.result && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="总体状态">
              <Tag color={statusColor[report.result.overall_status]}>
                {statusText[report.result.overall_status]}
              </Tag>
            </Descriptions.Item>
            {report.result.checks?.map((c: any, i: number) => (
              <Descriptions.Item label={c.name} key={i}>
                <Tag color={c.status === 'pass' ? 'green' : c.status === 'warning' ? 'orange' : 'red'}>
                  {c.status === 'pass' ? '通过' : c.status === 'warning' ? '警告' : '失败'}
                </Tag>
                {c.detail}
                {c.value !== undefined && <span style={{ marginLeft: 8 }}>({c.value})</span>}
              </Descriptions.Item>
            ))}
          </Descriptions>
        )}
      </Drawer>
    </>
  );
}
