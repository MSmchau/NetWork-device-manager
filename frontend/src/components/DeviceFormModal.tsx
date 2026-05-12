import { useEffect } from 'react';
import { Modal, Form, Input, InputNumber, Select } from 'antd';

interface DeviceFormData {
  name: string;
  ip: string;
  port: number;
  username: string;
  password: string;
  device_type: string;
}

interface Props {
  open: boolean;
  editing: DeviceFormData | null;
  onCancel: () => void;
  onOk: (values: DeviceFormData) => void;
}

export default function DeviceFormModal({ open, editing, onCancel, onOk }: Props) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      if (editing) {
        form.setFieldsValue(editing);
      } else {
        form.resetFields();
      }
    }
  }, [open, editing, form]);

  return (
    <Modal
      title={editing ? '编辑设备' : '添加设备'}
      open={open}
      onOk={() => form.submit()}
      onCancel={onCancel}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" onFinish={onOk} autoComplete="off">
        <Form.Item name="name" label="设备名称" rules={[{ required: true, message: '请输入设备名称' }]}>
          <Input placeholder="例如：核心交换机-01" />
        </Form.Item>
        <Form.Item name="ip" label="IP 地址" rules={[
          { required: true, message: '请输入 IP 地址' },
          { pattern: /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/, message: 'IP 格式不正确' },
        ]}>
          <Input placeholder="192.168.1.1" />
        </Form.Item>
        <Form.Item name="port" label="SSH 端口" initialValue={22}>
          <InputNumber min={1} max={65535} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="username" label="SSH 用户名" rules={[{ required: true, message: '请输入 SSH 用户名' }]}>
          <Input placeholder="admin" />
        </Form.Item>
        <Form.Item name="password" label="SSH 密码" rules={[{ required: !editing, message: '请输入 SSH 密码' }]}>
          <Input.Password placeholder={editing ? '留空则不修改' : ''} />
        </Form.Item>
        <Form.Item name="device_type" label="设备类型" initialValue="H3C">
          <Select>
            <Select.Option value="H3C">华三（H3C）</Select.Option>
            <Select.Option value="华为">华为（Huawei）</Select.Option>
            <Select.Option value="思科">思科（Cisco）</Select.Option>
            <Select.Option value="锐捷">锐捷（Ruijie）</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  );
}
