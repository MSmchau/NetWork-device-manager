import request from './request';
export const getBackups = (params?: { page?: number; page_size?: number }) =>
  request.get('/backup', { params });
export const triggerBackup = (id: number) => request.post(`/backup/trigger/${id}`);
export const deleteBackup = (id: number) => request.delete(`/backup/${id}`);
