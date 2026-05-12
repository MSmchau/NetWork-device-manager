import { useEffect, useState } from 'react';
import { Table, Tag, Drawer, Descriptions, Button, Space, Select, message, Empty, Spin } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { getDevices } from '../api/device';
import { getInspectionHistory, getInspectionReport, triggerInspect } from '../api/inspection';

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
  const [tableLoading, setTableLoading] = useState(false);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState(false);

  const loadDevices = async () => {
    const res = await getDevices({ page_size: 200 });
    setDevices(res.data.items || []);
  };

  const loadRecords = async (deviceId: number) => {
    setTableLoading(true);
    try {
      const res = await getInspectionHistory(deviceId);
      setRecords(res.data.items || []);
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => { loadDevices(); }, []);

  useEffect(() => {
    if (selectedDevice) loadRecords(selectedDevice);
    else setRecords([]);
  }, [selectedDevice]);

  const handleTrigger = async () => {
    if (!selectedDevice) return;
    setTriggerLoading(true);
    try {
      await triggerInspect(selectedDevice);
      message.success('巡检已触发');
      loadRecords(selectedDevice);
    } catch {
      message.error('巡检触发失败');
    } finally {
      setTriggerLoading(false);
    }
  };

  const showReport = async (recordId: number) => {
    setDrawerOpen(true);
    setReport(null);
    setReportLoading(true);
    try {
      const res = await getInspectionReport(recordId);
      setReport(res.data);
    } catch {
      message.error('获取报告失败');
    } finally {
      setReportLoading(false);
    }
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
          <Button
            type="primary"
            icon={<SearchOutlined />}
            disabled={!selectedDevice}
            loading={triggerLoading}
            onClick={handleTrigger}
          >
            触发巡检
          </Button>
        </Space>
      </div>

      {!selectedDevice ? (
        <Empty description="请先选择一台设备以查看巡检记录" style={{ marginTop: 80 }} />
      ) : (
        <Table
          rowKey="id"
          columns={columns}
          dataSource={records}
          loading={tableLoading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无巡检记录' }}
        />
      )}

      <Drawer
        title="巡检报告"
        width={600}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {reportLoading ? (
          <div style={{ textAlign: 'center', paddingTop: 80 }}><Spin size="large" /></div>
        ) : report?.result ? (
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
        ) : null}
      </Drawer>
    </>
  );
}
