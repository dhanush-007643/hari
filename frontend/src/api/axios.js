import baseAxios from 'axios';
import { toast } from 'react-hot-toast';

const apiUrl = import.meta.env.VITE_API_URL;
if (!apiUrl && import.meta.env.PROD) {
  console.error("CRITICAL ERROR: VITE_API_URL is not set! Requests will go to Vercel and fail with 405 Method Not Allowed.");
}
let baseURL = '/api/v1';
if (apiUrl) {
  // Strip trailing slashes
  const cleanUrl = apiUrl.replace(/\/+$/, '');
  // Append /api/v1 only if they didn't already include it
  baseURL = cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
}

const api = baseAxios.create({
  baseURL,
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
    
    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }
        
        // Try to refresh token
        const res = await baseAxios.post('/api/v1/auth/refresh', null, {
          params: { token: refreshToken }
        });
        
        const { access_token } = res.data;
        localStorage.setItem('access_token', access_token);
        
        // Update header and retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
        
      } catch (refreshError) {
        // Refresh failed, clear auth and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    const errorMsg = error.response?.data?.detail || error.message || "An unexpected error occurred";
    if (error.response?.status !== 401) {
      toast.error(errorMsg);
    }
    
    return Promise.reject(error);
  }
);

export default api;
