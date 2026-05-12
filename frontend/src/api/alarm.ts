import request from './request';
export const getAlarms = (params?: { page?: number; page_size?: number }) =>
  request.get('/alarm', { params });
