import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DevicePage from './pages/DevicePage';
import InspectionPage from './pages/InspectionPage';
import Layout from './layouts/Layout';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DevicePage />} />
          <Route path="/inspect" element={<InspectionPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
