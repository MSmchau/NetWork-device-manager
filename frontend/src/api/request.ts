import axios from 'axios';
import { message } from 'antd';

const request = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || '/api/v1',
  timeout: 30000,
});

// 响应拦截器：统一解包 + 全局错误处理
request.interceptors.response.use(
  (response: any) => {
    const body = response.data;
    // 后端统一响应格式：{ code, message, data }
    if (body.code !== undefined && body.code !== 0) {
      message.error(body.message || '请求失败');
      return Promise.reject(new Error(body.message));
    }
    // 成功时直接返回 data 字段，调用方无需再解套
    response.data = body.data;
    return response;
  },
  (error: any) => {
    if (error.response) {
      const { status, data } = error.response;
      if (status >= 500) {
        message.error('服务器内部错误');
      } else if (data?.message) {
        message.error(data.message);
      } else if (status === 422) {
        message.error('请求参数校验失败');
      } else {
        message.error(`请求失败 (${status})`);
      }
    } else {
      message.error('网络连接失败');
    }
    return Promise.reject(error);
  }
);

export default request;
