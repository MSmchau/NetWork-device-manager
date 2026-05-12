import request from './request';
export const getBackups = () => request.get('/backup');
export const triggerBackup = (id: number) => request.post(`/backup/trigger/${id}`);
