import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import useAuthStore from './store/authStore'

// Pages
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SQLPlaygroundPage from './pages/SQLPlaygroundPage'
import DatasetUploadPage from './pages/DatasetUploadPage'
import PredictionsPage from './pages/PredictionsPage'
import AIInsightsPage from './pages/AIInsightsPage'
import RecommendationCenterPage from './pages/RecommendationCenterPage'
import ReportsPage from './pages/ReportsPage'
import AdminPanelPage from './pages/AdminPanelPage'
import SettingsPage from './pages/SettingsPage'
import ProfilePage from './pages/ProfilePage'
import NotificationsPage from './pages/NotificationsPage'

// Protected Route Wrapper
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, user, isChecking } = useAuthStore();
  const location = useLocation();

  if (isChecking) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !user?.is_superuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Layout Wrapper
const DashboardLayout = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  // Reset scroll on route change
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="layout-container">
      <Sidebar collapsed={sidebarCollapsed} setCollapsed={setSidebarCollapsed} />
      <main className={`main-content ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <Navbar sidebarCollapsed={sidebarCollapsed} setSidebarCollapsed={setSidebarCollapsed} />
        <div className="page-wrapper animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
};

function App() {
  const { checkAuth } = useAuthStore();
  
  // Theme check
  useEffect(() => {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
  }, []);

  // Auth check on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Protected Dashboard Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout><DashboardPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><DashboardLayout><AnalyticsPage /></DashboardLayout></ProtectedRoute>} />
      
      {/* NLQ & SQL */}
      <Route path="/sql-playground" element={<ProtectedRoute><DashboardLayout><SQLPlaygroundPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/datasets/upload" element={<ProtectedRoute><DashboardLayout><DatasetUploadPage /></DashboardLayout></ProtectedRoute>} />
      
      {/* ML & XAI */}
      <Route path="/predictions" element={<ProtectedRoute><DashboardLayout><PredictionsPage /></DashboardLayout></ProtectedRoute>} />
      
      {/* BI & Insights */}
      <Route path="/insights" element={<ProtectedRoute><DashboardLayout><AIInsightsPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/recommendations" element={<ProtectedRoute><DashboardLayout><RecommendationCenterPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><DashboardLayout><ReportsPage /></DashboardLayout></ProtectedRoute>} />
      
      {/* User & Settings */}
      <Route path="/profile" element={<ProtectedRoute><DashboardLayout><ProfilePage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><DashboardLayout><SettingsPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute><DashboardLayout><NotificationsPage /></DashboardLayout></ProtectedRoute>} />
      
      {/* Admin */}
      <Route path="/admin" element={<ProtectedRoute requireAdmin={true}><DashboardLayout><AdminPanelPage /></DashboardLayout></ProtectedRoute>} />
      
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
