import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import DevicePage from './pages/DevicePage';
import AlarmPage from './pages/AlarmPage';
import BackupPage from './pages/BackupPage';
import InspectionPage from './pages/InspectionPage';
import StatusPage from './pages/StatusPage';
import Layout from './layouts/Layout';

function NotFound() {
  const navigate = useNavigate();
  return (
    <Result
      status="404"
      title="404"
      subTitle="页面不存在"
      extra={<Button type="primary" onClick={() => navigate('/')}>返回首页</Button>}
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DevicePage />} />
          <Route path="/alarm" element={<AlarmPage />} />
          <Route path="/backup" element={<BackupPage />} />
          <Route path="/inspect" element={<InspectionPage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
