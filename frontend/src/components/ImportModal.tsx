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

export default function ImportModal({ open, onCancel, onSuccess }: Props) {
  const [fileList, setFileList] = useState<any[]>([]);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleImport = async () => {
    if (fileList.length === 0) return;

    const file = fileList[0];
    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string;
        const devices = JSON.parse(content);

        if (!Array.isArray(devices) || devices.length === 0) {
          setResult({ type: 'error', message: '文件格式错误：应为 JSON 数组' });
          return;
        }

        setImporting(true);
        const res = await importDevices(devices);
        setResult({ type: 'success', message: `导入完成：成功 ${res.data.imported} 台，跳过 ${res.data.skipped} 台` });
        if (res.data.imported > 0) {
          onSuccess();
        }
      } catch (err: any) {
        setResult({ type: 'error', message: err?.message || '导入失败' });
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
      destroyOnHidden
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
            accept=".json"
            fileList={fileList}
            onRemove={() => setFileList([])}
            beforeUpload={(file) => {
              setFileList([file]);
              return false;
            }}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽 JSON 文件到此区域</p>
          </Dragger>
          <Text type="secondary" style={{ fontSize: 12 }}>
            JSON 格式：{`[{ "name": "...", "ip": "...", "username": "...", "password": "...", "device_type": "H3C" }]`}
          </Text>
        </Space>
      )}
    </Modal>
  );
}
