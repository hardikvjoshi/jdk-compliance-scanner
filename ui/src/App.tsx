import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Login } from './pages/Login';
import { Layout } from './components/layout';
import { Dashboard } from './pages/Dashboard';
import { Configuration } from './pages/Configuration';
import { Clusters } from './pages/Configuration/Clusters';
import { Projects } from './pages/Configuration/Projects';
import { Targets } from './pages/Configuration/Targets';
import { JDKVersions } from './pages/Configuration/JDKVersions';
import { Scanner } from './pages/Scanner';
import { Reports } from './pages/Reports';
import { Exemptions } from './pages/Exemptions';
import './styles/index.css';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, checkAuth, isLoading } = useAuthStore();

  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading) {
    return <div className="container">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="scanner" element={<Scanner />} />
          <Route path="reports" element={<Reports />} />
          <Route path="configuration" element={<Configuration />}>
            <Route index element={<Navigate to="/configuration/clusters" replace />} />
            <Route path="clusters" element={<Clusters />} />
            <Route path="projects" element={<Projects />} />
            <Route path="targets" element={<Targets />} />
            <Route path="jdk-versions" element={<JDKVersions />} />
          </Route>
          <Route path="exemptions" element={<Exemptions />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
