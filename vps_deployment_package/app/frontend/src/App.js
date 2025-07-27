import React, { useState, useEffect } from 'react';
import CryptoTraderCoach from './components/CryptoTraderCoach.jsx';
import SimpleLogin from './components/SimpleLogin.jsx';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userSession, setUserSession] = useState(null);
  
  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      setIsAuthenticated(true);
      setUserSession({ token });
    }
  }, []);

  const handleLoginSuccess = (session) => {
    localStorage.setItem('auth_token', session.token);
    setIsAuthenticated(true);
    setUserSession(session);
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    setIsAuthenticated(false);
    setUserSession(null);
  };

  if (!isAuthenticated) {
    return <SimpleLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="App">
      <CryptoTraderCoach 
        userSession={userSession}
        onLogout={handleLogout}
      />
    </div>
  );
}

export default App;