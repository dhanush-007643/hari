import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import toast from 'react-hot-toast';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuthStore();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    
    setLoading(true);
    const { success, error } = await register({
      username: formData.username,
      email: formData.email,
      full_name: formData.full_name,
      password: formData.password
    });
    setLoading(false);

    if (success) {
      toast.success('Registration successful!');
      navigate('/dashboard');
    } else {
      toast.error(error || 'Registration failed');
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'var(--bg-main)',
      padding: '20px'
    }}>
      <div className="glass-panel animate-fade-in" style={{ width: '100%', maxWidth: '500px' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontSize: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', margin: 0 }}>
            <span style={{ color: 'var(--primary)' }}>Data</span>Vista<span style={{ color: 'var(--accent)' }}>+</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Create your account</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>Username</label>
              <input 
                type="text" name="username" value={formData.username} onChange={handleChange} required
                style={{
                  width: '100%', padding: '12px', borderRadius: '8px',
                  border: '1px solid var(--border-glass)', background: 'var(--bg-glass)',
                  color: 'var(--text-primary)', outline: 'none'
                }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>Full Name</label>
              <input 
                type="text" name="full_name" value={formData.full_name} onChange={handleChange}
                style={{
                  width: '100%', padding: '12px', borderRadius: '8px',
                  border: '1px solid var(--border-glass)', background: 'var(--bg-glass)',
                  color: 'var(--text-primary)', outline: 'none'
                }}
              />
            </div>
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>Email Address</label>
            <input 
              type="email" name="email" value={formData.email} onChange={handleChange} required
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
              type="password" name="password" value={formData.password} onChange={handleChange} required
              placeholder="Min 8 chars, 1 uppercase, 1 number"
              style={{
                width: '100%', padding: '12px', borderRadius: '8px',
                border: '1px solid var(--border-glass)', background: 'var(--bg-glass)',
                color: 'var(--text-primary)', outline: 'none'
              }}
            />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>Confirm Password</label>
            <input 
              type="password" name="confirm_password" value={formData.confirm_password} onChange={handleChange} required
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
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Already have an account? <span style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 600 }} onClick={() => navigate('/login')}>Sign In</span>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
