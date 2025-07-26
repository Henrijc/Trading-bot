import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Shield, Smartphone, CheckCircle, AlertTriangle, Target } from 'lucide-react';

// The API endpoint for your backend. Ensure this is correct.
const API = process.env.REACT_APP_BACKEND_URL || import.meta.env?.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const LoginSystem = ({ onLoginSuccess }) => {
  const [currentStep, setCurrentStep] = useState('login');
  const [loginData, setLoginData] = useState({
    username: 'Henrijc',
    password: '',
    totp_code: '',
    backup_code: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loginAnalysis, setLoginAnalysis] = useState(null);

  // --- FIX: This function now makes a real API call to the backend ---
  const handleLogin = async (e) => {
    // Prevent the form from reloading the page
    e.preventDefault();

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // The actual API call to your backend's login endpoint
      const response = await axios.post(`${API}/api/auth/login`, {
        username: loginData.username,
        password: loginData.password,
        totp_code: loginData.totp_code,
        backup_code: loginData.backup_code,
      });

      // Assuming your backend returns a token and analysis data upon successful login
      const { token, analysis } = response.data;

      // Store the token and analysis data
      localStorage.setItem('auth_token', token);
      setLoginAnalysis(analysis);
      
      // Move to the next step
      setCurrentStep('analysis');
      setSuccess('Login successful! Analyzing your portfolio...');

    } catch (err) {
      // Provide more specific error feedback
      if (err.response) {
        // The backend responded with an error (e.g., 401 Unauthorized, 403 Forbidden)
        setError(err.response.data.detail || 'Login failed. Please check your credentials and 2FA code.');
      } else if (err.request) {
        // The request was made but no response was received (backend might be down)
        setError('Network Error: Could not connect to the server.');
      } else {
        // Something else went wrong
        setError('An unexpected error occurred during login.');
      }
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  const completeLogin = () => {
    onLoginSuccess({
      token: localStorage.getItem('auth_token'),
      analysis: loginAnalysis
    });
  };

  const renderLoginStep = () => (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
      <Card className="max-w-md w-full bg-gradient-to-br from-gray-800 to-gray-900 border border-cyan-600/40">
        <CardHeader className="text-center">
          <CardTitle className="text-cyan-300 flex items-center justify-center gap-2">
            <Shield className="text-cyan-500" size={24} />
            Henrijc's Secure Login
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* --- FIX: Wrapped inputs in a <form> and used its onSubmit handler --- */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="bg-blue-900/20 border border-blue-600/30 rounded-lg p-3 mb-4">
              <p className="text-blue-400 text-sm font-semibold">🔐 Your Login Details:</p>
              <p className="text-blue-300/80 text-xs mt-1">
                Username: Henrijc<br/>
                Password: H3nj3n<br/>
                2FA Secret: OPRYF3QGNFGQGFUPVRPWU2C33C4HWHFP
              </p>
            </div>

            <div>
              <label className="block text-cyan-400 text-sm font-medium mb-2">Username</label>
              <Input
                type="text"
                value={loginData.username}
                onChange={(e) => setLoginData(prev => ({ ...prev, username: e.target.value }))}
                className="bg-gray-700 border-cyan-600/40 text-cyan-100"
                placeholder="Enter your username"
              />
            </div>
            
            <div>
              <label className="block text-cyan-400 text-sm font-medium mb-2">Password</label>
              <Input
                type="password"
                value={loginData.password}
                onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
                className="bg-gray-700 border-cyan-600/40 text-cyan-100"
                placeholder="Enter your password"
              />
            </div>
            
            <div>
              <label className="block text-cyan-400 text-sm font-medium mb-2">2FA Code (Google Authenticator)</label>
              <Input
                type="text"
                value={loginData.totp_code}
                onChange={(e) => setLoginData(prev => ({ ...prev, totp_code: e.target.value }))}
                className="bg-gray-700 border-cyan-600/40 text-cyan-100"
                placeholder="6-digit code from app"
                maxLength={6}
              />
            </div>

            <div>
              <label className="block text-cyan-400 text-sm font-medium mb-2">Backup Code (if needed)</label>
              <Input
                type="text"
                value={loginData.backup_code}
                onChange={(e) => setLoginData(prev => ({ ...prev, backup_code: e.target.value }))}
                className="bg-gray-700 border-cyan-600/40 text-cyan-100"
                placeholder="Use if 2FA unavailable"
              />
            </div>

            {error && (
              <div className="border border-red-600/40 bg-red-900/20 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                  <span className="text-red-300">{error}</span>
                </div>
              </div>
            )}

            {success && (
              <div className="border border-green-600/40 bg-green-900/20 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-400" />
                  <span className="text-green-300">{success}</span>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                type="submit" // Use type="submit" for forms
                disabled={loading || !loginData.password}
                className="flex-1 bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-700 hover:to-cyan-800 text-black font-semibold"
              >
                {loading ? 'Authenticating...' : 'Login & Analyze Portfolio'}
              </Button>
            </div>

            <div className="text-center mt-4">
              <p className="text-cyan-400/70 text-xs">
                💡 Add to Google Authenticator: OPRYF3QGNFGQGFUPVRPWU2C33C4HWHFP
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );

  const renderAnalysisStep = () => {
    if (!loginAnalysis) return null;

    const { portfolio_summary, ai_recommendations, immediate_actions } = loginAnalysis;

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-cyan-600/40">
            <CardHeader className="border-b border-cyan-600/30 bg-gradient-to-r from-cyan-900/20 to-cyan-800/20">
              <CardTitle className="text-cyan-300 flex items-center gap-3 text-xl">
                <Target className="text-cyan-500" size={24} />
                Welcome Back, Henrijc! Portfolio Analysis Complete
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              
              {/* Portfolio Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-r from-green-900/30 to-green-800/30 p-4 rounded-lg border border-green-600/30">
                  <div className="text-green-400 text-2xl font-bold font-mono">
                    R{portfolio_summary?.total_value?.toLocaleString()}
                  </div>
                  <div className="text-green-300 text-sm">Current Portfolio Value</div>
                </div>
                
                <div className="bg-gradient-to-r from-blue-900/30 to-blue-800/30 p-4 rounded-lg border border-blue-600/30">
                  <div className="text-blue-400 text-2xl font-bold">
                    {portfolio_summary?.progress_percentage?.toFixed(1)}%
                  </div>
                  <div className="text-blue-300 text-sm">Target Progress 🚀</div>
                </div>
                
                <div className="bg-gradient-to-r from-purple-900/30 to-purple-800/30 p-4 rounded-lg border border-purple-600/30">
                  <div className="text-purple-400 text-2xl font-bold">
                    {portfolio_summary?.holdings_count}
                  </div>
                  <div className="text-purple-300 text-sm">Active Holdings</div>
                </div>
                
                <div className="bg-gradient-to-r from-cyan-900/30 to-cyan-800/30 p-4 rounded-lg border border-cyan-600/30">
                  <div className="text-cyan-400 text-2xl font-bold">
                    R{portfolio_summary?.monthly_target?.toLocaleString()}
                  </div>
                  <div className="text-cyan-300 text-sm">Monthly Target</div>
                </div>
              </div>

              {/* AI Recommendations */}
              <div className="bg-gradient-to-r from-gray-700 to-gray-800 p-6 rounded-xl border border-cyan-600/20">
                <h3 className="text-cyan-300 font-bold text-lg mb-4 flex items-center gap-2">
                  <Smartphone className="text-cyan-500" size={20} />
                  AI Portfolio Analysis & Recommendations
                </h3>
                <div className="text-cyan-100 whitespace-pre-line leading-relaxed text-sm">
                  {ai_recommendations}
                </div>
              </div>

              {/* Immediate Actions */}
              {immediate_actions && immediate_actions.length > 0 && (
                <div className="bg-gradient-to-r from-orange-900/30 to-orange-800/30 p-4 rounded-lg border border-orange-600/30">
                  <h4 className="text-orange-400 font-semibold mb-3">⚡ Immediate Actions Required:</h4>
                  <ul className="space-y-2">
                    {immediate_actions.map((action, index) => (
                      <li key={index} className="text-orange-200 text-sm flex items-start gap-2">
                        <span className="text-orange-500 mt-1">•</span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Continue Button */}
              <div className="text-center">
                <Button
                  onClick={completeLogin}
                  className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold px-8 py-3 text-lg"
                >
                  <CheckCircle className="w-5 h-5 mr-2" />
                  Continue to Trading Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };

  if (currentStep === 'login') {
    return renderLoginStep();
  } else if (currentStep === 'analysis') {
    return renderAnalysisStep();
  }

  return null;
};

export default LoginSystem;