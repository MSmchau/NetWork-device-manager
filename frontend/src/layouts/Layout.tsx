import { ReactNode } from 'react';
import { Layout as AntLayout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DesktopOutlined,
  BellOutlined,
  FileProtectOutlined,
  SearchOutlined,
  DashboardOutlined,
} from '@ant-design/icons';

const menuItems = [
  { key: '/', icon: <DesktopOutlined />, label: '设备管理' },
  { key: '/alarm', icon: <BellOutlined />, label: '告警信息' },
  { key: '/backup', icon: <FileProtectOutlined />, label: '备份记录' },
  { key: '/inspect', icon: <SearchOutlined />, label: '设备巡检' },
  { key: '/status', icon: <DashboardOutlined />, label: '系统状态' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <AntLayout.Sider collapsible>
        <div style={{ color: '#fff', textAlign: 'center', padding: 16, fontSize: 18 }}>
          网络设备管理平台
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </AntLayout.Sider>
      <AntLayout.Content style={{ padding: 24 }}>
        {children}
      </AntLayout.Content>
    </AntLayout>
  );
}
