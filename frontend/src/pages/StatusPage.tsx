import { useEffect, useState } from 'react';
import { Card, Row, Col, Tag, Spin, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { getHealth } from '../api/health';

export default function StatusPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getHealth();
      setHealth(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={load} loading={loading}>刷新状态</Button>
      </div>

      <Spin spinning={loading && !health}>
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Card title="服务状态">
              {health?.status === 'running' ? (
                <Tag color="green" style={{ fontSize: 14, padding: '4px 12px' }}>运行中</Tag>
              ) : (
                <Tag color="red" style={{ fontSize: 14, padding: '4px 12px' }}>已停止</Tag>
              )}
            </Card>
          </Col>
          <Col span={8}>
            <Card title="数据库连接">
              {health?.database === 'connected' ? (
                <Tag color="green" style={{ fontSize: 14, padding: '4px 12px' }}>已连接</Tag>
              ) : (
                <Tag color="red" style={{ fontSize: 14, padding: '4px 12px' }}>断开</Tag>
              )}
            </Card>
          </Col>
          <Col span={8}>
            <Card title="定时任务">
              {health?.scheduler === 'running' ? (
                <Tag color="green" style={{ fontSize: 14, padding: '4px 12px' }}>运行中</Tag>
              ) : (
                <Tag color="orange" style={{ fontSize: 14, padding: '4px 12px' }}>已停止</Tag>
              )}
            </Card>
          </Col>
        </Row>
      </Spin>
    </>
  );
}
