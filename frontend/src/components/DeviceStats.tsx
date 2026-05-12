import { useEffect, useState } from 'react';
import { Card, Radio, Row, Col, Statistic, Spin } from 'antd';
import ReactECharts from 'echarts-for-react';

interface DeviceStatsData {
  total: number;
  online: number;
  offline: number;
  by_type: { name: string; count: number }[];
}

type ChartMode = 'pie' | 'bar';

const COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4'];

export default function DeviceStats({ data }: { data: DeviceStatsData | null }) {
  const [mode, setMode] = useState<ChartMode>('pie');

  if (!data) return null;

  const total = data.total || 0;

  const pieOption = {
    tooltip: { trigger: 'item' as const, formatter: '{b}: {c} 台 ({d}%)' },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{c} 台' },
        emphasis: { label: { show: true, fontSize: 14 }, itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' } },
        data: data.by_type.length > 0
          ? data.by_type.map((t, i) => ({ value: t.count, name: t.name, itemStyle: { color: COLORS[i % COLORS.length] } }))
          : [{ value: 1, name: '暂无设备', itemStyle: { color: '#ddd' } }],
      },
    ],
  };

  const barOption = {
    tooltip: { trigger: 'axis' as const },
    xAxis: { type: 'category' as const, data: ['在线', '离线'] },
    yAxis: { type: 'value' as const, minInterval: 1 },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    series: [
      {
        type: 'bar',
        barWidth: '50%',
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: [
          { value: data.online, itemStyle: { color: '#52c41a' } },
          { value: data.offline, itemStyle: { color: '#ff4d4f' } },
        ],
      },
    ],
  };

  const chartOption = mode === 'pie' ? pieOption : barOption;

  return (
    <Card
      style={{ marginBottom: 16 }}
      styles={{ body: { paddingBottom: 8 } }}
    >
      <Row gutter={[16, 16]} align="middle">
        <Col span={6}>
          <Row gutter={[8, 8]}>
            <Col span={24}>
              <Statistic title="设备总数" value={total} suffix="台" />
            </Col>
            <Col span={12}>
              <Statistic
                title="在线"
                value={data.online}
                valueStyle={{ color: '#52c41a', fontSize: 22 }}
                suffix="台"
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="离线"
                value={data.offline}
                valueStyle={{ color: '#ff4d4f', fontSize: 22 }}
                suffix="台"
              />
            </Col>
          </Row>
        </Col>
        <Col span={18}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontWeight: 500, color: '#333' }}>
              {mode === 'pie' ? '设备类型分布' : '设备在线状态'}
            </div>
            <Radio.Group
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              size="small"
              optionType="button"
              buttonStyle="solid"
            >
              <Radio.Button value="pie">扇形图</Radio.Button>
              <Radio.Button value="bar">柱状图</Radio.Button>
            </Radio.Group>
          </div>
          <ReactECharts option={chartOption} style={{ height: 210 }} notMerge />
        </Col>
      </Row>
    </Card>
  );
}
