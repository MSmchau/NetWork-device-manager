import request from './request';
export const getDevices = (params?: { page?: number; page_size?: number }) =>
  request.get('/device', { params });
export const getDevice = (id: number) => request.get(`/device/${id}`);
export const createDevice = (data: any) => request.post('/device', data);
export const updateDevice = (id: number, data: any) => request.put(`/device/${id}`, data);
export const deleteDevice = (id: number) => request.delete(`/device/${id}`);
export const refreshDevice = (id: number) => request.post(`/device/refresh/${id}`);
