import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserPlus, Eye, EyeOff, Sparkles, CheckCircle2, XCircle, User, Mail, Lock, UserCheck } from 'lucide-react';
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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const { register, isAuthenticated, isChecking } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isChecking && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, isChecking, navigate]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Password rules validation
  const hasMinLength = formData.password.length >= 8;
  const hasUpper = /[A-Z]/.test(formData.password);
  const hasLower = /[a-z]/.test(formData.password);
  const hasDigit = /[0-9]/.test(formData.password);
  const isPasswordValid = hasMinLength && hasUpper && hasLower && hasDigit;
  const passwordsMatch = formData.password.length > 0 && formData.password === formData.confirm_password;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.username.trim() || !formData.email.trim() || !formData.password) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (!isPasswordValid) {
      toast.error('Password does not meet the security requirements (8+ chars, uppercase, lowercase, number)');
      return;
    }

    if (!passwordsMatch) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);
    const { success, error } = await register({
      username: formData.username.trim(),
      email: formData.email.trim(),
      full_name: formData.full_name.trim() || null,
      password: formData.password
    });
    setLoading(false);

    if (success) {
      toast.success('Account created successfully! Welcome to DataVista+');
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
      background: 'radial-gradient(ellipse at top, rgba(108, 99, 255, 0.15), transparent 70%), var(--bg-main)',
      padding: '24px'
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: '100%',
        maxWidth: '480px',
        padding: '36px',
        borderRadius: '20px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.15)',
        border: '1px solid var(--border-glass)'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, var(--primary), var(--accent))',
            color: '#fff',
            marginBottom: '12px',
            boxShadow: '0 8px 20px rgba(108, 99, 255, 0.35)'
          }}>
            <Sparkles size={24} />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 6px 0', letterSpacing: '-0.5px' }}>
            Create Your Account
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
            Join <span style={{ color: 'var(--primary)', fontWeight: 600 }}>DataVista+</span> to unlock AI-powered insights
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
                <User size={14} color="var(--primary)" /> Username *
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="johndoe"
                required
                autoComplete="username"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-main)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
                <UserCheck size={14} color="var(--primary)" /> Full Name
              </label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="John Doe"
                autoComplete="name"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-main)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
              <Mail size={14} color="var(--primary)" /> Email Address *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="john@example.com"
              required
              autoComplete="email"
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-main)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
              <Lock size={14} color="var(--primary)" /> Password *
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                required
                autoComplete="new-password"
                style={{
                  width: '100%',
                  padding: '10px 38px 10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-main)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-secondary)',
                  padding: 0,
                  display: 'flex'
                }}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Real-time Password Strength Check */}
            {formData.password && (
              <div style={{
                marginTop: '8px',
                padding: '8px 12px',
                background: 'rgba(0, 0, 0, 0.03)',
                borderRadius: '8px',
                fontSize: '0.78rem',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '6px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: hasMinLength ? 'var(--success)' : 'var(--text-secondary)' }}>
                  {hasMinLength ? <CheckCircle2 size={13} /> : <XCircle size={13} />} 8+ characters
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: hasUpper ? 'var(--success)' : 'var(--text-secondary)' }}>
                  {hasUpper ? <CheckCircle2 size={13} /> : <XCircle size={13} />} 1 Uppercase (A-Z)
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: hasLower ? 'var(--success)' : 'var(--text-secondary)' }}>
                  {hasLower ? <CheckCircle2 size={13} /> : <XCircle size={13} />} 1 Lowercase (a-z)
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: hasDigit ? 'var(--success)' : 'var(--text-secondary)' }}>
                  {hasDigit ? <CheckCircle2 size={13} /> : <XCircle size={13} />} 1 Number (0-9)
                </div>
              </div>
            )}
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
              <Lock size={14} color="var(--primary)" /> Confirm Password *
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                placeholder="••••••••"
                required
                autoComplete="new-password"
                style={{
                  width: '100%',
                  padding: '10px 38px 10px 12px',
                  borderRadius: '8px',
                  border: `1px solid ${formData.confirm_password ? (passwordsMatch ? 'var(--success)' : 'var(--danger)') : 'var(--border-glass)'}`,
                  background: 'var(--bg-main)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-secondary)',
                  padding: 0,
                  display: 'flex'
                }}
                tabIndex={-1}
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {formData.confirm_password && !passwordsMatch && (
              <span style={{ fontSize: '0.78rem', color: 'var(--danger)', marginTop: '4px', display: 'block' }}>
                Passwords do not match
              </span>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || (formData.password && !isPasswordValid)}
            style={{
              marginTop: '10px',
              padding: '13px',
              width: '100%',
              fontSize: '0.98rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              borderRadius: '10px'
            }}
          >
            {loading ? (
              'Creating Account...'
            ) : (
              <>
                <UserPlus size={18} /> Complete Registration
              </>
            )}
          </button>
        </form>

        {/* Login Link */}
        <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <span
            style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 600, textDecoration: 'underline' }}
            onClick={() => navigate('/login')}
          >
            Sign In
          </span>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
