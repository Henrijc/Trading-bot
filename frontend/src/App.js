import React, { useState } from 'react';
import SimpleDashboard from './components/SimpleDashboard.jsx';
import SimpleLogin from './components/SimpleLogin.jsx';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <SimpleLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="App">
      <SimpleDashboard onLogout={handleLogout} />
    </div>
  );
}

export default App;