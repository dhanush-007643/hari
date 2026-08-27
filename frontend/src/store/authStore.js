import { create } from 'zustand';
import api from '../api/axios';

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isChecking: true,
  
  login: async (email, password) => {
    try {
      // For OAuth2PasswordRequestForm we need to send form data
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const res = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const { access_token, refresh_token, user } = res.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      set({ user, isAuthenticated: true });
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      let errorMsg = 'Invalid credentials';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail.map(d => d.msg || d).join(', ') : (typeof detail === 'string' ? detail : JSON.stringify(detail));
      }
      return { 
        success: false, 
        error: errorMsg 
      };
    }
  },
  
  register: async (userData) => {
    try {
      await api.post('/auth/register', userData);
      // Auto login after registration
      return await get().login(userData.email, userData.password);
    } catch (error) {
      let errorMsg = 'Registration failed';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail.map(d => d.msg || d).join(', ') : (typeof detail === 'string' ? detail : JSON.stringify(detail));
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
