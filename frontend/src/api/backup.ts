import request from './request';
export const getBackups = (params?: { page?: number; page_size?: number }) =>
  request.get('/backup', { params });
export const triggerBackup = (id: number) => request.post(`/backup/trigger/${id}`);
export const triggerBackupAll = () => request.post('/backup/trigger-all');
export const getSchedule = () => request.get('/backup/schedule');
export const updateSchedule = (data: { enabled: boolean; interval: number }) =>
  request.put('/backup/schedule', data);
export const deleteBackup = (id: number) => request.delete(`/backup/${id}`);
export const getDownloadUrl = (id: number) => `/api/v1/backup/${id}/download`;
