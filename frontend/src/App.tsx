import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DevicePage from './pages/DevicePage';
import AlarmPage from './pages/AlarmPage';
import BackupPage from './pages/BackupPage';
import InspectionPage from './pages/InspectionPage';
import Layout from './layouts/Layout';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DevicePage />} />
          <Route path="/alarm" element={<AlarmPage />} />
          <Route path="/backup" element={<BackupPage />} />
          <Route path="/inspect" element={<InspectionPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
