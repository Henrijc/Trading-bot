import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, Smartphone, Key, CheckCircle, AlertTriangle, Target, TrendingUp, BarChart3 } from 'lucide-react';

const API = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const LoginSystem = ({ onLoginSuccess }) => {
  const [currentStep, setCurrentStep] = useState('login'); // login, setup_2fa, verify_2fa, analysis
  const [loginData, setLoginData] = useState({
    username: 'admin',
    password: '',
    totp_code: '',
    backup_code: ''
  });
  const [twoFactorSetup, setTwoFactorSetup] = useState({
    qr_code: '',
    totp_secret: '',
    backup_codes: [],
    test_code: ''
  });
  const [loginAnalysis, setLoginAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/auth/login`, loginData);

      if (response.data.success) {
        // Store token
        localStorage.setItem('auth_token', response.data.access_token);
        
        // Set analysis data
        setLoginAnalysis(response.data.login_analysis);
        
        // Move to analysis step
        setCurrentStep('analysis');
        
        setSuccess('Login successful! Reviewing your portfolio...');
      } else if (response.data.requires_2fa) {
        setError('2FA code required');
      } else {
        setError(response.data.error || 'Login failed');
      }
    } catch (error) {
      if (error.response?.status === 401) {
        setError('Invalid credentials or 2FA code');
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const setup2FA = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/auth/setup-2fa`, {
        username: loginData.username
      });

      if (response.data.success) {
        setTwoFactorSetup({
          qr_code: response.data.qr_code,
          totp_secret: response.data.totp_secret,
          backup_codes: response.data.backup_codes,
          test_code: ''
        });
        setCurrentStep('setup_2fa');
        setSuccess('2FA setup initialized. Scan the QR code with Google Authenticator.');
      } else {
        setError(response.data.error);
      }
    } catch (error) {
      setError('Failed to setup 2FA');
    } finally {
      setLoading(false);
    }
  };

  const verify2FASetup = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/auth/verify-2fa`, {
        totp_secret: twoFactorSetup.totp_secret,
        test_code: twoFactorSetup.test_code
      });

      if (response.data.success) {
        setSuccess('2FA setup completed successfully!');
        setCurrentStep('verify_2fa');
        
        // Auto-proceed to login with 2FA
        setTimeout(() => {
          setCurrentStep('login');
          setError('Please login again with your 2FA code');
        }, 2000);
      } else {
        setError('Invalid 2FA code. Please try again.');
      }
    } catch (error) {
      setError('2FA verification failed');
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

  const updateGoals = async (newGoals) => {
    try {
      const token = localStorage.getItem('auth_token');
      await axios.post(`${API}/auth/update-goals`, newGoals, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Goals updated successfully!');
    } catch (error) {
      setError('Failed to update goals');
    }
  };

  const renderLoginStep = () => (
    <Card className="max-w-md mx-auto bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40">
      <CardHeader className="text-center">
        <CardTitle className="text-amber-300 flex items-center justify-center gap-2">
          <Shield className="text-amber-500" size={24} />
          Secure Login
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="block text-amber-400 text-sm font-medium mb-2">Username</label>
          <Input
            type="text"
            value={loginData.username}
            onChange={(e) => setLoginData(prev => ({ ...prev, username: e.target.value }))}
            className="bg-gray-700 border-amber-600/40 text-amber-100"
            disabled
          />
        </div>
        
        <div>
          <label className="block text-amber-400 text-sm font-medium mb-2">Password</label>
          <Input
            type="password"
            value={loginData.password}
            onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
            className="bg-gray-700 border-amber-600/40 text-amber-100"
            placeholder="Enter your password"
          />
        </div>
        
        <div>
          <label className="block text-amber-400 text-sm font-medium mb-2">2FA Code (if enabled)</label>
          <Input
            type="text"
            value={loginData.totp_code}
            onChange={(e) => setLoginData(prev => ({ ...prev, totp_code: e.target.value }))}
            className="bg-gray-700 border-amber-600/40 text-amber-100"
            placeholder="6-digit code from authenticator"
            maxLength={6}
          />
        </div>

        <div>
          <label className="block text-amber-400 text-sm font-medium mb-2">Backup Code (optional)</label>
          <Input
            type="text"
            value={loginData.backup_code}
            onChange={(e) => setLoginData(prev => ({ ...prev, backup_code: e.target.value }))}
            className="bg-gray-700 border-amber-600/40 text-amber-100"
            placeholder="Use if 2FA is unavailable"
          />
        </div>

        {error && (
          <Alert className="border-red-600/40 bg-red-900/20">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <AlertDescription className="text-red-300">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="border-green-600/40 bg-green-900/20">
            <CheckCircle className="h-4 w-4 text-green-400" />
            <AlertDescription className="text-green-300">{success}</AlertDescription>
          </Alert>
        )}

        <div className="flex gap-3">
          <Button
            onClick={handleLogin}
            disabled={loading || !loginData.password}
            className="flex-1 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold"
          >
            {loading ? 'Authenticating...' : 'Login'}
          </Button>
          <Button
            onClick={setup2FA}
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
          >
            <Smartphone className="w-4 h-4 mr-2" />
            Setup 2FA
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const render2FASetupStep = () => (
    <Card className="max-w-lg mx-auto bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40">
      <CardHeader className="text-center">
        <CardTitle className="text-amber-300 flex items-center justify-center gap-2">
          <Smartphone className="text-amber-500" size={24} />
          Setup Google 2FA
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {twoFactorSetup.qr_code && (
          <div className="text-center">
            <p className="text-amber-400 mb-4">1. Scan this QR code with Google Authenticator:</p>
            <img 
              src={twoFactorSetup.qr_code} 
              alt="2FA QR Code" 
              className="mx-auto border rounded-lg"
            />
          </div>
        )}
        
        <div>
          <p className="text-amber-400 text-sm mb-2">2. Or manually enter this secret key:</p>
          <Input
            value={twoFactorSetup.totp_secret}
            readOnly
            className="bg-gray-700 border-amber-600/40 text-amber-100 font-mono text-xs"
          />
        </div>

        <div>
          <p className="text-amber-400 text-sm mb-2">3. Enter the 6-digit code to verify setup:</p>
          <Input
            type="text"
            value={twoFactorSetup.test_code}
            onChange={(e) => setTwoFactorSetup(prev => ({ ...prev, test_code: e.target.value }))}
            className="bg-gray-700 border-amber-600/40 text-amber-100 text-center text-lg"
            placeholder="123456"
            maxLength={6}
          />
        </div>

        <div className="bg-red-900/20 border border-red-600/30 rounded-lg p-4">
          <p className="text-red-400 text-sm font-semibold mb-2">📝 Save these backup codes:</p>
          <div className="grid grid-cols-2 gap-1 text-xs font-mono">
            {twoFactorSetup.backup_codes.map((code, index) => (
              <span key={index} className="text-red-300">{code}</span>
            ))}
          </div>
          <p className="text-red-300/80 text-xs mt-2">Store these codes safely! Use them if you lose access to your authenticator.</p>
        </div>

        <Button
          onClick={verify2FASetup}
          disabled={loading || twoFactorSetup.test_code.length !== 6}
          className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold"
        >
          {loading ? 'Verifying...' : 'Complete 2FA Setup'}
        </Button>
      </CardContent>
    </Card>
  );

  const renderAnalysisStep = () => {
    if (!loginAnalysis) return null;

    const { portfolio_summary, ai_recommendations, immediate_actions } = loginAnalysis;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40">
          <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
            <CardTitle className="text-amber-300 flex items-center gap-3 text-xl">
              <Target className="text-amber-500" size={24} />
              Login Portfolio Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            
            {/* Portfolio Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-r from-green-900/30 to-green-800/30 p-4 rounded-lg border border-green-600/30">
                <div className="text-green-400 text-2xl font-bold font-mono">
                  R{portfolio_summary?.total_value?.toLocaleString()}
                </div>
                <div className="text-green-300 text-sm">Portfolio Value</div>
              </div>
              
              <div className="bg-gradient-to-r from-blue-900/30 to-blue-800/30 p-4 rounded-lg border border-blue-600/30">
                <div className="text-blue-400 text-2xl font-bold">
                  {portfolio_summary?.progress_percentage?.toFixed(1)}%
                </div>
                <div className="text-blue-300 text-sm">Target Progress</div>
              </div>
              
              <div className="bg-gradient-to-r from-purple-900/30 to-purple-800/30 p-4 rounded-lg border border-purple-600/30">
                <div className="text-purple-400 text-2xl font-bold">
                  {portfolio_summary?.holdings_count}
                </div>
                <div className="text-purple-300 text-sm">Active Holdings</div>
              </div>
              
              <div className="bg-gradient-to-r from-amber-900/30 to-amber-800/30 p-4 rounded-lg border border-amber-600/30">
                <div className="text-amber-400 text-2xl font-bold">
                  R{portfolio_summary?.monthly_target?.toLocaleString()}
                </div>
                <div className="text-amber-300 text-sm">Monthly Target</div>
              </div>
            </div>

            {/* AI Recommendations */}
            <div className="bg-gradient-to-r from-gray-700 to-gray-800 p-6 rounded-xl border border-amber-600/20">
              <h3 className="text-amber-300 font-bold text-lg mb-4 flex items-center gap-2">
                <BarChart3 className="text-amber-500" size={20} />
                AI Analysis & Recommendations
              </h3>
              <div className="text-amber-100 whitespace-pre-line leading-relaxed">
                {ai_recommendations}
              </div>
            </div>

            {/* Immediate Actions */}
            {immediate_actions && immediate_actions.length > 0 && (
              <div className="bg-gradient-to-r from-orange-900/30 to-orange-800/30 p-4 rounded-lg border border-orange-600/30">
                <h4 className="text-orange-400 font-semibold mb-3">Immediate Actions:</h4>
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

            {/* Goal Review */}
            <div className="flex gap-4">
              <Button
                onClick={completeLogin}
                className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Continue to Dashboard
              </Button>
              <Button
                onClick={() => {
                  // Open goals adjustment modal
                  const newMonthlyTarget = prompt('Enter new monthly target (ZAR):', portfolio_summary?.monthly_target);
                  if (newMonthlyTarget) {
                    updateGoals({
                      monthly_target: parseFloat(newMonthlyTarget),
                      weekly_target: parseFloat(newMonthlyTarget) / 4,
                      risk_tolerance: 'aggressive'
                    });
                  }
                }}
                className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold"
              >
                <Target className="w-4 h-4 mr-2" />
                Adjust Goals
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4 flex items-center justify-center">
      <div className="w-full max-w-6xl">
        {currentStep === 'login' && renderLoginStep()}
        {currentStep === 'setup_2fa' && render2FASetupStep()}
        {currentStep === 'analysis' && renderAnalysisStep()}
        
        {error && currentStep !== 'login' && (
          <Alert className="mt-4 border-red-600/40 bg-red-900/20">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <AlertDescription className="text-red-300">{error}</AlertDescription>
          </Alert>
        )}

        {success && currentStep !== 'login' && (
          <Alert className="mt-4 border-green-600/40 bg-green-900/20">
            <CheckCircle className="h-4 w-4 text-green-400" />
            <AlertDescription className="text-green-300">{success}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default LoginSystem;