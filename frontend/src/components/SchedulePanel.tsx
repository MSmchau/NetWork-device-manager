import { Switch, InputNumber, Card, Space } from 'antd';

interface SchedulePanelProps {
  title: string;
  actionLabel: string;
  enabled: boolean;
  interval: number;
  loading: boolean;
  onToggle: (checked: boolean) => void;
  onIntervalChange: (value: number | null) => void;
}

export default function SchedulePanel({
  title, actionLabel, enabled, interval,
  loading, onToggle, onIntervalChange,
}: SchedulePanelProps) {
  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Space wrap>
        <span style={{ fontWeight: 500 }}>{title}</span>
        <Switch
          checked={enabled}
          loading={loading}
          onChange={onToggle}
          checkedChildren="已开启"
          unCheckedChildren="已关闭"
        />
        <span style={{ color: '#666' }}>间隔：</span>
        <InputNumber
          min={60}
          max={86400}
          step={300}
          value={interval}
          onChange={onIntervalChange}
          addonAfter="秒"
          disabled={loading}
          style={{ width: 160 }}
        />
        <span style={{ color: '#999', fontSize: 12 }}>
          {enabled
            ? `约每 ${Math.round(interval / 60)} 分钟自动${actionLabel}全部设备`
            : `定时${actionLabel}已关闭`}
        </span>
      </Space>
    </Card>
  );
}
