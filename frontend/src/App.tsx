import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Result, Button, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import Layout from './layouts/Layout';

const DevicePage = lazy(() => import('./pages/DevicePage'));
const AlarmPage = lazy(() => import('./pages/AlarmPage'));
const BackupPage = lazy(() => import('./pages/BackupPage'));
const InspectionPage = lazy(() => import('./pages/InspectionPage'));
const StatusPage = lazy(() => import('./pages/StatusPage'));

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
        <Suspense fallback={<Spin style={{ display: 'block', marginTop: 200 }} />}>
          <Routes>
            <Route path="/" element={<DevicePage />} />
            <Route path="/alarm" element={<AlarmPage />} />
            <Route path="/backup" element={<BackupPage />} />
            <Route path="/inspect" element={<InspectionPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}
