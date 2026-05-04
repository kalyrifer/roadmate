import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { BASE_URL } from '../../config';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      const isAuthEndpoint =
        url.includes('/auth/login') || url.includes('/auth/register');

      if (isAuthEndpoint) {
        const err = new Error('AUTH_INVALID_CREDENTIALS');
        return Promise.reject(err);
      }

      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
    }
    
    // Handle 400 errors (validation errors)
    if (error.response?.status === 400) {
      const validationError = error.response.data;
      // Handle both object { detail: "..." } and plain string responses
      let errorMessage = 'Validation error';
      if (typeof validationError === 'string') {
        errorMessage = validationError;
      } else if (validationError && typeof validationError === 'object' && 'detail' in validationError) {
        errorMessage = validationError.detail;
      }
      console.error('Validation error:', errorMessage);
      return Promise.reject(errorMessage);
    }
    
    // Handle 500 errors (server errors)
    if (error.response?.status === 500) {
      const serverError = error.response.data;
      const errorMessage = serverError.detail || 'Server error';
      console.error('Server error:', errorMessage);
      return Promise.reject(errorMessage);
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      return Promise.reject('Network error. Please check your connection.');
    }
    
    return Promise.reject(error);
  }
);

export default api;
