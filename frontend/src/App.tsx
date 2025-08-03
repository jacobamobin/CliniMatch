import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { TrialProvider } from './contexts/TrialContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import ResultsPage from './pages/ResultsPage';
import MapPage from './pages/MapPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <TrialProvider>
          <Router>
            <div className="App min-h-screen bg-slate-900">
              <Header />
              <main>
                <Routes>
                  <Route path="/" element={<LandingPage />} />
                  <Route 
                    path="/dashboard" 
                    element={
                      <ProtectedRoute>
                        <DashboardPage />
                      </ProtectedRoute>
                    } 
                  />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/results" element={<ResultsPage />} />
                  <Route path="/map" element={<MapPage />} />
                  <Route path="/search/:method" element={<ProfilePage />} />
                </Routes>
        </main>
              <Footer />
      </div>
          </Router>
        </TrialProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
