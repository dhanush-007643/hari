import { create } from 'zustand';
import api from '../api/axios';

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isChecking: true,
  
  login: async (emailOrUsername, password) => {
    try {
      const payload = {
        username: emailOrUsername.trim(),
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
        username: userData.username.trim(),
        email: userData.email.trim(),
        full_name: userData.full_name?.trim() || null,
        password: userData.password
      };
      await api.post('/auth/register', cleanData);
      // Auto login after registration
      return await get().login(cleanData.email, cleanData.password);
    } catch (error) {
      let errorMsg = 'Registration failed';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail.map(d => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(', ') : (typeof detail === 'string' ? detail : JSON.stringify(detail));
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
