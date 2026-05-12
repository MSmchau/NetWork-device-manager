import request from './request';
export const triggerInspect = (deviceId: number) => request.post(`/inspect/${deviceId}`);
export const getInspectionHistory = (deviceId: number) => request.get(`/inspect/${deviceId}`);
export const getInspectionReport = (recordId: number) => request.get(`/inspect/report/${recordId}`);
