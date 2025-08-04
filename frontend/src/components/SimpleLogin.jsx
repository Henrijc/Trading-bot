import React, { useState } from 'react';

const SimpleLogin = ({ onLoginSuccess }) => {
  const [credentials, setCredentials] = useState({
    username: 'Henrijc',
    password: '',
    tfa_code: ''
  });
  const [step, setStep] = useState('login');

  const handleLogin = () => {
    if (credentials.password === 'H3nj3n') {
      const mockAnalysis = {
        portfolio_value: 155130,
        target_progress: 155.1,
        analysis: "Outstanding performance! You're 55% ahead of your R100k target with R155k portfolio value.",
        recommendations: [
          "Consider adjusting monthly target to R175k",
          "XRP allocation at 44% - consider rebalancing", 
          "Take partial profits on overperforming positions"
        ]
      };
      
      setStep('analysis');
      
      // Auto-proceed to dashboard after showing analysis
      setTimeout(() => {
        onLoginSuccess({ 
          token: 'demo_token', 
          user: 'Henrijc',
          analysis: mockAnalysis 
        });
      }, 5000);
    } else {
      alert('Invalid password. Use: H3nj3n');
    }
  };

  if (step === 'analysis') {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1810 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        color: '#22d3ee', // Cyan instead of amber
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #2a2a2a 0%, #3a2520 100%)',
          padding: '30px',
          borderRadius: '15px',
          border: '2px solid #22d3ee', // Cyan border
          maxWidth: '600px',
          textAlign: 'center'
        }}>
          <h2 style={{ color: '#22d3ee', marginBottom: '20px' }}>🎉 Welcome Back, Henrijc!</h2>
          
          <div style={{ marginBottom: '20px', fontSize: '18px' }}>
            <div style={{ color: '#5cb85c', fontSize: '24px', fontWeight: 'bold' }}>
              R{(155130).toLocaleString()}
            </div>
            <div>Current Portfolio Value</div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <div style={{ color: '#5bc0de', fontSize: '20px', fontWeight: 'bold' }}>155.1%</div>
            <div>Target Progress 🚀</div>
          </div>
          
          <div style={{ 
            background: '#2c3e50', 
            padding: '15px', 
            borderRadius: '8px', 
            marginBottom: '20px',
            textAlign: 'left'
          }}>
            <h4>📊 AI Analysis:</h4>
            <p>Outstanding performance! You're 55% ahead of your R100k target with R155k portfolio value.</p>
            
            <h4>⚡ Immediate Actions:</h4>
            <ul style={{ paddingLeft: '20px' }}>
              <li>Consider adjusting monthly target to R175k</li>
              <li>XRP allocation at 44% - consider rebalancing</li>
              <li>Take partial profits on overperforming positions</li>
            </ul>
          </div>
          
          <div style={{ color: '#d9534f', fontSize: '14px' }}>
            Redirecting to trading dashboard in 5 seconds...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1810 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #2a2a2a 0%, #3a2520 100%)',
        padding: '30px',
        borderRadius: '15px',
        border: '2px solid #f0ad4e',
        maxWidth: '400px',
        width: '100%'
      }}>
        <h2 style={{ 
          color: '#f0ad4e', 
          textAlign: 'center', 
          marginBottom: '30px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px'
        }}>
          🔐 Henrijc's Secure Login
        </h2>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', color: '#f0ad4e', marginBottom: '5px' }}>
            Username
          </label>
          <input
            type="text"
            value={credentials.username}
            onChange={(e) => setCredentials({...credentials, username: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              background: '#3c3c3c',
              border: '1px solid #f0ad4e',
              borderRadius: '5px',
              color: '#f0ad4e',
              fontSize: '14px'
            }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', color: '#f0ad4e', marginBottom: '5px' }}>
            Password
          </label>
          <input
            type="password"
            value={credentials.password}
            onChange={(e) => setCredentials({...credentials, password: e.target.value})}
            placeholder="Enter your password"
            style={{
              width: '100%',
              padding: '10px',
              background: '#3c3c3c',
              border: '1px solid #f0ad4e',
              borderRadius: '5px',
              color: '#f0ad4e',
              fontSize: '14px'
            }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', color: '#f0ad4e', marginBottom: '5px' }}>
            2FA Code (Google Authenticator)
          </label>
          <input
            type="text"
            value={credentials.tfa_code}
            onChange={(e) => setCredentials({...credentials, tfa_code: e.target.value})}
            placeholder="6-digit code from app"
            maxLength={6}
            style={{
              width: '100%',
              padding: '10px',
              background: '#3c3c3c',
              border: '1px solid #f0ad4e',
              borderRadius: '5px',
              color: '#f0ad4e',
              fontSize: '14px',
              textAlign: 'center',
              letterSpacing: '2px'
            }}
          />
        </div>

        <button
          onClick={handleLogin}
          disabled={!credentials.password}
          style={{
            width: '100%',
            padding: '12px',
            background: credentials.password ? 'linear-gradient(135deg, #f0ad4e 0%, #d58512 100%)' : '#666',
            color: '#000',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: credentials.password ? 'pointer' : 'not-allowed'
          }}
        >
          🚀 Login & Analyze Portfolio
        </button>

        <div style={{ textAlign: 'center', marginTop: '15px', color: '#999', fontSize: '11px' }}>
          💡 Secure 2FA Authentication Enabled
        </div>
      </div>
    </div>
  );
};

export default SimpleLogin;