import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Search, Moon, Sun, User as UserIcon, LogOut } from 'lucide-react';
import useAuthStore from '../store/authStore';
import toast from 'react-hot-toast';

const Navbar = ({ sidebarCollapsed, setSidebarCollapsed }) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  return (
    <nav className="glass-nav" style={{
      height: '80px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 30px',
      position: 'sticky',
      top: 0,
      zIndex: 40,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-main)',
          borderRadius: '30px',
          padding: '8px 20px',
          maxWidth: '400px',
          border: '1px solid var(--border-glass)'
        }}>
          <Search size={18} color="var(--text-secondary)" />
          <input 
            type="text" 
            placeholder="Ask AI anything about your data..." 
            style={{
              border: 'none',
              background: 'transparent',
              outline: 'none',
              padding: '4px 12px',
              width: '100%',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                navigate('/sql-playground', { state: { query: e.target.value } });
              }
            }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <button 
          onClick={toggleTheme}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
        >
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>

        <button 
          onClick={() => navigate('/notifications')}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', position: 'relative' }}
        >
          <Bell size={20} />
          <span style={{
            position: 'absolute',
            top: '-2px',
            right: '-2px',
            width: '8px',
            height: '8px',
            background: 'var(--accent)',
            borderRadius: '50%',
            border: '2px solid var(--bg-card)'
          }}></span>
        </button>

        <div style={{ position: 'relative' }}>
          <div 
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px', 
              cursor: 'pointer',
              padding: '6px 12px',
              borderRadius: '20px',
              background: 'var(--bg-main)',
              border: '1px solid var(--border-glass)'
            }}
          >
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                {user?.full_name || user?.username || 'User'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                {user?.role || 'viewer'}
              </div>
            </div>
            <div style={{ 
              width: '36px', 
              height: '36px', 
              borderRadius: '50%', 
              background: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white'
            }}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
              ) : (
                <UserIcon size={18} />
              )}
            </div>
          </div>

          {showProfileMenu && (
            <div 
              className="glass-panel animate-fade-in"
              style={{
                position: 'absolute',
                top: '120%',
                right: 0,
                width: '200px',
                padding: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px'
              }}
            >
              <button 
                onClick={() => { setShowProfileMenu(false); navigate('/profile'); }}
                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', textAlign: 'left', borderRadius: '8px', transition: 'background 0.2s' }}
                onMouseOver={(e) => e.currentTarget.style.background = 'var(--bg-main)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <UserIcon size={16} /> Profile
              </button>
              <div style={{ height: '1px', background: 'var(--border-glass)', margin: '4px 0' }}></div>
              <button 
                onClick={handleLogout}
                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--danger)', textAlign: 'left', borderRadius: '8px', transition: 'background 0.2s' }}
                onMouseOver={(e) => e.currentTarget.style.background = 'var(--bg-main)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <LogOut size={16} /> Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
