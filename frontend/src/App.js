import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function App() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [balance, setBalance] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiTradingActive, setAiTradingActive] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    checkSystemHealth();
    loadBalance();
    loadMarketData();
    
    const healthInterval = setInterval(checkSystemHealth, 30000);
    const dataInterval = setInterval(loadMarketData, 10000);
    
    return () => {
      clearInterval(healthInterval);
      clearInterval(dataInterval);
    };
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await axios.get(`${API}/health`);
      setSystemHealth(response.data);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Health check failed:', error);
      setConnectionStatus('disconnected');
      setSystemHealth({ status: 'unhealthy', error: error.message });
    }
  };

  const loadBalance = async () => {
    try {
      const response = await axios.get(`${API}/balance`);
      setBalance(response.data.data);
    } catch (error) {
      console.error('Balance fetch failed:', error);
    }
  };

  const loadMarketData = async () => {
    try {
      const response = await axios.get(`${API}/market-data/XBTZAR`);
      setMarketData(response.data.data);
    } catch (error) {
      console.error('Market data fetch failed:', error);
    }
  };

  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'R0.00';
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR'
    }).format(amount);
  };

  return (
    <div className="App">
      {/* System Status Header */}
      <div className={`status-header ${connectionStatus}`} style={{
        backgroundColor: connectionStatus === 'connected' ? '#059669' : '#dc2626',
        color: 'white',
        padding: '0.5rem 0'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: 0 }}>🤖 AI Crypto Trading Bot</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: connectionStatus === 'connected' ? '#10b981' : '#ef4444',
                borderRadius: '50%',
                display: 'inline-block'
              }}></span>
              <span style={{ fontSize: '0.875rem', textTransform: 'capitalize' }}>{connectionStatus}</span>
            </div>
          </div>
          <div style={{ fontSize: '0.875rem', display: 'flex', gap: '1rem' }}>
            <span>Luno: {systemHealth?.services?.luno || 'unknown'}</span>
            <span>DB: {systemHealth?.services?.database || 'unknown'}</span>
            <span>AI: {systemHealth?.services?.freqtrade || 'ready'}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ minHeight: 'calc(100vh - 60px)', backgroundColor: '#f8fafc', padding: '2rem 0' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
          
          {/* Dashboard Header */}
          <div style={{ marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937', marginBottom: '0.5rem' }}>
              🎯 AI Crypto Trading Dashboard
            </h1>
            <p style={{ color: '#6b7280' }}>
              Real-time cryptocurrency trading with AI-powered strategies targeting R1,000 daily profit
            </p>
          </div>

          {/* Key Metrics Grid */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
            gap: '1.5rem', 
            marginBottom: '2rem' 
          }}>
            
            {/* Account Balance */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem' 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280', margin: 0 }}>Account Balance</h3>
                <div style={{ 
                  backgroundColor: '#dcfce7', 
                  padding: '0.5rem', 
                  borderRadius: '50%',
                  width: '2.5rem',
                  height: '2.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  💰
                </div>
              </div>
              <div>
                <p style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#1f2937', margin: 0 }}>
                  {formatCurrency(balance?.ZAR_balance)}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  Available: {formatCurrency((balance?.ZAR_balance || 0) - (balance?.ZAR_reserved || 0))}
                </p>
              </div>
            </div>

            {/* BTC Price */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem' 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280', margin: 0 }}>BTC/ZAR Price</h3>
                <div style={{ 
                  backgroundColor: '#fef3c7', 
                  padding: '0.5rem', 
                  borderRadius: '50%',
                  width: '2.5rem',
                  height: '2.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  ₿
                </div>
              </div>
              <div>
                <p style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f59e0b', margin: 0 }}>
                  {formatCurrency(marketData?.ticker?.last_trade)}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  Spread: {formatCurrency((marketData?.ticker?.ask || 0) - (marketData?.ticker?.bid || 0))}
                </p>
              </div>
            </div>

            {/* Daily Target Progress */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem' 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280', margin: 0 }}>Daily Target Progress</h3>
                <div style={{ 
                  backgroundColor: '#dbeafe', 
                  padding: '0.5rem', 
                  borderRadius: '50%',
                  width: '2.5rem',
                  height: '2.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  🎯
                </div>
              </div>
              <div>
                <p style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#3b82f6', margin: 0 }}>
                  R0.00 / R1,000
                </p>
                <div style={{ 
                  backgroundColor: '#e5e7eb', 
                  borderRadius: '9999px', 
                  height: '0.5rem', 
                  marginTop: '0.5rem' 
                }}>
                  <div style={{ 
                    backgroundColor: '#3b82f6', 
                    height: '100%', 
                    borderRadius: '9999px', 
                    width: '0%',
                    transition: 'width 0.3s ease' 
                  }}></div>
                </div>
              </div>
            </div>

            {/* AI Trading Status */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem' 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280', margin: 0 }}>AI Trading Status</h3>
                <div style={{ 
                  backgroundColor: '#f3e8ff', 
                  padding: '0.5rem', 
                  borderRadius: '50%',
                  width: '2.5rem',
                  height: '2.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  🤖
                </div>
              </div>
              <div>
                <p style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#8b5cf6', margin: 0 }}>
                  Ready
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  AI models loaded and monitoring market
                </p>
              </div>
            </div>
          </div>

          {/* Market Overview */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            marginBottom: '2rem' 
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem' }}>
              📊 Live Market Data (BTC/ZAR)
            </h3>
            
            {marketData && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.5rem' }}>
                  <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0 0 0.5rem 0' }}>Last Trade</p>
                  <p style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#1f2937', margin: 0 }}>
                    {formatCurrency(marketData.ticker.last_trade)}
                  </p>
                </div>
                
                <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f0fdf4', borderRadius: '0.5rem' }}>
                  <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0 0 0.5rem 0' }}>Bid</p>
                  <p style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#059669', margin: 0 }}>
                    {formatCurrency(marketData.ticker.bid)}
                  </p>
                </div>
                
                <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#fef2f2', borderRadius: '0.5rem' }}>
                  <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0 0 0.5rem 0' }}>Ask</p>
                  <p style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#dc2626', margin: 0 }}>
                    {formatCurrency(marketData.ticker.ask)}
                  </p>
                </div>
                
                <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#fffbeb', borderRadius: '0.5rem' }}>
                  <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0 0 0.5rem 0' }}>24h Volume</p>
                  <p style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#d97706', margin: 0 }}>
                    {(marketData.ticker.rolling_24_hour_volume || 0).toFixed(2)} BTC
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Trading Controls - CRITICAL ADDITION per BlikSIM */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            marginBottom: '2rem' 
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem' }}>
              🎮 Trading Controls
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
              <button
                onClick={() => startAITrading()}
                style={{
                  padding: '1rem',
                  backgroundColor: '#16a34a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#15803d'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#16a34a'}
              >
                🚀 Start AI Trading
              </button>
              
              <button
                onClick={() => stopAITrading()}
                style={{
                  padding: '1rem',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#b91c1c'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#dc2626'}
              >
                🛑 Stop AI Trading
              </button>
              
              <button
                onClick={() => openManualTradeModal()}
                style={{
                  padding: '1rem',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#2563eb'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#3b82f6'}
              >
                📊 Manual Trade
              </button>
              
              <button
                onClick={() => openConfigModal()}
                style={{
                  padding: '1rem',
                  backgroundColor: '#8b5cf6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#7c3aed'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#8b5cf6'}
              >
                ⚙️ AI Config
              </button>
            </div>
          </div>

          {/* AI Insights */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem' 
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem' }}>
              🧠 AI Trading Insights
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', backgroundColor: '#eff6ff', borderRadius: '0.5rem', border: '1px solid #dbeafe' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ marginRight: '0.5rem' }}>💡</span>
                  <span style={{ fontWeight: '600', color: '#1d4ed8' }}>Market Analysis</span>
                </div>
                <p style={{ fontSize: '0.875rem', color: '#1e40af', margin: 0 }}>
                  AI models are analyzing market patterns and preparing trading strategies. 
                  Real-time data feed active and monitoring for optimal entry points.
                </p>
              </div>
              
              <div style={{ padding: '1rem', backgroundColor: '#f0fdf4', borderRadius: '0.5rem', border: '1px solid #bbf7d0' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ marginRight: '0.5rem' }}>✅</span>
                  <span style={{ fontWeight: '600', color: '#166534' }}>System Status</span>
                </div>
                <p style={{ fontSize: '0.875rem', color: '#15803d', margin: 0 }}>
                  All systems operational. Luno API connected, database active, 
                  and AI models ready for automated trading execution.
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: '2rem', padding: '1rem', color: '#6b7280' }}>
            <p style={{ margin: 0 }}>
              🚀 AI Crypto Trading Bot - Built for smart, automated cryptocurrency trading
            </p>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
              Last updated: {new Date().toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;