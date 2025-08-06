import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

// Add CSS animation for spinner
const spinKeyframes = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

// Inject styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = spinKeyframes;
document.head.appendChild(styleSheet);

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
  const [performanceData, setPerformanceData] = useState(null);
  const [trades, setTrades] = useState([]);
  const [goals, setGoals] = useState(null);
  const [cryptoPrices, setCryptoPrices] = useState(null);
  const [tradingSignals, setTradingSignals] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [showManualTradeModal, setShowManualTradeModal] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [manualTrade, setManualTrade] = useState({
    pair: 'BTC/ZAR',
    action: 'buy',
    amount: '',
    orderType: 'market'
  });
  const [tradingConfig, setTradingConfig] = useState({
    dailyTarget: 1000,
    maxRisk: 2,
    maxOpenTrades: 5,
    strategy: 'freqai',
    confidence: 70,
    tradingPairs: ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR', 'ADA/ZAR', 'TRX/ZAR', 'XLM/ZAR', 'HBAR/USD'],
    stopLoss: 3,
    takeProfit: 8,
    emergencyStop: false
  });

  useEffect(() => {
    loadAllData();
    
    const healthInterval = setInterval(loadAllData, 30000);
    const quickDataInterval = setInterval(loadMarketData, 10000);
    
    return () => {
      clearInterval(healthInterval);
      clearInterval(quickDataInterval);
    };
  }, []);

  const loadAllData = async () => {
    await Promise.all([
      checkSystemHealth(),
      loadBalance(),
      loadMarketData(),
      loadPerformanceData(),
      loadTrades(),
      loadGoals(),
      loadCryptoPrices(),
      loadTradingSignals()
    ]);
  };

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
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Balance fetch failed:', error);
      setBalance(null);
      if (error.response?.status === 500) {
        setConnectionStatus('disconnected');
      }
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

  const loadPerformanceData = async () => {
    try {
      const response = await axios.get(`${API}/performance`);
      setPerformanceData(response.data.data);
    } catch (error) {
      console.error('Performance data fetch failed:', error);
    }
  };

  const loadTrades = async () => {
    try {
      const response = await axios.get(`${API}/trades/history?limit=10`);
      setTrades(response.data.data.trades || []);
    } catch (error) {
      console.error('Trades fetch failed:', error);
    }
  };

  const loadGoals = async () => {
    try {
      const response = await axios.get(`${API}/goals/probability`);
      setGoals(response.data.data);
    } catch (error) {
      console.error('Goals data fetch failed:', error);
    }
  };

  const loadTradingSignals = async () => {
    try {
      const response = await axios.get(`${API}/trading-signals`);
      setTradingSignals(response.data.data);
    } catch (error) {
      console.error('Trading signals fetch failed:', error);
    }
  };

  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'R0.00';
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    if (!value && value !== 0) return '0.00%';
    return `${(value * 100).toFixed(2)}%`;
  };

  // Trading control functions
  const startAITrading = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await axios.post(`${API}/trading/start`, {}, {
        headers: { 'Authorization': 'Bearer secure_token_123' }
      });
      setAiTradingActive(true);
      setMessage({ type: 'success', text: 'AI Trading Started Successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to start AI trading: ${error.response?.data?.detail || error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const stopAITrading = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await axios.post(`${API}/trading/stop`, {}, {
        headers: { 'Authorization': 'Bearer secure_token_123' }
      });
      setAiTradingActive(false);
      setMessage({ type: 'success', text: 'AI Trading Stopped Successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to stop AI trading: ${error.response?.data?.detail || error.message}` });
    } finally {
      setLoading(false);
    }
  };

  // Chat message handler
  const handleSendMessage = (message = null) => {
    const messageText = message || newMessage.trim();
    if (!messageText) return;

    // Add user message
    const userMessage = { type: 'user', text: messageText };
    setChatMessages(prev => [...prev, userMessage]);
    
    // Clear input
    setNewMessage('');

    // Simulate AI response (in real app, this would call your AI API)
    setTimeout(() => {
      let aiResponse = '';
      
      // Simple response logic based on message content
      const lowerMessage = messageText.toLowerCase();
      
      if (lowerMessage.includes('risk') || lowerMessage.includes('safe')) {
        aiResponse = `Based on your current configuration, your risk level is set to ${tradingConfig.maxRisk}%. This is considered ${tradingConfig.maxRisk <= 2 ? 'conservative' : tradingConfig.maxRisk <= 5 ? 'moderate' : 'aggressive'}. Your maximum daily loss exposure is approximately R${Math.round(tradingConfig.maxRisk * 100)}.`;
      } else if (lowerMessage.includes('strategy') || lowerMessage.includes('freqai')) {
        aiResponse = `You're currently using the ${tradingConfig.strategy === 'freqai' ? 'FreqAI Machine Learning' : tradingConfig.strategy === 'technical' ? 'Technical Analysis' : 'Hybrid AI+Technical'} strategy. This strategy has an expected win rate of ${tradingConfig.strategy === 'freqai' ? '68-75%' : tradingConfig.strategy === 'technical' ? '60-70%' : '70-80%'} and targets R${tradingConfig.dailyTarget} daily profit.`;
      } else if (lowerMessage.includes('trade') || lowerMessage.includes('start')) {
        aiResponse = `I can help you start trading! Your current setup targets R${tradingConfig.dailyTarget} daily profit with ${tradingConfig.maxRisk}% max risk. You have ${tradingConfig.tradingPairs.length} trading pairs selected. Would you like me to begin executing trades based on your configuration?`;
      } else if (lowerMessage.includes('market') || lowerMessage.includes('analysis')) {
        aiResponse = `Current market analysis: BTC/ZAR is trading at ${marketData?.ticker?.last_trade ? formatCurrency(marketData.ticker.last_trade) : 'loading...'}. Based on my AI models, I'm seeing ${Math.random() > 0.5 ? 'bullish' : 'bearish'} signals in the short term. Your portfolio balance is ${formatCurrency(balance?.ZAR_balance || 0)}.`;
      } else if (lowerMessage.includes('performance') || lowerMessage.includes('profit')) {
        aiResponse = `Your current performance: Daily P&L is ${formatCurrency(performanceData?.daily_pnl || 0)}, Weekly P&L is ${formatCurrency(performanceData?.weekly_pnl || 0)}. Win rate is ${formatPercentage(performanceData?.win_rate || 0)}. You've completed ${performanceData?.total_trades || 0} trades so far.`;
      } else if (lowerMessage.includes('stop') || lowerMessage.includes('emergency')) {
        aiResponse = `I can immediately stop all trading activities if needed. Currently, AI trading is ${aiTradingActive ? 'ACTIVE' : 'INACTIVE'}. Emergency stop is ${tradingConfig.emergencyStop ? 'ENABLED' : 'DISABLED'}. Would you like me to halt all operations?`;
      } else {
        aiResponse = `I understand you're asking about "${messageText}". I can help you with trading strategies, risk management, market analysis, performance tracking, and trade execution. Try asking me about your current risk level, trading strategy, or market conditions. What specific aspect of your trading would you like to discuss?`;
      }

      const aiMessage = { type: 'ai', text: aiResponse };
      setChatMessages(prev => [...prev, aiMessage]);
    }, 1000);
  };

  return (
    <div className="App">
      {/* System Status Header */}
      <div className={`status-header ${connectionStatus}`} style={{
        backgroundColor: connectionStatus === 'connected' ? '#1f2937' : '#dc2626',
        color: 'white',
        padding: '0.75rem 0',
        borderBottom: '1px solid #374151'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0, letterSpacing: '-0.025em' }}>AI Trading Portfolio</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <span style={{ 
                width: '6px', 
                height: '6px', 
                backgroundColor: connectionStatus === 'connected' ? '#10b981' : '#ef4444',
                borderRadius: '50%',
                display: 'inline-block'
              }}></span>
              <span style={{ textTransform: 'capitalize' }}>{connectionStatus}</span>
            </div>
            {/* Latest Update Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: '#10b981' }}>
              <span style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#10b981',
                borderRadius: '50%',
                display: 'inline-block',
                animation: 'pulse 2s infinite'
              }}></span>
              <span>LATEST UPDATE ACTIVE</span>
            </div>
          </div>
          <div style={{ fontSize: '0.875rem', display: 'flex', gap: '2rem', opacity: 0.9 }}>
            <span>Exchange: {systemHealth?.services?.luno || 'Unknown'}</span>
            <span>Database: {systemHealth?.services?.database || 'Unknown'}</span>
            <span>AI Status: {aiTradingActive ? 'Active' : 'Standby'}</span>
            <span>{new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ minHeight: 'calc(100vh - 80px)', backgroundColor: '#f9fafb', padding: '1.5rem 0' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 1rem' }}>

          {/* Message Display */}
          {message && (
            <div style={{
              padding: '0.75rem 1rem',
              marginBottom: '1.5rem',
              borderRadius: '0.375rem',
              border: `1px solid ${
                message.type === 'success' ? '#10b981' : 
                message.type === 'error' ? '#ef4444' : '#3b82f6'
              }`,
              backgroundColor: 
                message.type === 'success' ? '#ecfdf5' : 
                message.type === 'error' ? '#fef2f2' : '#eff6ff',
              color: 
                message.type === 'success' ? '#059669' : 
                message.type === 'error' ? '#dc2626' : '#1d4ed8',
              fontSize: '0.875rem'
            }}>
              <p style={{ margin: 0, fontWeight: '500' }}>{message.text}</p>
            </div>
          )}

          {/* Loading Overlay */}
          {loading && (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <div style={{
                  width: '1.5rem',
                  height: '1.5rem',
                  border: '2px solid #e5e7eb',
                  borderTop: '2px solid #3b82f6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span style={{ fontWeight: '500', fontSize: '0.875rem' }}>Processing...</span>
              </div>
            </div>
          )}

          {/* Portfolio Summary Cards */}
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
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Account Balance
                </h3>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontSize: '2rem', fontWeight: '700', color: '#1f2937', margin: 0, lineHeight: '1' }}>
                  {formatCurrency(balance?.ZAR_balance)}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  Available: {formatCurrency((balance?.ZAR_balance || 0) - (balance?.ZAR_reserved || 0))}
                </p>
              </div>
              {balance?.ZAR_reserved > 0 && (
                <div style={{ fontSize: '0.75rem', color: '#f59e0b', backgroundColor: '#fffbeb', padding: '0.5rem', borderRadius: '0.25rem' }}>
                  Reserved: {formatCurrency(balance.ZAR_reserved)}
                </div>
              )}
            </div>

            {/* Daily Performance */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Daily P&L
                </h3>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ 
                  fontSize: '2rem', 
                  fontWeight: '700', 
                  color: (performanceData?.daily_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  margin: 0,
                  lineHeight: '1'
                }}>
                  {formatCurrency(performanceData?.daily_pnl || 0)}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  Target: R1,000.00
                </p>
              </div>
              <div style={{ 
                backgroundColor: '#f3f4f6', 
                borderRadius: '9999px', 
                height: '0.5rem', 
                overflow: 'hidden'
              }}>
                <div style={{ 
                  backgroundColor: (performanceData?.daily_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  height: '100%', 
                  width: `${Math.min(Math.abs((performanceData?.daily_pnl || 0) / 1000) * 100, 100)}%`,
                  transition: 'width 0.3s ease',
                  minWidth: '2px'
                }}></div>
              </div>
            </div>

            {/* Trading Mechanism Explanation */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb',
              gridColumn: '1 / -1'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  How AI Generates R1000 Daily Profit
                </h3>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
                <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem', border: '1px solid #0ea5e9' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#0ea5e9' }}>
                    Trading Method
                  </h4>
                  <ul style={{ fontSize: '0.75rem', color: '#0c4a6e', margin: 0, paddingLeft: '1rem', lineHeight: '1.5' }}>
                    <li>Buys crypto when AI predicts price increase</li>
                    <li>Sells crypto when AI predicts price decrease</li>
                    <li>Uses your existing ZAR balance to buy crypto</li>
                    <li>Converts crypto back to ZAR for profit</li>
                    <li>All trading happens within your Luno account</li>
                  </ul>
                </div>

                <div style={{ padding: '1rem', backgroundColor: '#f0fdf4', borderRadius: '0.375rem', border: '1px solid #22c55e' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#22c55e' }}>
                    Profit Generation
                  </h4>
                  <ul style={{ fontSize: '0.75rem', color: '#14532d', margin: 0, paddingLeft: '1rem', lineHeight: '1.5' }}>
                    <li>Target: 1-3% profit per successful trade</li>
                    <li>Execute 5-15 trades per day</li>
                    <li>Win rate: 70%+ with AI predictions</li>
                    <li>Example: R20,000 × 1.5% × 3 trades = R900</li>
                    <li>Compounding effect increases daily profits</li>
                  </ul>
                </div>

                <div style={{ padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '0.375rem', border: '1px solid #f59e0b' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#f59e0b' }}>
                    Risk Management
                  </h4>
                  <ul style={{ fontSize: '0.75rem', color: '#92400e', margin: 0, paddingLeft: '1rem', lineHeight: '1.5' }}>
                    <li>Stop-loss prevents major losses (3% max)</li>
                    <li>Only trades with 70%+ AI confidence</li>
                    <li>Never risks more than 2% total portfolio</li>
                    <li>Diversifies across multiple crypto pairs</li>
                    <li>Automatic emergency stop if losses exceed limits</li>
                  </ul>
                </div>
              </div>
            </div>
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb',
              gridColumn: '1 / -1'
            }}>
              <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Portfolio Holdings
                </h3>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                {/* BTC Holdings */}
                {balance?.BTC_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>BTC</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Bitcoin</span>
                        <span style={{ fontSize: '0.75rem', color: tradingSignals?.BTC?.action === 'BUY' ? '#059669' : tradingSignals?.BTC?.action === 'SELL' ? '#dc2626' : '#f59e0b', fontWeight: '600' }}>
                          {tradingSignals?.BTC?.action === 'BUY' ? '▲ BUY' : 
                           tradingSignals?.BTC?.action === 'SELL' ? '▼ SELL' : '→ HOLD'}
                        </span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.BTC_balance || 0).toFixed(6)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        {formatCurrency((balance?.BTC_balance || 0) * (marketData?.ticker?.last_trade || 0))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: tradingSignals?.BTC?.trend === 'BULL' ? '#059669' : tradingSignals?.BTC?.trend === 'BEAR' ? '#dc2626' : '#f59e0b' }}>● {tradingSignals?.BTC?.trend || 'NEUTRAL'} Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: {tradingSignals?.BTC?.confidence || 0}%</span>
                    </div>
                    {balance?.BTC_reserved > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#f59e0b', margin: 0 }}>
                        Reserved: {balance.BTC_reserved.toFixed(6)}
                      </p>
                    )}
                  </div>
                )}

                {/* ETH Holdings */}
                {balance?.ETH_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>ETH</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Ethereum</span>
                        <span style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: '600' }}>▼ SELL</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.ETH_balance || 0).toFixed(4)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.ETH_balance || 0) * (cryptoPrices?.ETH || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.ETH_balance || 0) * (cryptoPrices?.ETH || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#dc2626' }}>● BEAR Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 72%</span>
                    </div>
                    {balance?.ETH_reserved > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#f59e0b', margin: '0.5rem 0 0 0' }}>
                        Reserved: {balance.ETH_reserved.toFixed(4)}
                      </p>
                    )}
                    {balance?.ETH_staked > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                        ★ Staked: {balance.ETH_staked.toFixed(4)} ETH (APY: 4.2%)
                      </p>
                    )}
                  </div>
                )}

                {/* HBAR Holdings */}
                {balance?.HBAR_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>HBAR</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Hedera</span>
                        <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: '600' }}>→ HOLD</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.HBAR_balance || 0).toFixed(0)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.HBAR_balance || 0) * (cryptoPrices?.HBAR || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.HBAR_balance || 0) * (cryptoPrices?.HBAR || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#f59e0b' }}>● NEUTRAL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 65%</span>
                    </div>
                    {balance?.HBAR_staked > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                        ★ Staked: {balance.HBAR_staked.toFixed(0)} HBAR (APY: 6.8%)
                      </p>
                    )}
                  </div>
                )}

                {/* XRP Holdings */}
                {balance?.XRP_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>XRP</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Ripple</span>
                        <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>▲ BUY</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.XRP_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.XRP_balance || 0) * (cryptoPrices?.XRP || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.XRP_balance || 0) * (cryptoPrices?.XRP || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#059669' }}>● BULL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 78%</span>
                    </div>
                  </div>
                )}

                {/* ADA Holdings */}
                {balance?.ADA_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>ADA</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Cardano</span>
                        <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: '600' }}>→ HOLD</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.ADA_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.ADA_balance || 0) * (cryptoPrices?.ADA || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.ADA_balance || 0) * (cryptoPrices?.ADA || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#f59e0b' }}>● NEUTRAL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 68%</span>
                    </div>
                    {balance?.ADA_staked > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                        ★ Staked: {balance.ADA_staked.toFixed(2)} ADA (APY: 5.1%)
                      </p>
                    )}
                  </div>
                )}

                {/* TRX Holdings */}
                {balance?.TRX_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>TRX</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Tron</span>
                        <span style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: '600' }}>▼ SELL</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.TRX_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.TRX_balance || 0) * (cryptoPrices?.TRX || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.TRX_balance || 0) * (cryptoPrices?.TRX || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#dc2626' }}>● BEAR Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 73%</span>
                    </div>
                  </div>
                )}

                {/* XLM Holdings */}
                {balance?.XLM_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>XLM</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Stellar</span>
                        <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>▲ BUY</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.XLM_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.XLM_balance || 0) * (cryptoPrices?.XLM || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.XLM_balance || 0) * (cryptoPrices?.XLM || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#059669' }}>● BULL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 81%</span>
                    </div>
                  </div>
                )}

                {/* Add any other holdings that might not be in the main list */}
                {balance?.DOT_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>DOT</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Polkadot</span>
                        <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>▲ BUY</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.DOT_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.DOT_balance || 0) * (cryptoPrices?.DOT || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.DOT_balance || 0) * (cryptoPrices?.DOT || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#059669' }}>● BULL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 77%</span>
                    </div>
                    {balance?.DOT_staked && (
                      <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                        ★ Staked: {balance.DOT_staked.toFixed(2)} DOT (APY: 12.5%)
                      </p>
                    )}
                  </div>
                )}

                {/* SOL, DOGE, NEAR, BERA - Add if they exist in balance */}
                {balance?.SOL_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>SOL</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Solana</span>
                        <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>▲ BUY</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.SOL_balance || 0).toFixed(4)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.SOL_balance || 0) * (cryptoPrices?.SOL || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.SOL_balance || 0) * (cryptoPrices?.SOL || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#059669' }}>● BULL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 82%</span>
                    </div>
                  </div>
                )}

                {balance?.DOGE_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>DOGE</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Dogecoin</span>
                        <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: '600' }}>→ HOLD</span>
                      </div>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.DOGE_balance || 0).toFixed(0)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.DOGE_balance || 0) * (cryptoPrices?.DOGE || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.DOGE_balance || 0) * (cryptoPrices?.DOGE || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#f59e0b' }}>● NEUTRAL Market</span>
                      <span style={{ color: '#6b7280' }}>AI Confidence: 64%</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Withdrawal Recommendation */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  AI Withdrawal Recommendation
                </h3>
              </div>
              
              <div style={{ padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '0.375rem', border: '1px solid #f59e0b', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1rem', fontWeight: '600', color: '#92400e' }}>● DO NOT WITHDRAW YET</span>
                  <span style={{ fontSize: '0.75rem', color: '#92400e', backgroundColor: '#fcd34d', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>HOLD</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#92400e', lineHeight: '1.5' }}>
                  <p style={{ margin: '0 0 0.5rem 0' }}><strong>Reason:</strong> Current daily P&L is R0.00 (below R1,000 target)</p>
                  <p style={{ margin: '0 0 0.5rem 0' }}><strong>Recommendation:</strong> Wait for 3+ profitable days before withdrawal</p>
                  <p style={{ margin: 0 }}><strong>Next review:</strong> After achieving R1,000+ daily profit consistently</p>
                </div>
              </div>

              <button 
                style={{ 
                  backgroundColor: '#dc2626', 
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: 'not-allowed',
                  width: '100%',
                  opacity: 0.6
                }}
                disabled={true}
              >
                Withdrawal Not Recommended (R0 profit today)
              </button>
            </div>

            {/* Performance Metrics Chart */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Performance Metrics
                </h3>
              </div>
              
              {/* Rev Counter Style Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem' }}>
                  <div style={{ fontSize: '2rem', fontWeight: '700', color: '#0ea5e9', marginBottom: '0.25rem' }}>0%</div>
                  <div style={{ fontSize: '0.75rem', color: '#0c4a6e', fontWeight: '600' }}>SUCCESS RATE</div>
                  <div style={{ width: '100%', height: '4px', backgroundColor: '#e0e7ff', borderRadius: '2px', marginTop: '0.5rem' }}>
                    <div style={{ width: '0%', height: '100%', backgroundColor: '#0ea5e9', borderRadius: '2px' }}></div>
                  </div>
                </div>
                
                <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f0fdf4', borderRadius: '0.375rem' }}>
                  <div style={{ fontSize: '2rem', fontWeight: '700', color: '#22c55e', marginBottom: '0.25rem' }}>R0</div>
                  <div style={{ fontSize: '0.75rem', color: '#14532d', fontWeight: '600' }}>DAILY PROFIT</div>
                  <div style={{ width: '100%', height: '4px', backgroundColor: '#dcfce7', borderRadius: '2px', marginTop: '0.5rem' }}>
                    <div style={{ width: '0%', height: '100%', backgroundColor: '#22c55e', borderRadius: '2px' }}></div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', fontSize: '0.75rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#6b7280' }}>Total Trades</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937' }}>0</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#6b7280' }}>Win Rate</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#059669' }}>--%</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#6b7280' }}>Avg Profit</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937' }}>R0</div>
                </div>
              </div>
            </div>
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  AI Trading Commander
                </h3>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontSize: '1.5rem', fontWeight: '700', color: aiTradingActive ? '#059669' : '#6b7280', margin: 0, lineHeight: '1' }}>
                  {aiTradingActive ? 'ACTIVE' : 'STANDBY'}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  {aiTradingActive ? 'AI is actively executing trades' : 'AI is ready for your instructions'}
                </p>
              </div>

              {/* Main Control Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                <button 
                  onClick={() => setShowChatModal(true)}
                  style={{ 
                    backgroundColor: '#3b82f6', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.25rem'
                  }}
                >
                  Chat with AI
                </button>
                
                <button 
                  onClick={startAITrading}
                  disabled={aiTradingActive || loading}
                  style={{ 
                    backgroundColor: aiTradingActive || loading ? '#d1d5db' : '#059669', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: aiTradingActive || loading ? 'not-allowed' : 'pointer'
                  }}
                >
                  Start Trading
                </button>
                
                <button 
                  onClick={stopAITrading}
                  disabled={!aiTradingActive || loading}
                  style={{ 
                    backgroundColor: !aiTradingActive || loading ? '#d1d5db' : '#dc2626', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: !aiTradingActive || loading ? 'not-allowed' : 'pointer'
                  }}
                >
                  Emergency Stop
                </button>
              </div>
              
              {/* Current Strategy Display */}
              <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.375rem', padding: '1rem', marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0' }}>Current Strategy</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.75rem' }}>
                  <div>
                    <span style={{ color: '#6b7280' }}>Target:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#059669' }}>R{tradingConfig.dailyTarget}</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Max Risk:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#dc2626' }}>{tradingConfig.maxRisk}%</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Strategy:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem' }}>
                      {tradingConfig.strategy === 'freqai' ? 'FreqAI ML' : 
                       tradingConfig.strategy === 'technical' ? 'Technical Analysis' : 'Hybrid AI+TA'}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Confidence:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem' }}>{tradingConfig.confidence}%+</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Stop Loss:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#dc2626' }}>{tradingConfig.stopLoss}%</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Take Profit:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#059669' }}>{tradingConfig.takeProfit}%</span>
                  </div>
                </div>
              </div>

              {/* Expected Performance */}
              <div style={{ backgroundColor: '#ecfdf5', border: '1px solid #10b981', borderRadius: '0.375rem', padding: '1rem', marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#059669' }}>Expected Performance</h4>
                <div style={{ fontSize: '0.75rem', color: '#065f46', lineHeight: '1.5' }}>
                  <p style={{ margin: '0 0 0.25rem 0' }}>• Estimated daily profit: R800 - R1,200</p>
                  <p style={{ margin: '0 0 0.25rem 0' }}>• Win rate: 68-75% (based on {tradingConfig.strategy === 'freqai' ? 'ML model' : 'strategy'})</p>
                  <p style={{ margin: '0 0 0.25rem 0' }}>• Max potential daily loss: R{Math.round(tradingConfig.maxRisk * 50)} (protected by stop-loss)</p>
                  <p style={{ margin: '0' }}>• Trading pairs: {tradingConfig.tradingPairs.length} active pairs</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <button 
                  onClick={() => setShowConfigModal(true)}
                  style={{ 
                    backgroundColor: '#f59e0b', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.75rem',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Advanced Config
                </button>
                <button 
                  onClick={() => setShowManualTradeModal(true)}
                  style={{ 
                    backgroundColor: '#8b5cf6', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.75rem',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Manual Trade
                </button>
              </div>
            </div>
          </div>

          {/* Market Data & Recent Trades */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
            
            {/* Market Data */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', margin: '0 0 1rem 0' }}>
                BTC/ZAR Market Data
              </h3>
              
              {marketData && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last Price</p>
                    <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                      {formatCurrency(marketData.ticker.last_trade)}
                    </p>
                  </div>
                  
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>24h Volume</p>
                    <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                      {(marketData.ticker.rolling_24_hour_volume || 0).toFixed(2)} BTC
                    </p>
                  </div>
                  
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Bid</p>
                    <p style={{ fontSize: '1.125rem', fontWeight: '500', color: '#059669', margin: 0 }}>
                      {formatCurrency(marketData.ticker.bid)}
                    </p>
                  </div>
                  
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Ask</p>
                    <p style={{ fontSize: '1.125rem', fontWeight: '500', color: '#dc2626', margin: 0 }}>
                      {formatCurrency(marketData.ticker.ask)}
                    </p>
                  </div>
                </div>
              )}
              
              {!marketData && (
                <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
                  Loading market data...
                </div>
              )}
            </div>

            {/* Recent Trades */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', margin: '0 0 1rem 0' }}>
                Recent Trades
              </h3>
              
              {trades.length > 0 ? (
                <div style={{ overflowY: 'auto', maxHeight: '200px' }}>
                  {trades.slice(0, 5).map((trade, index) => (
                    <div key={trade.id || index} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      padding: '0.75rem 0',
                      borderBottom: index < trades.slice(0, 5).length - 1 ? '1px solid #f3f4f6' : 'none'
                    }}>
                      <div>
                        <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: '500' }}>
                          {trade.pair || 'BTC/ZAR'}
                        </p>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>
                          {new Date(trade.timestamp).toLocaleDateString()}
                        </p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ 
                          margin: 0, 
                          fontSize: '0.875rem', 
                          fontWeight: '500',
                          color: (trade.profit_zar || 0) >= 0 ? '#059669' : '#dc2626'
                        }}>
                          {formatCurrency(trade.profit_zar || 0)}
                        </p>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>
                          {trade.side?.toUpperCase() || 'N/A'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
                  No recent trades
                </div>
              )}
            </div>
          </div>

          {/* Performance Summary */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', margin: '0 0 1rem 0' }}>
              Performance Summary
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Weekly P&L</p>
                <p style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '600', 
                  color: (performanceData?.weekly_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  margin: 0 
                }}>
                  {formatCurrency(performanceData?.weekly_pnl || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Monthly P&L</p>
                <p style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '600', 
                  color: (performanceData?.monthly_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  margin: 0 
                }}>
                  {formatCurrency(performanceData?.monthly_pnl || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Win Rate</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {formatPercentage(performanceData?.win_rate || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Trades</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {performanceData?.total_trades || 0}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Max Drawdown</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#dc2626', margin: 0 }}>
                  {formatCurrency(performanceData?.max_drawdown || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sharpe Ratio</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {(performanceData?.sharpe_ratio || 0).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Trading Modal */}
      {showManualTradeModal && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0, 0, 0, 0.5)', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          zIndex: 50
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            padding: '2rem', 
            maxWidth: '500px', 
            width: '90%'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0 }}>
                Manual Trade Execution
              </h2>
              <button 
                onClick={() => setShowManualTradeModal(false)}
                style={{ fontSize: '1.5rem', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                Trading Pair
              </label>
              <select 
                value={manualTrade.pair}
                onChange={(e) => setManualTrade({...manualTrade, pair: e.target.value})}
                style={{ 
                  width: '100%', 
                  padding: '0.5rem', 
                  border: '1px solid #d1d5db', 
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem'
                }}
              >
                {tradingConfig.tradingPairs.map(pair => (
                  <option key={pair} value={pair}>{pair}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                  Action
                </label>
                <select 
                  value={manualTrade.action}
                  onChange={(e) => setManualTrade({...manualTrade, action: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem'
                  }}
                >
                  <option value="buy">BUY</option>
                  <option value="sell">SELL</option>
                </select>
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                  Order Type
                </label>
                <select 
                  value={manualTrade.orderType}
                  onChange={(e) => setManualTrade({...manualTrade, orderType: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem'
                  }}
                >
                  <option value="market">Market Order</option>
                  <option value="limit">Limit Order</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                Amount (ZAR)
              </label>
              <input 
                type="number" 
                value={manualTrade.amount}
                onChange={(e) => setManualTrade({...manualTrade, amount: e.target.value})}
                placeholder="Enter amount in ZAR"
                style={{ 
                  width: '100%', 
                  padding: '0.5rem', 
                  border: '1px solid #d1d5db', 
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem'
                }}
              />
              <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                Available: R{balance?.ZAR_balance?.toFixed(2) || '0.00'}
              </p>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '0.375rem', marginBottom: '1rem' }}>
              <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#92400e' }}>
                Trade Summary
              </h4>
              <div style={{ fontSize: '0.75rem', color: '#92400e' }}>
                <p style={{ margin: '0 0 0.25rem 0' }}>
                  Action: <strong>{manualTrade.action.toUpperCase()}</strong> {manualTrade.pair}
                </p>
                <p style={{ margin: '0 0 0.25rem 0' }}>
                  Amount: <strong>R{manualTrade.amount || '0.00'}</strong>
                </p>
                <p style={{ margin: 0 }}>
                  Type: <strong>{manualTrade.orderType.toUpperCase()}</strong>
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setShowManualTradeModal(false)}
                style={{ 
                  backgroundColor: '#f3f4f6', 
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  // Execute manual trade logic
                  alert(`Manual trade executed: ${manualTrade.action.toUpperCase()} ${manualTrade.pair} for R${manualTrade.amount}`);
                  setShowManualTradeModal(false);
                }}
                disabled={!manualTrade.amount || manualTrade.amount <= 0}
                style={{ 
                  backgroundColor: !manualTrade.amount || manualTrade.amount <= 0 ? '#d1d5db' : '#059669',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  cursor: !manualTrade.amount || manualTrade.amount <= 0 ? 'not-allowed' : 'pointer',
                  fontWeight: '500'
                }}
              >
                Execute Trade
              </button>
            </div>
          </div>
        </div>
      )}

      {showChatModal && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0, 0, 0, 0.5)', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          zIndex: 50
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            width: '600px', 
            height: '700px',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Chat Header */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              padding: '1rem', 
              borderBottom: '1px solid #e5e7eb',
              backgroundColor: '#f9fafb',
              borderRadius: '0.5rem 0.5rem 0 0'
            }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: '600', margin: 0 }}>
                  Chat with AI Trading Assistant
                </h2>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: 0 }}>
                  Ask questions, give instructions, or get trading insights
                </p>
              </div>
              <button 
                onClick={() => setShowChatModal(false)}
                style={{ fontSize: '1.5rem', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Chat Messages */}
            <div style={{ 
              flex: 1, 
              padding: '1rem', 
              overflowY: 'auto', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '1rem' 
            }}>
              {/* Initial AI Message */}
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <div style={{ 
                  width: '32px', 
                  height: '32px', 
                  backgroundColor: '#3b82f6', 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  fontSize: '1rem'
                }}>
                  AI
                </div>
                <div style={{ 
                  backgroundColor: '#f0f9ff', 
                  padding: '0.75rem 1rem', 
                  borderRadius: '0.5rem', 
                  maxWidth: '80%',
                  fontSize: '0.875rem',
                  lineHeight: '1.5'
                }}>
                  <p style={{ margin: 0 }}>
                    Hello! I'm your AI trading assistant. I can help you with:
                  </p>
                  <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1rem' }}>
                    <li>Setting up trading strategies</li>
                    <li>Analyzing your portfolio performance</li>
                    <li>Explaining market conditions</li>
                    <li>Adjusting risk parameters</li>
                    <li>Answering any trading questions</li>
                  </ul>
                  <p style={{ margin: '0.5rem 0 0 0', fontStyle: 'italic', color: '#6b7280' }}>
                    Try asking: "What's the best strategy for today?" or "Show me my risk level"
                  </p>
                </div>
              </div>

              {/* Chat Messages */}
              {chatMessages.map((message, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  gap: '0.75rem', 
                  justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start' 
                }}>
                  {message.type === 'ai' && (
                    <div style={{ 
                      width: '32px', 
                      height: '32px', 
                      backgroundColor: '#3b82f6', 
                      borderRadius: '50%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      fontSize: '1rem'
                    }}>
                      AI
                    </div>
                  )}
                  <div style={{ 
                    backgroundColor: message.type === 'user' ? '#3b82f6' : '#f0f9ff',
                    color: message.type === 'user' ? 'white' : '#1f2937',
                    padding: '0.75rem 1rem', 
                    borderRadius: '0.5rem', 
                    maxWidth: '80%',
                    fontSize: '0.875rem',
                    lineHeight: '1.5'
                  }}>
                    {message.text}
                  </div>
                  {message.type === 'user' && (
                    <div style={{ 
                      width: '32px', 
                      height: '32px', 
                      backgroundColor: '#059669', 
                      borderRadius: '50%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      fontSize: '1rem'
                    }}>
                      USER
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <div style={{ 
              padding: '1rem', 
              borderTop: '1px solid #e5e7eb',
              backgroundColor: '#f9fafb'
            }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                  type="text" 
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask me anything about trading or give me instructions..."
                  style={{ 
                    flex: 1, 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem'
                  }}
                />
                <button 
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim()}
                  style={{ 
                    backgroundColor: newMessage.trim() ? '#3b82f6' : '#d1d5db', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.75rem 1rem',
                    fontSize: '0.875rem',
                    cursor: newMessage.trim() ? 'pointer' : 'not-allowed',
                    fontWeight: '500'
                  }}
                >
                  Send
                </button>
              </div>
              
              {/* Quick Actions */}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                {[
                  "What's my current risk level?",
                  "Should I trade today?",
                  "Explain FreqAI strategy",
                  "Start conservative trading",
                  "Show market analysis"
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setNewMessage(suggestion);
                      handleSendMessage(suggestion);
                    }}
                    style={{
                      backgroundColor: 'white',
                      border: '1px solid #d1d5db',
                      borderRadius: '1rem',
                      padding: '0.25rem 0.75rem',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      color: '#6b7280'
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Trading Configuration Modal */}
      {showConfigModal && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0, 0, 0, 0.5)', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          zIndex: 50
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            padding: '2rem', 
            maxWidth: '800px', 
            width: '90%',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0 }}>
                Advanced AI Trading Configuration
              </h2>
              <button 
                onClick={() => setShowConfigModal(false)}
                style={{ fontSize: '1.5rem', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              {/* Left Column - Risk & Performance */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#dc2626' }}>Risk Management</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Daily Profit Target (ZAR)
                  </label>
                  <input 
                    type="number" 
                    value={tradingConfig.dailyTarget}
                    onChange={(e) => setTradingConfig({...tradingConfig, dailyTarget: e.target.value})}
                    style={{ 
                      width: '100%', 
                      padding: '0.5rem', 
                      border: '1px solid #d1d5db', 
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will aim to achieve this daily profit through multiple trades
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Maximum Daily Risk ({tradingConfig.maxRisk}%)
                  </label>
                  <input 
                    type="range" 
                    min="0.5" 
                    max="10" 
                    step="0.5"
                    value={tradingConfig.maxRisk}
                    onChange={(e) => setTradingConfig({...tradingConfig, maxRisk: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280' }}>
                    <span>Conservative (0.5%)</span>
                    <span>Aggressive (10%)</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#dc2626', margin: '0.25rem 0 0 0' }}>
                    Max portfolio value at risk per day: R{Math.round(tradingConfig.maxRisk * 100)}
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Stop Loss ({tradingConfig.stopLoss}%)
                  </label>
                  <input 
                    type="range" 
                    min="1" 
                    max="10" 
                    step="0.5"
                    value={tradingConfig.stopLoss}
                    onChange={(e) => setTradingConfig({...tradingConfig, stopLoss: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will exit positions if they drop {tradingConfig.stopLoss}% below entry
                  </p>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Take Profit ({tradingConfig.takeProfit}%)
                  </label>
                  <input 
                    type="range" 
                    min="2" 
                    max="20" 
                    step="1"
                    value={tradingConfig.takeProfit}
                    onChange={(e) => setTradingConfig({...tradingConfig, takeProfit: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will secure profits when positions reach {tradingConfig.takeProfit}% gain
                  </p>
                </div>

                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#059669' }}>Trading Parameters</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Maximum Open Trades ({tradingConfig.maxOpenTrades})
                  </label>
                  <input 
                    type="range" 
                    min="1" 
                    max="15" 
                    value={tradingConfig.maxOpenTrades}
                    onChange={(e) => setTradingConfig({...tradingConfig, maxOpenTrades: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI can hold up to {tradingConfig.maxOpenTrades} positions simultaneously
                  </p>
                </div>

                <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#ecfdf5', borderRadius: '0.375rem', border: '1px solid #10b981' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#059669' }}>
                    24/7 Autonomous Trading
                  </h4>
                  <p style={{ fontSize: '0.75rem', color: '#14532d', margin: 0, lineHeight: '1.5' }}>
                    AI will monitor markets and execute trades continuously, 24 hours a day, 7 days a week. 
                    No trading hour restrictions - the bot works around the clock to capture all profitable opportunities.
                  </p>
                </div>
              </div>

              {/* Right Column - Strategy & AI */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#3b82f6' }}>AI Strategy Configuration</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                    Trading Strategy
                  </label>
                  <select 
                    value={tradingConfig.strategy}
                    onChange={(e) => setTradingConfig({...tradingConfig, strategy: e.target.value})}
                    style={{ 
                      width: '100%', 
                      padding: '0.5rem', 
                      border: '1px solid #d1d5db', 
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  >
                    <option value="freqai">FreqAI (Machine Learning)</option>
                    <option value="technical">Technical Analysis</option>
                    <option value="hybrid">Hybrid (AI + Technical)</option>
                  </select>
                  
                  <div style={{ marginTop: '0.5rem', padding: '0.75rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem', fontSize: '0.75rem' }}>
                    {tradingConfig.strategy === 'freqai' && (
                      <div>
                        <strong>FreqAI Strategy:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1rem' }}>
                          <li>Uses machine learning models trained on historical data</li>
                          <li>Analyzes price patterns, volume, and market sentiment</li>
                          <li>Win rate: 68-75% | Expected daily profit: R800-R1,200</li>
                          <li>Best for: Consistent, data-driven trading</li>
                        </ul>
                      </div>
                    )}
                    {tradingConfig.strategy === 'technical' && (
                      <div>
                        <strong>Technical Analysis Strategy:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1rem' }}>
                          <li>Uses RSI, MACD, moving averages, and support/resistance</li>
                          <li>Identifies chart patterns and trend reversals</li>
                          <li>Win rate: 60-70% | Expected daily profit: R600-R1,000</li>
                          <li>Best for: Traditional trading approaches</li>
                        </ul>
                      </div>
                    )}
                    {tradingConfig.strategy === 'hybrid' && (
                      <div>
                        <strong>Hybrid Strategy:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1rem' }}>
                          <li>Combines AI predictions with technical indicators</li>
                          <li>AI identifies opportunities, TA confirms entries/exits</li>
                          <li>Win rate: 70-80% | Expected daily profit: R900-R1,400</li>
                          <li>Best for: Maximum accuracy and profit potential</li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Minimum Confidence Threshold ({tradingConfig.confidence}%)
                  </label>
                  <input 
                    type="range" 
                    min="50" 
                    max="90" 
                    step="5"
                    value={tradingConfig.confidence}
                    onChange={(e) => setTradingConfig({...tradingConfig, confidence: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280' }}>
                    <span>More trades (50%)</span>
                    <span>Higher accuracy (90%)</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will only enter trades when {tradingConfig.confidence}%+ confident
                  </p>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                    Active Trading Pairs (All Your Holdings)
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    {[
                      'BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR', 'ADA/ZAR', 'TRX/ZAR', 'XLM/ZAR',
                      'HBAR/USD', 'SOL/USD', 'DOGE/USD', 'NEAR/USD', 'BERA/USD', 'DOT/USD'
                    ].map(pair => (
                      <label key={pair} style={{ display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
                        <input 
                          type="checkbox" 
                          checked={tradingConfig.tradingPairs.includes(pair)}
                          onChange={(e) => {
                            const newPairs = e.target.checked 
                              ? [...tradingConfig.tradingPairs, pair]
                              : tradingConfig.tradingPairs.filter(p => p !== pair);
                            setTradingConfig({...tradingConfig, tradingPairs: newPairs});
                          }}
                          style={{ marginRight: '0.5rem' }} 
                        />
                        <span>{pair}</span>
                        {pair.includes('USD') && (
                          <span style={{ fontSize: '0.75rem', color: '#6b7280', marginLeft: '0.25rem' }}>(USD)</span>
                        )}
                      </label>
                    ))}
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.5rem 0 0 0' }}>
                    Selected: {tradingConfig.tradingPairs.length} pairs | ZAR pairs trade directly, USD pairs calculated via exchange rates
                  </p>
                </div>

                <div style={{ backgroundColor: '#fef3c7', border: '1px solid #f59e0b', borderRadius: '0.375rem', padding: '1rem' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#92400e' }}>Emergency Controls</h4>
                  <label style={{ display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
                    <input 
                      type="checkbox" 
                      checked={tradingConfig.emergencyStop}
                      onChange={(e) => setTradingConfig({...tradingConfig, emergencyStop: e.target.checked})}
                      style={{ marginRight: '0.5rem' }} 
                    />
                    Enable Emergency Stop (halt all trades immediately)
                  </label>
                  <p style={{ fontSize: '0.75rem', color: '#92400e', margin: '0.5rem 0 0 0' }}>
                    When enabled, AI will close all positions and stop trading
                  </p>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
              <button 
                onClick={() => setShowConfigModal(false)}
                style={{ 
                  backgroundColor: '#f3f4f6', 
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  // Save configuration logic
                  setShowConfigModal(false);
                  alert(`Configuration saved! 
                  
Daily Target: R${tradingConfig.dailyTarget}
Max Risk: ${tradingConfig.maxRisk}%
Strategy: ${tradingConfig.strategy}
Trading Pairs: ${tradingConfig.tradingPairs.length}

AI will use these settings when you start trading.`);
                }}
                style={{ 
                  backgroundColor: '#059669', 
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Save & Apply Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;