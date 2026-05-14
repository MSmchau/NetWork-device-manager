import request from './request';
export const getDevices = (params?: { page?: number; page_size?: number }) =>
  request.get('/device', { params });
export const getDevice = (id: number) => request.get(`/device/${id}`);
export const createDevice = (data: any) => request.post('/device', data);
export const updateDevice = (id: number, data: any) => request.put(`/device/${id}`, data);
export const deleteDevice = (id: number) => request.delete(`/device/${id}`);
export const refreshDevice = (id: number) => request.post(`/device/refresh/${id}`);
export const refreshAllDevices = () => request.post('/device/refresh-all');
export const getDeviceStats = () => request.get('/device/stats');
export const importDevices = (data: any[]) => request.post('/device/import', data);
// 导出使用直接 URL 下载（CSV 为 StreamingResponse，JSON 直接下载文件）
export const getExportUrl = (format: string) =>
  `${request.defaults.baseURL}/device/export?format=${format}`;
