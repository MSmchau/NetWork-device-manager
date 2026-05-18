import { useEffect, useState } from 'react';
import { Table, Tag, Drawer, Descriptions, Button, Space, Select, Popconfirm, message, Spin, Card } from 'antd';
import { SearchOutlined, DeleteOutlined, PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';
import { getDevices } from '../api/device';
import {
  getInspectionHistory, getInspectionReport, triggerInspect,
  triggerInspectAll, deleteInspection, getSchedule, updateSchedule,
  exportInspectionReport,
} from '../api/inspection';
import SchedulePanel from '../components/SchedulePanel';
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
  const [triggerAllLoading, setTriggerAllLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  // 定时巡检状态
  const [schedEnabled, setSchedEnabled] = useState(false);
  const [schedInterval, setSchedInterval] = useState(3600);
  const [scheduleLoading, setScheduleLoading] = useState(false);

  const loadAll = async () => {
    try {
      const [devRes, schedRes] = await Promise.all([
        getDevices({ page_size: 200 }),
        getSchedule(),
      ]);
      setDevices(devRes.data.items || []);
      setSchedEnabled(schedRes.data.enabled);
      setSchedInterval(schedRes.data.interval || 3600);
    } catch {
      // 静默
    }
  };

  const loadDevices = async () => {
    const res = await getDevices({ page_size: 200 });
    setDevices(res.data.items || []);
  };

  const loadRecords = async (deviceId?: number) => {
    setTableLoading(true);
    try {
      const res = await getInspectionHistory(deviceId);
      setRecords(res.data.items || []);
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  useEffect(() => {
    loadRecords(selectedDevice ?? undefined);
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

  const handleTriggerAll = async () => {
    setTriggerAllLoading(true);
    try {
      const res = await triggerInspectAll();
      message.success(`全部巡检完成：成功 ${res.data.success} 台，失败 ${res.data.failed} 台`);
      loadRecords(selectedDevice ?? undefined);
    } catch {
      message.error('批量巡检失败');
    } finally {
      setTriggerAllLoading(false);
    }
  };

  const handleScheduleToggle = async (checked: boolean) => {
    setScheduleLoading(true);
    try {
      await updateSchedule({ enabled: checked, interval: schedInterval });
      setSchedEnabled(checked);
      message.success(`定时巡检已${checked ? '开启' : '关闭'}`);
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
        message.success(`巡检间隔已设为 ${value} 秒`);
      } catch {
        message.error('更新间隔失败');
      } finally {
        setScheduleLoading(false);
      }
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

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const blob = await exportInspectionReport();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `巡检报告_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      message.error('导出报告失败');
    } finally {
      setExportLoading(false);
    }
  };

  const handleDeleteRecord = async (id: number) => {
    try {
      await deleteInspection(id);
      message.success('巡检记录已删除');
      if (selectedDevice) loadRecords(selectedDevice);
    } catch {
      message.error('删除失败');
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
      width: 160,
      render: (_: any, r: InspectionRecordItem) => (
        <Space>
          <Button size="small" onClick={() => showReport(r.id)}>查看详情</Button>
          <Popconfirm title="确定删除该巡检记录？" onConfirm={() => handleDeleteRecord(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      {/* 手动巡检区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <span style={{ fontWeight: 500 }}>手动巡检：</span>
          <Select
            style={{ width: 240 }}
            placeholder="全部设备（查看所有记录）"
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
          <Button
            icon={<PlayCircleOutlined />}
            loading={triggerAllLoading}
            onClick={handleTriggerAll}
          >
            全部巡检
          </Button>
          <Button
            icon={<DownloadOutlined />}
            loading={exportLoading}
            onClick={handleExport}
          >
            导出报告
          </Button>
        </Space>
      </Card>

      <SchedulePanel
        title="定时巡检："
        actionLabel="巡检"
        enabled={schedEnabled}
        interval={schedInterval}
        loading={scheduleLoading}
        onToggle={handleScheduleToggle}
        onIntervalChange={handleIntervalChange}
      />

      <Table
          rowKey="id"
          columns={columns}
          dataSource={records}
          loading={tableLoading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无巡检记录' }}
        />

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
