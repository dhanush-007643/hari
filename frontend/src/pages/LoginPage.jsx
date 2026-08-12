import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import toast from 'react-hot-toast';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }
    
    setLoading(true);
    const { success, error } = await login(email, password);
    setLoading(false);

    if (success) {
      toast.success('Login successful');
      navigate(from, { replace: true });
    } else {
      toast.error(error || 'Login failed');
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'var(--bg-main)'
    }}>
      <div className="glass-panel animate-fade-in" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontSize: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', margin: 0 }}>
            <span style={{ color: 'var(--primary)' }}>Data</span>Vista<span style={{ color: 'var(--accent)' }}>+</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>Email or Username</label>
            <input 
              type="text" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@datavista.com"
              style={{
                width: '100%', padding: '12px', borderRadius: '8px',
                border: '1px solid var(--border-glass)', background: 'var(--bg-glass)',
                color: 'var(--text-primary)', outline: 'none'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%', padding: '12px', borderRadius: '8px',
                border: '1px solid var(--border-glass)', background: 'var(--bg-glass)',
                color: 'var(--text-primary)', outline: 'none'
              }}
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading}
            style={{ marginTop: '10px', padding: '14px', width: '100%' }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Don't have an account? <span style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 600 }} onClick={() => navigate('/register')}>Register</span>
        </div>
        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Default Admin: <strong>admin@datavista.com / Admin@123</strong>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
