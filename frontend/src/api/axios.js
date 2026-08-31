import baseAxios from 'axios';
import { toast } from 'react-hot-toast';

const apiUrl = import.meta.env.VITE_API_URL;
let baseURL = '/api/v1';

if (apiUrl) {
  const cleanUrl = apiUrl.replace(/\/+$/, '');
  baseURL = cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
}

const api = baseAxios.create({
  baseURL,
  timeout: 45000, // 45s timeout to allow waking sleeping backend instances
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401s and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthRequest = originalRequest?.url?.includes('/auth/login') || 
                          originalRequest?.url?.includes('/auth/register') ||
                          originalRequest?.url?.includes('/auth/refresh');
    
    // Only attempt token refresh for protected routes that receive a 401
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRequest) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        // Try to refresh token
        const res = await baseAxios.post(`${baseURL}/auth/refresh`, null, {
          params: { token: refreshToken }
        });
        
        const { access_token } = res.data;
        localStorage.setItem('access_token', access_token);
        
        // Update header and retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
        
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }
    
    let errorMsg = "An unexpected error occurred";
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        errorMsg = detail.map(d => (d.msg || (typeof d === 'string' ? d : JSON.stringify(d)))).join(', ');
      } else if (typeof detail === 'string') {
        errorMsg = detail;
      } else {
        errorMsg = JSON.stringify(detail);
      }
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorMsg = "Server took too long to respond. If running on Render free tier, please wait 30s for the server to wake up and try again.";
    } else if (error.message === 'Network Error' || !error.response) {
      errorMsg = "Network Error: Could not connect to backend. Please verify your connection or backend URL.";
    } else if (error.message) {
      errorMsg = error.message;
    }

    // Do not show duplicate global toasts for auth requests handled in their own page handlers
    if (!isAuthRequest) {
      toast.error(errorMsg);
    }
    
    return Promise.reject(error);
  }
);

export default api;
