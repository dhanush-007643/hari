import { create } from 'zustand';
import api from '../api/axios';

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isChecking: true,
  
  login: async (emailOrUsername, password) => {
    try {
      const identifier = (emailOrUsername || '').trim();
      const payload = {
        username: identifier,
        email: identifier,
        password: password
      };
      
      const res = await api.post('/auth/login', payload);
      const { access_token, refresh_token, user } = res.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      set({ user, isAuthenticated: true, isChecking: false });
      return { success: true, user };
    } catch (error) {
      console.error('Login error:', error);
      let errorMsg = 'Invalid credentials';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail.map(d => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(', ') : (typeof detail === 'string' ? detail : JSON.stringify(detail));
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMsg = 'Server took too long to respond. If running on Render free tier, please wait ~30s for the server to wake up and try again.';
      } else if (error.message === 'Network Error' || !error.response) {
        errorMsg = 'Cannot connect to backend server. If using Render free tier, the instance might be waking up (please retry in 30s) or check your VITE_API_URL.';
      } else if (error.message) {
        errorMsg = error.message;
      }
      return { 
        success: false, 
        error: errorMsg 
      };
    }
  },
  
  register: async (userData) => {
    try {
      const cleanData = {
        username: (userData.username || '').trim(),
        email: (userData.email || '').trim(),
        full_name: (userData.full_name || '').trim() || null,
        password: userData.password
      };
      
      const res = await api.post('/auth/register', cleanData);
      
      if (res.data?.access_token) {
        const { access_token, refresh_token, user } = res.data;
        localStorage.setItem('access_token', access_token);
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token);
        }
        set({ user, isAuthenticated: true, isChecking: false });
        return { success: true, user };
      }
      
      // Fallback auto login
      return await get().login(cleanData.username, cleanData.password);
    } catch (error) {
      console.error('Registration error:', error);
      let errorMsg = 'Registration failed';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail.map(d => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(', ') : (typeof detail === 'string' ? detail : JSON.stringify(detail));
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMsg = 'Server took too long to respond. Please wait ~30s and try again.';
      } else if (error.message === 'Network Error' || !error.response) {
        errorMsg = 'Cannot connect to backend server. Please verify your connection or backend URL.';
      } else if (error.message) {
        errorMsg = error.message;
      }
      return { 
        success: false, 
        error: errorMsg 
      };
    }
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },
  
  checkAuth: async () => {
    set({ isChecking: true });
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        set({ user: null, isAuthenticated: false, isChecking: false });
        return;
      }
      
      const res = await api.get('/auth/me');
      set({ user: res.data, isAuthenticated: true, isChecking: false });
    } catch (error) {
      // Interceptor will handle refresh, if that fails it clears storage
      const stillHasToken = !!localStorage.getItem('access_token');
      set({ 
        user: null, 
        isAuthenticated: stillHasToken, // keep true if interceptor is refreshing
        isChecking: false 
      });
    }
  },
  
  updateProfile: async (data) => {
    try {
      await api.put('/auth/me', data);
      await get().checkAuth(); // refresh user data
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Update failed' };
    }
  }
}));

export default useAuthStore;
