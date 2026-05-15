import request from './request';
export const getAlarms = (params?: { page?: number; page_size?: number }) =>
  request.get('/alarm', { params });
export const handleAlarm = (id: number) => request.put(`/alarm/${id}/handle`);
export const deleteAlarm = (id: number) => request.delete(`/alarm/${id}`);
