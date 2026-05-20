import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { showNotification } from '@mantine/notifications';

const API_BASE_URL = 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      // Don't show notification for login page redirects
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        showNotification({
          title: 'Session expired',
          message: 'Please log in again',
          color: 'red',
        });
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      showNotification({
        title: 'Access denied',
        message: 'You do not have permission to perform this action',
        color: 'red',
      });
    } else if (error.response?.status === 404) {
      showNotification({
        title: 'Not found',
        message: 'The requested resource was not found',
        color: 'orange',
      });
    } else if (error.response?.status === 500) {
      showNotification({
        title: 'Server error',
        message: 'An unexpected error occurred. Please try again later.',
        color: 'red',
      });
    } else if (error.code === 'ERR_NETWORK') {
      showNotification({
        title: 'Connection error',
        message: 'Unable to connect to the server. Please check if the backend is running.',
        color: 'red',
      });
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
