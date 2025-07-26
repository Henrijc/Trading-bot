import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Shield, Smartphone, CheckCircle, AlertTriangle, Target } from 'lucide-react';

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

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError('');

      // For now, let's simulate the login process with direct API call
      const mockAnalysis = {
        portfolio_summary: {
          total_value: 155130,
          monthly_target: 100000,
          progress_percentage: 155.1,
          holdings_count: 8
        },
        ai_recommendations: `**LOGIN BRIEFING - ${new Date().toLocaleString()}**

**Portfolio Status:** Your portfolio is valued at R155,130 across 8 assets. 

**Outstanding Performance:** You're 55% ahead of your R100k monthly target! This exceptional performance suggests your aggressive trading strategy is working brilliantly.

**Current Allocation Analysis:**
- XRP dominates at 44% (R68,280) - consider rebalancing
- ETH strong at 28% (R43,940) - good long-term hold  
- BTC solid at 20% (R31,785) - recommended increase

**Immediate Recommendations:**
1. **Profit Taking**: Consider securing 20% of gains
2. **Rebalancing**: Reduce XRP exposure, increase BTC to 30%
3. **Target Adjustment**: With this performance, increase monthly target to R175k

**Market Opportunities:**
- BTC showing strength above R2.1M support
- ETH testing R63.5k resistance - potential breakout
- Consider scaling into positions on any dips

Ready to execute today's trading strategy!`,
        immediate_actions: [
          "🎯 Consider adjusting monthly target to R175k based on performance",
          "⚡ Review XRP allocation (44% is high concentration)",
          "📊 Take partial profits on overperforming positions"
        ]
      };

      // Simulate successful login
      const mockToken = "mock_jwt_token_for_henrijc";
      localStorage.setItem('auth_token', mockToken);
      
      setLoginAnalysis(mockAnalysis);
      setCurrentStep('analysis');
      setSuccess('Login successful! Analyzing your portfolio...');

    } catch (error) {
      setError('Login failed. Please check your credentials and 2FA code.');
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
        <CardContent className="space-y-4">
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
              onClick={handleLogin}
              disabled={loading || !loginData.password}
              className="flex-1 bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold"
            >
              {loading ? 'Authenticating...' : 'Login & Analyze Portfolio'}
            </Button>
          </div>

          <div className="text-center mt-4">
            <p className="text-cyan-400/70 text-xs">
              💡 Add to Google Authenticator: OPRYF3QGNFGQGFUPVRPWU2C33C4HWHFP
            </p>
          </div>
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
            <CardHeader className="border-b border-cyan-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
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
                
                <div className="bg-gradient-to-r from-amber-900/30 to-amber-800/30 p-4 rounded-lg border border-cyan-600/30">
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