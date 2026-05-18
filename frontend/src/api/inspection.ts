import request from './request';
export const triggerInspect = (deviceId: number) => request.post(`/inspect/trigger/${deviceId}`);
export const triggerInspectAll = () => request.post('/inspect/trigger-all');
export const getSchedule = () => request.get('/inspect/schedule');
export const updateSchedule = (data: { enabled: boolean; interval: number }) =>
  request.put('/inspect/schedule', data);
export const getInspectionHistory = (deviceId?: number) =>
  deviceId ? request.get(`/inspect/${deviceId}`) : request.get('/inspect');
export const getInspectionReport = (recordId: number) => request.get(`/inspect/report/${recordId}`);
export const deleteInspection = (id: number) => request.delete(`/inspect/${id}`);
export const exportInspectionReport = async (): Promise<Blob> => {
  const url = `${request.defaults.baseURL}/inspect/export`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('导出失败');
  return response.blob();
};
