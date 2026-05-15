import { useState } from 'react';
import { Modal, Upload, Button, Alert, Space, Typography } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import { importDevices } from '../api/device';

const { Dragger } = Upload;
const { Text } = Typography;

interface Props {
  open: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

/** 列名映射：中文/英文 → 标准字段名 */
const COLUMN_MAP: Record<string, string> = {
  '名称': 'name', 'name': 'name',
  'ip': 'ip', 'IP': 'ip',
  '端口': 'port', 'port': 'port',
  '用户名': 'username', 'username': 'username',
  '密码': 'password', 'password': 'password',
  '设备类型': 'device_type', 'device_type': 'device_type',
  '连接协议': 'protocol', 'protocol': 'protocol',
};

function parseCSV(text: string): Record<string, any>[] {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length < 2) {
    throw new Error('CSV 文件至少需要标题行和一行数据');
  }

  // 解析标题行（支持引号包裹的字段）
  const parseLine = (line: string): string[] => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    for (const ch of line) {
      if (ch === '"') { inQuotes = !inQuotes; continue; }
      if (ch === ',' && !inQuotes) { result.push(current.trim()); current = ''; continue; }
      current += ch;
    }
    result.push(current.trim());
    return result;
  };

  const headers = parseLine(lines[0]);
  const fields = headers.map(h => COLUMN_MAP[h.toLowerCase()] || COLUMN_MAP[h] || h);

  const devices: Record<string, any>[] = [];
  for (let i = 1; i < lines.length; i++) {
    const values = parseLine(lines[i]);
    const device: Record<string, any> = {};

    fields.forEach((field, idx) => {
      if (field && idx < values.length) {
        device[field] = values[idx];
      }
    });

    // 校验必填字段
    if (!device.name) throw new Error(`第 ${i + 1} 行缺少名称(name)`);
    if (!device.ip) throw new Error(`第 ${i + 1} 行缺少 IP 地址`);
    if (!device.username) throw new Error(`第 ${i + 1} 行缺少用户名(username)`);
    if (!device.password) throw new Error(`第 ${i + 1} 行缺少密码(password)`);

    // 设置默认值
    if (device.port) device.port = parseInt(device.port, 10) || 22;
    else device.port = device.protocol === 'telnet' ? 23 : 22;
    if (!device.device_type) device.device_type = 'H3C';
    if (!device.protocol) device.protocol = 'ssh';

    devices.push(device);
  }

  return devices;
}

export default function ImportModal({ open, onCancel, onSuccess }: Props) {
  const [fileList, setFileList] = useState<any[]>([]);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleImport = async () => {
    if (fileList.length === 0) return;

    const file = fileList[0];
    const isCSV = file.name.endsWith('.csv');
    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string;
        let devices: Record<string, any>[];

        if (isCSV) {
          devices = parseCSV(content);
        } else {
          devices = JSON.parse(content);
          if (!Array.isArray(devices) || devices.length === 0) {
            setResult({ type: 'error', message: '文件格式错误：应为 JSON 数组' });
            return;
          }
          // JSON 导入兼容：补充默认字段
          for (const d of devices) {
            if (!d.protocol) d.protocol = 'ssh';
            if (!d.port) d.port = d.protocol === 'telnet' ? 23 : 22;
            if (!d.device_type) d.device_type = 'H3C';
          }
        }

        setImporting(true);
        const res = await importDevices(devices);
        setResult({ type: 'success', message: `导入完成：成功 ${res.data.imported} 台，跳过 ${res.data.skipped} 台` });
        if (res.data.imported > 0) {
          onSuccess();
        }
      } catch (err: any) {
        setResult({ type: 'error', message: err?.response?.data?.message || err?.message || '导入失败' });
      } finally {
        setImporting(false);
      }
    };

    reader.readAsText(file);
  };

  const handleClose = () => {
    setFileList([]);
    setResult(null);
    onCancel();
  };

  return (
    <Modal
      title="批量导入设备"
      open={open}
      onCancel={handleClose}
      footer={
        result ? (
          <Button onClick={handleClose}>关闭</Button>
        ) : (
          <Space>
            <Button onClick={handleClose}>取消</Button>
            <Button type="primary" loading={importing} disabled={fileList.length === 0} onClick={handleImport}>
              开始导入
            </Button>
          </Space>
        )
      }
      destroyOnClose
    >
      {result ? (
        <Alert
          type={result.type}
          message={result.message}
          showIcon
        />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Dragger
            accept=".json,.csv"
            fileList={fileList}
            onRemove={() => setFileList([])}
            beforeUpload={(file) => {
              setFileList([file]);
              return false;
            }}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽 JSON / CSV 文件到此区域</p>
          </Dragger>
          <Text type="secondary" style={{ fontSize: 12 }}>
            JSON 格式：{`[{ "name": "...", "ip": "...", "username": "...", "password": "...", "device_type": "H3C", "protocol": "ssh" }]`}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            CSV 格式：name, ip, port, username, password, device_type, protocol（支持中英文列名，protocol 默认 ssh）
          </Text>
        </Space>
      )}
    </Modal>
  );
}
