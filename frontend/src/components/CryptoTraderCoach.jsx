import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { TrendingUp, TrendingDown, Target, AlertTriangle, MessageCircle, DollarSign, BarChart3, Shield, RefreshCw, Activity, PieChart, TrendingUpIcon, Zap, Play, Pause, Plus, Settings, TestTube } from 'lucide-react';
import axios from 'axios';
import BacktestingDashboard from './BacktestingDashboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CryptoTraderCoach = () => {
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [marketData, setMarketData] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [dailyStrategy, setDailyStrategy] = useState(null);
  const [weeklyTargets, setWeeklyTargets] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [sessionId, setSessionId] = useState(() => {
    // Try to get existing session ID from localStorage
    let existingSessionId = localStorage.getItem('ai_trading_coach_session_id');
    if (!existingSessionId) {
      // Create new session ID if none exists
      existingSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('ai_trading_coach_session_id', existingSessionId);
    }
    return existingSessionId;
  });
  const [activeTab, setActiveTab] = useState('overview');
  const [lastRefresh, setLastRefresh] = useState(Date.now());
  const [monthlyTargetState, setMonthlyTargetState] = useState(null);
  const [weeklyTargetState, setWeeklyTargetState] = useState(null);
  const [targetSettings, setTargetSettings] = useState(null);
  const [autoTradeSettings, setAutoTradeSettings] = useState(null);
  const [showAutoTradeModal, setShowAutoTradeModal] = useState(false);
  const [technicalAnalysis, setTechnicalAnalysis] = useState(null);
  const [selectedTechnicalSymbol, setSelectedTechnicalSymbol] = useState('BTC');
  const [technicalIndicators, setTechnicalIndicators] = useState(null);
  const [marketOverview, setMarketOverview] = useState(null);
  const [dataLoadingComplete, setDataLoadingComplete] = useState(false);
  const [activeCampaigns, setActiveCampaigns] = useState([]);
  const [campaignProgress, setCampaignProgress] = useState(null);
  const [showCreateCampaignModal, setShowCreateCampaignModal] = useState(false);
  const [newCampaignData, setNewCampaignData] = useState({
    allocated_capital: 10000,
    profit_target: 10000,
    timeframe_days: 7,
    risk_level: 'aggressive'
  });
  const [showTargetAdjustmentModal, setShowTargetAdjustmentModal] = useState(false);
  const [newTargetData, setNewTargetData] = useState({
    monthly_target: 100000,
    weekly_target: 25000
  });
  const chatScrollRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load technical analysis when selected symbol changes
  useEffect(() => {
    if (selectedTechnicalSymbol) {
      loadTechnicalAnalysis();
      loadTechnicalIndicators(selectedTechnicalSymbol);
    }
  }, [selectedTechnicalSymbol]);

  // Debug effect to log portfolio changes
  useEffect(() => {
    console.log('Portfolio state changed:', portfolio);
    if (portfolio) {
      console.log('Portfolio total value:', portfolio.total_value);
    }
  }, [portfolio]);

  // Debug effect to log market data changes
  useEffect(() => {
    console.log('Market data state changed:', marketData);
    console.log('Market data length:', marketData.length);
  }, [marketData]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setDataLoadingComplete(false);
      
      // Load data sequentially instead of parallel to avoid race conditions
      console.log('Starting initial data load...');
      
      // Load market data first
      await loadMarketData();
      
      // Load portfolio data second
      await loadPortfolio();
      
      // Load other data
      await loadDailyStrategy();
      await loadWeeklyTargets();
      await loadRiskMetrics();
      await loadChatHistory();
      await loadTargetSettings();
      await loadAutoTradeSettings();
      await loadTechnicalAnalysis();
      await loadMarketOverview();
      
      console.log('Initial data load completed');
      setDataLoadingComplete(true);
    } catch (error) {
      console.error('Error loading initial data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMarketData = async () => {
    try {
      console.log('Loading market data...');
      console.log('API URL:', `${API}/market/data`);
      
      const response = await axios.get(`${API}/market/data`, { timeout: 10000 });
      console.log('Market data response status:', response.status);
      console.log('Market data response data:', response.data);
      setMarketData(response.data);
      console.log('Market data state updated successfully');
    } catch (error) {
      console.error('Error loading market data:', error);
      console.error('Error details:', error.response?.data, error.response?.status);
      console.error('Error message:', error.message);
    }
  };

  const loadPortfolio = async () => {
    try {
      console.log('Loading portfolio data...');
      console.log('API URL:', `${API}/portfolio`);
      
      const response = await axios.get(`${API}/portfolio`, { timeout: 10000 });
      console.log('Portfolio response status:', response.status);
      console.log('Portfolio response data:', response.data);
      
      if (response.data && response.data.total_value) {
        console.log('Setting portfolio state with value:', response.data.total_value);
        setPortfolio(response.data);
        console.log('Portfolio state set successfully');
      } else {
        console.error('Invalid portfolio data received:', response.data);
      }
    } catch (error) {
      console.error('Error loading portfolio:', error);
      console.error('Error details:', error.response?.data, error.response?.status);
      console.error('Error message:', error.message);
    }
  };

  const loadDailyStrategy = async () => {
    try {
      const response = await axios.get(`${API}/strategy/daily`);
      setDailyStrategy(response.data);
    } catch (error) {
      console.error('Error loading daily strategy:', error);
    }
  };

  const loadWeeklyTargets = async () => {
    try {
      const response = await axios.get(`${API}/targets/weekly`);
      setWeeklyTargets(response.data);
    } catch (error) {
      console.error('Error loading weekly targets:', error);
    }
  };

  const loadRiskMetrics = async () => {
    try {
      const response = await axios.get(`${API}/risk/metrics`);
      setRiskMetrics(response.data);
    } catch (error) {
      console.error('Error loading risk metrics:', error);
    }
  };

  const loadAutoTradeSettings = async () => {
    try {
      const response = await axios.get(`${API}/autotrade/settings`);
      setAutoTradeSettings(response.data);
    } catch (error) {
      console.error('Error loading auto trade settings:', error);
    }
  };

  const loadTargetSettings = async () => {
    try {
      const response = await axios.get(`${API}/targets/settings`);
      setTargetSettings(response.data);
      setMonthlyTargetState(response.data.monthly_target);
      setWeeklyTargetState(response.data.weekly_target);
    } catch (error) {
      console.error('Error loading target settings:', error);
    }
  };

  const loadChatHistory = async () => {
    try {
      console.log('Loading chat history for session:', sessionId);
      const response = await axios.get(`${API}/chat/history/${sessionId}`);
      console.log('Chat history response:', response.data);
      
      if (response.data && response.data.length > 0) {
        setChatMessages(response.data);
        console.log('Chat history loaded:', response.data.length, 'messages');
      } else {
        // Start with a clean welcome message if no history
        const welcomeTimestamp = new Date();
        const welcomeMessage = [{
          id: 1,
          role: 'assistant',
          message: 'Hello! I\'m your AI Trading Coach. I\'m ready to help with market analysis, trading strategies, and portfolio guidance. What can I assist you with today?',
          timestamp: welcomeTimestamp.toISOString()
        }];
        setChatMessages(welcomeMessage);
        console.log('No chat history found, starting with welcome message');
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Start with a clean welcome message if error loading history
      const errorTimestamp = new Date();
      const welcomeMessage = [{
        id: 1,
        role: 'assistant',
        message: 'Hello! I\'m your AI Trading Coach. I\'m ready to help with market analysis, trading strategies, and portfolio guidance. What can I assist you with today?',
        timestamp: errorTimestamp.toISOString()
      }];
      setChatMessages(welcomeMessage);
      console.log('Error loading chat history, starting with welcome message');
    }
  };

  const loadTechnicalAnalysis = async () => {
    try {
      const response = await axios.get(`${API}/technical/signals/${selectedTechnicalSymbol}`);
      setTechnicalAnalysis(response.data);
    } catch (error) {
      console.error('Error loading technical analysis:', error);
    }
  };

  const loadTechnicalIndicators = async (symbol) => {
    try {
      const response = await axios.get(`${API}/technical/indicators/${symbol}`);
      setTechnicalIndicators(response.data);
    } catch (error) {
      console.error('Error loading technical indicators:', error);
    }
  };

  const loadMarketOverview = async () => {
    try {
      const response = await axios.get(`${API}/technical/market-overview`);
      setMarketOverview(response.data);
    } catch (error) {
      console.error('Error loading market overview:', error);
    }
  };

  const createTradingCampaign = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/campaigns/create`, newCampaignData);
      
      if (response.data.success) {
        setActiveCampaigns(prev => [...prev, response.data.campaign]);
        setShowCreateCampaignModal(false);
        
        // Add AI message about campaign creation
        const campaignTimestamp = new Date();
        setChatMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          message: `🎯 TRADING CAMPAIGN CREATED!\n\n${response.data.campaign.name}\n\nAllocated Capital: R${newCampaignData.allocated_capital.toLocaleString()}\nProfit Target: R${newCampaignData.profit_target.toLocaleString()}\nTimeframe: ${newCampaignData.timeframe_days} days\n\n${response.data.risk_warning}\n\nI'm now monitoring the markets for high-probability opportunities. Let's make this work!`,
          timestamp: campaignTimestamp.toISOString()
        }]);
        
        // Reset form
        setNewCampaignData({
          allocated_capital: 10000,
          profit_target: 10000,
          timeframe_days: 7,
          risk_level: 'aggressive'
        });
      }
    } catch (error) {
      console.error('Error creating campaign:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const executeCampaignTrades = async (campaignId) => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/campaigns/${campaignId}/execute`);
      
      if (response.data.success && response.data.trades_executed > 0) {
        // Add campaign execution message
        const executionTimestamp = new Date();
        setChatMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          message: `⚡ TRADES EXECUTED!\n\nCampaign: ${campaignId}\nTrades: ${response.data.trades_executed}\n\nJust executed ${response.data.trades_executed} high-confidence trades based on current market analysis. Monitoring positions for optimal exits.`,
          timestamp: executionTimestamp.toISOString()
        }]);
      }
    } catch (error) {
      console.error('Error executing campaign trades:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateTargetsManually = async () => {
    try {
      setIsLoading(true);
      
      // Update target settings in backend
      const response = await axios.post(`${API}/targets/settings`, {
        monthly_target: newTargetData.monthly_target,
        weekly_target: newTargetData.weekly_target,
        user_id: "default_user",
        manually_adjusted: true
      });
      
      if (response.data.success) {
        // Update local state immediately for dashboard refresh
        setMonthlyTargetState(newTargetData.monthly_target);
        setWeeklyTargetState(newTargetData.weekly_target);
        setShowTargetAdjustmentModal(false);
        
        // Force reload all data to update dashboard progress bars and calculations
        await loadTargetSettings();
        await loadInitialData();
        
        // Add AI message about manual target update
        const targetUpdateTimestamp = new Date();
        setChatMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          message: `🎯 TARGETS UPDATED MANUALLY!\n\nNew Monthly Target: ${formatCurrency(newTargetData.monthly_target)}\nNew Weekly Target: ${formatCurrency(newTargetData.weekly_target)}\n\nPerfect! I've updated the dashboard with your new targets. All progress bars and calculations now reflect your new goals. Let's crush these targets together!`,
          timestamp: targetUpdateTimestamp.toISOString()
        }]);
      }
    } catch (error) {
      console.error('Error updating targets manually:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    console.log('Sending message:', inputMessage, 'for session:', sessionId);
    
    // Create single Date object as source of truth
    const messageTimestamp = new Date();
    
    // Use for backend transmission (UTC)
    const timestampForBackend = messageTimestamp.toISOString();
    
    // Use for immediate display (local timezone) 
    const timestampForDisplay = messageTimestamp.toLocaleString(undefined, { 
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      message: inputMessage,
      timestamp: timestampForBackend // Store UTC for consistency with backend
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      // Include current portfolio and market data as context
      const context = {
        portfolio: portfolio,
        market_data: marketData,
        target_settings: targetSettings,
        technical_analysis: technicalAnalysis,
        market_overview: marketOverview
      };
      
      console.log('Sending context with message:', context);
      
      const response = await axios.post(`${API}/chat/send`, {
        session_id: sessionId,
        role: 'user',
        message: inputMessage,
        context: context
      });
      
      console.log('AI response received:', response.data);
      setChatMessages(prev => [...prev, response.data]);
      
      // Check if AI suggests a trade
      if (response.data.message.includes('BUY') || response.data.message.includes('SELL')) {
        const tradeTimestamp = new Date();
        setChatMessages(prev => [...prev, {
          id: Date.now() + 2,
          role: 'assistant',
          message: `Ready to Execute Trade?\n\nI can help you execute this trade on Luno. Just confirm and I will place the order for you.\n\nNote: This will be a real trade on your Luno account. Always double-check before confirming.`,
          timestamp: tradeTimestamp.toISOString()
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      const errorTimestamp = new Date();
      setChatMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        message: 'Connection error. Please try again.',
        timestamp: errorTimestamp.toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLastRefresh(Date.now());
    await loadInitialData();
  };

  const handleNewSession = async () => {
    try {
      setIsLoading(true);
      
      // Fork session: Summarize and clear for fresh start while maintaining context
      const response = await axios.delete(`${API}/chat/history/${sessionId}`);
      
      if (response.data.summary_created) {
        console.log('Session forked with summary:', response.data.summary?.summary);
      }
      
      // Create new session ID
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Update localStorage and React state
      localStorage.setItem('ai_trading_coach_session_id', newSessionId);
      setSessionId(newSessionId);
      
      // Clear frontend chat messages with context-aware welcome
      const newSessionTimestamp = new Date();
      setChatMessages([{
        id: 1,
        role: 'assistant',
        message: 'Hello! Starting a fresh conversation. I have context from our previous discussions and I\'m ready to help with your trading strategy. What would you like to focus on today?',
        timestamp: newSessionTimestamp.toISOString()
      }]);
      
      console.log('Session forked successfully:', newSessionId);
      
    } catch (error) {
      console.error('Error forking session:', error);
      // Fallback to simple refresh if forking fails
      const newSessionTimestamp = new Date();
      setChatMessages([{
        id: 1,
        role: 'assistant', 
        message: 'Hello! I\'m your AI Trading Coach. I\'m ready to help with market analysis, trading strategies, and portfolio guidance. What can I assist you with today?',
        timestamp: newSessionTimestamp.toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-ZA', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(num);
  };

  const currentMonthProgress = useMemo(() => {
    const value = portfolio?.total_value || 0;
    console.log('useMemo currentMonthProgress recalculated:', value, 'from portfolio:', portfolio);
    return value;
  }, [portfolio]);
  
  // Debug logging
  console.log('Portfolio state:', portfolio);
  console.log('Portfolio total_value:', portfolio?.total_value);
  console.log('currentMonthProgress:', currentMonthProgress);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/20 via-transparent to-transparent"></div>
      
      <div className="relative z-10 container mx-auto p-4 lg:p-6">
        {/* Header */}
        <div className="mb-6 lg:mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-gradient-to-r from-transparent via-cyan-700/50 to-transparent pb-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-cyan-500 to-cyan-700 rounded-xl shadow-lg">
                <Activity className="w-8 h-8 text-black" />
              </div>
              <div>
                <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-cyan-500 bg-clip-text text-transparent">
                  AI Trading Coach
                </h1>
                <p className="text-cyan-600/80 text-sm lg:text-base font-medium">
                  Professional Cryptocurrency Trading Analysis
                </p>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <Button
                onClick={handleNewSession}
                className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold border border-green-500/50 shadow-lg shadow-green-500/25 transition-all duration-300"
              >
                <Plus className="w-4 h-4 mr-2" />
                Fork Session
              </Button>
              <Button
                onClick={handleRefresh}
                className="bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-700 hover:to-cyan-800 text-black font-semibold border border-cyan-500/50 shadow-lg shadow-cyan-500/25 transition-all duration-300"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Data
              </Button>
              <Button
                onClick={() => {
                  setNewTargetData({
                    monthly_target: monthlyTargetState || 100000,
                    weekly_target: weeklyTargetState || 25000
                  });
                  setShowTargetAdjustmentModal(true);
                }}
                className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold border border-purple-500/50 shadow-lg shadow-purple-500/25 transition-all duration-300"
              >
                <Settings className="w-4 h-4 mr-2" />
                Adjust Targets
              </Button>
              <Button
                onClick={() => setShowAutoTradeModal(true)}
                className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold border border-blue-500/50 shadow-lg shadow-blue-500/25 transition-all duration-300"
              >
                <Activity className="w-4 h-4 mr-2" />
                Auto Trade: {autoTradeSettings?.enabled ? 'ON' : 'OFF'}
              </Button>
              <div className="text-center lg:text-right bg-gradient-to-r from-gray-800 to-gray-900 p-4 rounded-xl border border-cyan-600/30 shadow-lg">
                <div className="text-2xl lg:text-3xl font-bold font-mono bg-gradient-to-r from-green-400 to-green-500 bg-clip-text text-transparent">
                  {formatCurrency(currentMonthProgress)}
                </div>
                <div className="text-xs lg:text-sm text-cyan-400/80 font-medium">
                  Real-Time Portfolio Value
                </div>
                <div className="text-xs text-green-400 mt-1">
                  ● Live Data • Trading Enabled
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
          
          {/* Chat Interface */}
          <div className="lg:col-span-1 order-2 lg:order-1">
            <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-cyan-600/40 shadow-2xl shadow-cyan-500/10 h-[500px] lg:h-[650px] flex flex-col">
              <CardHeader className="pb-3 border-b border-cyan-600/30 bg-gradient-to-r from-cyan-900/20 to-cyan-800/20">
                <CardTitle className="text-cyan-300 flex items-center gap-3 text-lg font-semibold">
                  <MessageCircle className="text-cyan-500" size={22} />
                  AI Trading Assistant
                  <div className="ml-auto w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col p-4">
                <div 
                  ref={chatScrollRef}
                  className="flex-1 mb-4 max-h-[350px] lg:max-h-[450px] overflow-y-auto pr-2"
                  style={{ scrollBehavior: 'smooth' }}
                >
                  <div className="space-y-4">
                    {chatMessages.map((msg) => (
                      <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[90%] p-4 rounded-lg border shadow-lg ${
                          msg.role === 'user' 
                            ? 'bg-gradient-to-r from-amber-600 to-amber-700 text-black border-amber-500/50 shadow-amber-500/25' 
                            : 'bg-gradient-to-r from-gray-700 to-gray-800 text-gray-100 border-gray-600/50 shadow-gray-500/25'
                        }`}>
                          <div className="text-sm leading-relaxed font-medium whitespace-pre-wrap">
                            {msg.message.split('\n').map((line, index) => {
                              // Handle headers (lines starting with ##, **, or numbered lists)
                              if (line.startsWith('##')) {
                                return (
                                  <div key={index} className="font-semibold text-amber-300 mb-2 mt-3 first:mt-0">
                                    {line.replace(/^##\s*/, '')}
                                  </div>
                                );
                              }
                              // Handle bullet points
                              if (line.startsWith('- ') || line.startsWith('• ')) {
                                return (
                                  <div key={index} className="ml-4 mb-1 flex items-start">
                                    <span className="text-amber-400 mr-2 mt-1">•</span>
                                    <span>{line.replace(/^[-•]\s*/, '')}</span>
                                  </div>
                                );
                              }
                              // Handle numbered lists
                              if (/^\d+\./.test(line)) {
                                return (
                                  <div key={index} className="ml-4 mb-1 flex items-start">
                                    <span className="text-amber-400 mr-2 font-medium">{line.match(/^\d+\./)[0]}</span>
                                    <span>{line.replace(/^\d+\.\s*/, '')}</span>
                                  </div>
                                );
                              }
                              // Regular text
                              return line.trim() ? (
                                <div key={index} className="mb-1">
                                  {line}
                                </div>
                              ) : (
                                <div key={index} className="mb-1"></div>
                              );
                            })}
                          </div>
                          <p className="text-xs opacity-70 mt-3 font-mono border-t border-gray-600/30 pt-2">
                            {new Date(msg.timestamp).toLocaleString(undefined, { 
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit',
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric'
                            })}
                          </p>
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gradient-to-r from-gray-700 to-gray-800 text-gray-100 p-4 rounded-lg border border-gray-600/50 shadow-lg">
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div>
                            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                            <span className="text-sm font-medium">AI Coach is analyzing your request...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-3">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask about trading strategies, market analysis..."
                    className="bg-gradient-to-r from-gray-700 to-gray-800 border-amber-600/40 text-amber-100 placeholder-amber-400/60 focus:border-amber-500 focus:ring-amber-500/50 font-medium"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button 
                    onClick={handleSendMessage}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold border border-amber-500/50 shadow-lg px-4"
                  >
                    Send
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Dashboard Content */}
          <div className="lg:col-span-2 order-1 lg:order-2">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6 bg-gradient-to-r from-gray-800 to-gray-900 border border-cyan-600/40 p-1 rounded-xl shadow-lg">
                <TabsTrigger value="overview" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Overview
                </TabsTrigger>
                <TabsTrigger value="portfolio" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Portfolio
                </TabsTrigger>
                <TabsTrigger value="strategy" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Strategy
                </TabsTrigger>
                <TabsTrigger value="risk" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Risk
                </TabsTrigger>
                <TabsTrigger value="campaigns" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Campaigns
                </TabsTrigger>
                <TabsTrigger value="technical" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Technical
                </TabsTrigger>
                <TabsTrigger value="backtesting" className="text-cyan-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-600 data-[state=active]:to-cyan-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  <TestTube className="mr-1" size={16} />
                  Backtest
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-6">
                
                {/* Monthly Progress */}
                <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                    <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                      <Target className="text-amber-500" size={24} />
                      Monthly Target Progress
                      <div className="ml-auto bg-gradient-to-r from-amber-600 to-amber-700 text-black px-3 py-1 rounded-full text-sm font-bold">
                        {formatCurrency(monthlyTargetState || 100000)} Goal
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-gradient-to-r from-green-900/40 to-green-800/40 rounded-xl border border-green-600/30">
                          <div className="text-2xl font-bold font-mono text-green-400">
                            {portfolio && portfolio.total_value ? formatCurrency(currentMonthProgress) : 
                             isLoading ? "Loading..." : 
                             "R 0.00"}
                          </div>
                          <div className="text-sm text-green-300/80">Current Value</div>
                        </div>
                        <div className="text-center p-4 bg-gradient-to-r from-blue-900/40 to-blue-800/40 rounded-xl border border-blue-600/30">
                          <div className="text-2xl font-bold font-mono text-blue-400">
                            {formatCurrency(monthlyTargetState || 100000)}
                          </div>
                          <div className="text-sm text-blue-300/80">Monthly Target</div>
                        </div>
                        <div className="text-center p-4 bg-gradient-to-r from-amber-900/40 to-amber-800/40 rounded-xl border border-amber-600/30">
                          <div className="text-2xl font-bold font-mono text-amber-400">
                            {formatCurrency((monthlyTargetState || 100000) - currentMonthProgress)}
                          </div>
                          <div className="text-sm text-amber-300/80">Remaining</div>
                        </div>
                      </div>
                      <div className="bg-gradient-to-r from-gray-700 to-gray-800 rounded-full h-6 border border-amber-600/30 overflow-hidden shadow-inner">
                        <div 
                          className="h-full bg-gradient-to-r from-amber-500 via-amber-400 to-amber-600 transition-all duration-1000 ease-out shadow-lg relative"
                          style={{width: `${Math.min((currentMonthProgress / (monthlyTargetState || 100000)) * 100, 100)}%`}}
                        >
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold font-mono bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent">
                          {((currentMonthProgress / (monthlyTargetState || 100000)) * 100).toFixed(1)}%
                        </div>
                        <div className="text-amber-400/80 text-sm mt-1 font-medium">
                          Progress Towards Freedom
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Market Overview */}
                <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                    <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                      <BarChart3 className="text-amber-500" size={24} />
                      Live Market Data
                      <div className="ml-auto w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {marketData.map((crypto) => (
                        <div key={crypto.symbol} className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <div className="font-bold text-amber-300 text-lg">{crypto.symbol}</div>
                              <div className="text-sm text-amber-400/70 font-medium">{crypto.name}</div>
                            </div>
                            <div className="text-right">
                              <div className="text-amber-100 font-mono text-base font-semibold">{formatCurrency(crypto.price)}</div>
                              <div className={`text-sm flex items-center gap-1 justify-end font-semibold ${
                                crypto.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {crypto.change_24h >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                {formatPercentage(crypto.change_24h)}
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-amber-600/20">
                            <div className="text-xs text-amber-400/60 font-medium">
                              Volume: {formatCurrency(crypto.volume)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Weekly Targets */}
                {weeklyTargets && (
                  <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                    <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                      <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                        <DollarSign className="text-amber-500" size={24} />
                        Weekly Performance
                        <div className="ml-auto bg-gradient-to-r from-blue-600 to-blue-700 text-white px-3 py-1 rounded-full text-sm font-bold">
                          {weeklyTargets.days_left} Days Left
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="text-center p-4 bg-gradient-to-r from-blue-900/40 to-blue-800/40 rounded-xl border border-blue-600/30">
                            <div className="text-2xl font-bold font-mono text-blue-400">
                              {formatCurrency(weeklyTargets.target)}
                            </div>
                            <div className="text-sm text-blue-300/80">Weekly Target</div>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-r from-green-900/40 to-green-800/40 rounded-xl border border-green-600/30">
                            <div className="text-2xl font-bold font-mono text-green-400">
                              {formatCurrency(weeklyTargets.achieved)}
                            </div>
                            <div className="text-sm text-green-300/80">Achieved</div>
                          </div>
                        </div>
                        <div className="bg-gradient-to-r from-gray-700 to-gray-800 rounded-full h-6 border border-amber-600/30 overflow-hidden shadow-inner">
                          <div 
                            className="h-full bg-gradient-to-r from-blue-500 via-blue-400 to-blue-600 transition-all duration-1000 ease-out shadow-lg relative"
                            style={{width: `${Math.min(weeklyTargets.progress, 100)}%`}}
                          >
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold font-mono bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
                            {formatCurrency(weeklyTargets.remaining)}
                          </div>
                          <div className="text-amber-400/80 text-sm mt-1 font-medium">
                            Remaining This Week
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

              </TabsContent>

              {/* Portfolio Tab */}
              <TabsContent value="portfolio" className="space-y-6">
                <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                    <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                      <PieChart className="text-amber-500" size={24} />
                      Portfolio Holdings
                      <div className="ml-auto bg-gradient-to-r from-green-600 to-green-700 text-white px-3 py-1 rounded-full text-sm font-bold">
                        {portfolio?.holdings?.length || 0} Assets
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      {portfolio?.holdings?.map((holding) => (
                        <div key={holding.symbol} className="p-5 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20 shadow-lg hover:shadow-xl transition-all duration-300">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <div className="flex items-center gap-2">
                                <div className="font-bold text-amber-300 text-xl">{holding.symbol}</div>
                                {holding.is_staked && (
                                  <Badge className="bg-gradient-to-r from-blue-600 to-blue-700 text-white text-xs">
                                    STAKED
                                  </Badge>
                                )}
                                {holding.source === 'USD' && (
                                  <Badge className="bg-gradient-to-r from-green-600 to-green-700 text-white text-xs">
                                    USD→ZAR
                                  </Badge>
                                )}
                                {holding.source === 'Luno' && (
                                  <Badge className="bg-gradient-to-r from-amber-600 to-amber-700 text-black text-xs">
                                    LUNO
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm text-amber-400/70 font-medium">{holding.name}</div>
                              <div className="text-sm text-amber-400/50 mt-2 font-mono bg-gray-800/50 px-3 py-1 rounded-lg">
                                {formatNumber(holding.amount)} units
                                {holding.accounts > 1 && (
                                  <span className="ml-2 text-blue-400">({holding.accounts} accounts)</span>
                                )}
                                {holding.is_staked && (
                                  <span className="ml-2 text-purple-400">• Earning Rewards</span>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-amber-100 font-mono text-lg font-semibold">{formatCurrency(holding.value)}</div>
                              <div className={`text-sm font-semibold flex items-center gap-1 justify-end ${
                                holding.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {holding.change_24h >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                {formatPercentage(holding.change_24h)}
                              </div>
                            </div>
                          </div>
                          <div className="flex justify-between items-center pt-4 border-t border-amber-600/20">
                            <div className="text-sm text-amber-400/60 font-medium">
                              Price: {formatCurrency(holding.current_price)}
                            </div>
                            <div className="bg-gradient-to-r from-amber-600 to-amber-700 text-black px-3 py-1 rounded-full text-sm font-bold">
                              {holding.allocation.toFixed(1)}% of portfolio
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Strategy Tab */}
              <TabsContent value="strategy" className="space-y-6">
                {dailyStrategy && (
                  <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                    <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                      <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                        <Zap className="text-amber-500" size={24} />
                        Daily Trading Strategy
                      </CardTitle>
                      <Badge className="w-fit bg-gradient-to-r from-orange-600 to-orange-700 text-white border border-orange-500/50 font-semibold shadow-lg">
                        {dailyStrategy.risk_level} Risk Level
                      </Badge>
                    </CardHeader>
                    <CardContent className="p-6">
                      <div className="space-y-6">
                        <div className="p-5 bg-gradient-to-r from-blue-900/40 to-blue-800/40 rounded-xl border border-blue-600/30">
                          <h4 className="text-amber-300 font-semibold mb-3 text-lg">Primary Recommendation</h4>
                          <p className="text-amber-100 leading-relaxed font-medium text-base">
                            {dailyStrategy.main_recommendation}
                          </p>
                        </div>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                          <div className="text-center p-4 bg-gradient-to-r from-green-900/40 to-green-800/40 rounded-xl border border-green-600/30">
                            <div className="text-sm text-green-300/80 font-medium">Expected Return</div>
                            <div className="text-green-400 font-mono text-xl font-bold">{dailyStrategy.expected_return}</div>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-r from-blue-900/40 to-blue-800/40 rounded-xl border border-blue-600/30">
                            <div className="text-sm text-blue-300/80 font-medium">Timeframe</div>
                            <div className="text-blue-400 font-mono text-xl font-bold">{dailyStrategy.timeframe}</div>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-r from-purple-900/40 to-purple-800/40 rounded-xl border border-purple-600/30">
                            <div className="text-sm text-purple-300/80 font-medium">Target Price</div>
                            <div className="text-purple-400 font-mono text-xl font-bold">{dailyStrategy.key_levels.target}</div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-amber-300 font-semibold mb-4 text-lg">Recommended Actions</h4>
                          <div className="space-y-4">
                            {dailyStrategy.actions.map((action, index) => (
                              <div key={index} className="p-5 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20 shadow-lg">
                                <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-3">
                                      <Badge className={`${
                                        action.type === 'BUY' ? 'bg-gradient-to-r from-green-600 to-green-700 text-white' : 'bg-gradient-to-r from-red-600 to-red-700 text-white'
                                      } font-bold shadow-lg`}>
                                        {action.type}
                                      </Badge>
                                      <div className="text-amber-300 font-mono text-lg font-bold">{action.asset}</div>
                                    </div>
                                    <div className="text-sm text-amber-400/80 leading-relaxed font-medium bg-gray-800/50 p-3 rounded-lg">
                                      {action.reasoning}
                                    </div>
                                  </div>
                                  <div className="text-right bg-gradient-to-r from-amber-900/40 to-amber-800/40 p-4 rounded-xl border border-amber-600/30">
                                    <div className="text-amber-200 font-mono text-base font-semibold">{action.amount}</div>
                                    <div className="text-sm text-amber-400/80 font-medium mt-1">@ {action.price}</div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Risk Tab */}
              <TabsContent value="risk" className="space-y-6">
                {riskMetrics && (
                  <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                    <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                      <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                        <Shield className="text-amber-500" size={24} />
                        Risk Management Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                      <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center p-5 bg-gradient-to-r from-red-900/40 to-red-800/40 rounded-xl border border-red-600/30">
                            <div className="text-3xl font-bold font-mono text-red-400">
                              {riskMetrics.risk_score}/10
                            </div>
                            <div className="text-sm text-red-300/80 font-medium">Risk Score</div>
                          </div>
                          <div className="text-center p-5 bg-gradient-to-r from-orange-900/40 to-orange-800/40 rounded-xl border border-orange-600/30">
                            <div className="text-3xl font-bold font-mono text-orange-400">
                              {riskMetrics.portfolio_var}%
                            </div>
                            <div className="text-sm text-orange-300/80 font-medium">Value at Risk</div>
                          </div>
                          <div className="text-center p-5 bg-gradient-to-r from-green-900/40 to-green-800/40 rounded-xl border border-green-600/30">
                            <div className="text-3xl font-bold font-mono text-green-400">
                              {riskMetrics.sharpe_ratio}
                            </div>
                            <div className="text-sm text-green-300/80 font-medium">Sharpe Ratio</div>
                          </div>
                          <div className="text-center p-5 bg-gradient-to-r from-purple-900/40 to-purple-800/40 rounded-xl border border-purple-600/30">
                            <div className="text-3xl font-bold font-mono text-purple-400">
                              {riskMetrics.diversification_score}/10
                            </div>
                            <div className="text-sm text-purple-300/80 font-medium">Diversification</div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-amber-300 font-semibold mb-4 text-lg flex items-center gap-2">
                            <AlertTriangle className="text-amber-500" size={20} />
                            Risk Management Recommendations
                          </h4>
                          <div className="space-y-3">
                            {riskMetrics.recommendations.map((rec, index) => (
                              <div key={index} className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20 shadow-lg">
                                <p className="text-amber-100 leading-relaxed font-medium">{rec}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Campaigns Tab */}
              <TabsContent value="campaigns" className="space-y-6">
                
                {/* Create New Campaign */}
                <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                    <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                      <Target className="text-amber-500" size={24} />
                      Targeted Trading Campaigns
                      <Button
                        onClick={() => setShowCreateCampaignModal(true)}
                        className="ml-auto bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold border border-green-500/50 shadow-lg"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        New Campaign
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="text-center text-amber-300/80 mb-6">
                      <p className="text-lg font-semibold mb-2">🎯 High-Precision Trading Campaigns</p>
                      <p className="text-sm">Allocate specific capital • Set profit targets • Define timeframes • Let AI execute</p>
                    </div>
                    
                    {activeCampaigns.length === 0 ? (
                      <div className="text-center py-8">
                        <div className="text-6xl mb-4">💰</div>
                        <p className="text-amber-400 text-lg font-semibold mb-2">Ready to Turn R10k into R20k?</p>
                        <p className="text-amber-300/70 mb-4">Create your first targeted trading campaign</p>
                        <Button
                          onClick={() => setShowCreateCampaignModal(true)}
                          className="bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold"
                        >
                          <Target className="w-4 h-4 mr-2" />
                          Start Campaign
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {activeCampaigns.map((campaign, index) => (
                          <div key={index} className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20">
                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <h3 className="font-bold text-amber-300">{campaign.name}</h3>
                                <p className="text-sm text-amber-400/70">Target: {((campaign.profit_target / campaign.allocated_capital) * 100).toFixed(0)}% in {campaign.timeframe_days} days</p>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  onClick={() => executeCampaignTrades(campaign.id)}
                                  className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white text-xs px-3 py-1"
                                >
                                  <Play className="w-3 h-3 mr-1" />
                                  Execute
                                </Button>
                                <Button
                                  className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white text-xs px-3 py-1"
                                >
                                  <Pause className="w-3 h-3 mr-1" />
                                  Pause
                                </Button>
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div>
                                <div className="text-green-400 font-mono">{formatCurrency(campaign.current_value || campaign.allocated_capital)}</div>
                                <div className="text-amber-400/70">Current Value</div>
                              </div>
                              <div>
                                <div className="text-blue-400 font-mono">{formatCurrency(campaign.profit_target)}</div>
                                <div className="text-amber-400/70">Target Profit</div>
                              </div>
                              <div>
                                <div className="text-amber-400 font-mono">{campaign.timeframe_days} days</div>
                                <div className="text-amber-400/70">Timeframe</div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Campaign Creation Modal */}
                {showCreateCampaignModal && (
                  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 rounded-xl p-6 max-w-md w-full mx-4">
                      <h3 className="text-xl font-bold text-amber-300 mb-4">🎯 Create Trading Campaign</h3>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="block text-amber-400 text-sm font-medium mb-2">Allocated Capital (ZAR)</label>
                          <Input
                            type="number"
                            value={newCampaignData.allocated_capital}
                            onChange={(e) => setNewCampaignData(prev => ({ ...prev, allocated_capital: parseFloat(e.target.value) }))}
                            className="bg-gray-700 border-amber-600/40 text-amber-100"
                            placeholder="10000"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-amber-400 text-sm font-medium mb-2">Profit Target (ZAR)</label>
                          <Input
                            type="number"
                            value={newCampaignData.profit_target}
                            onChange={(e) => setNewCampaignData(prev => ({ ...prev, profit_target: parseFloat(e.target.value) }))}
                            className="bg-gray-700 border-amber-600/40 text-amber-100"
                            placeholder="10000"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-amber-400 text-sm font-medium mb-2">Timeframe (Days)</label>
                          <Input
                            type="number"
                            value={newCampaignData.timeframe_days}
                            onChange={(e) => setNewCampaignData(prev => ({ ...prev, timeframe_days: parseInt(e.target.value) }))}
                            className="bg-gray-700 border-amber-600/40 text-amber-100"
                            placeholder="7"
                          />
                        </div>
                        
                        <div className="bg-red-900/20 border border-red-600/30 rounded-lg p-3">
                          <p className="text-red-400 text-sm font-semibold">⚠️ HIGH RISK WARNING</p>
                          <p className="text-red-300/80 text-xs mt-1">
                            Target: {((newCampaignData.profit_target / newCampaignData.allocated_capital) * 100).toFixed(0)}% return in {newCampaignData.timeframe_days} days requires aggressive trading. Only proceed if you can afford to lose the entire amount.
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex gap-3 mt-6">
                        <Button
                          onClick={() => setShowCreateCampaignModal(false)}
                          className="flex-1 bg-gray-700 hover:bg-gray-600 text-amber-300"
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={createTradingCampaign}
                          disabled={isLoading}
                          className="flex-1 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold"
                        >
                          {isLoading ? 'Creating...' : 'Create Campaign'}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

              </TabsContent>

              {/* Technical Analysis Tab */}
              <TabsContent value="technical" className="space-y-6">
                {/* Market Overview */}
                <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                    <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                      <Activity className="text-amber-500" size={24} />
                      Market Technical Overview
                      <Button
                        onClick={loadMarketOverview}
                        className="ml-auto bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold p-2 rounded-full"
                        size="sm"
                      >
                        <RefreshCw size={16} />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    {marketOverview ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {marketOverview.market_overview?.map((crypto) => (
                          <div key={crypto.symbol} className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20 shadow-lg">
                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <div className="font-bold text-amber-300 text-lg">{crypto.symbol}</div>
                                <div className="text-sm text-amber-400/70">{formatCurrency(crypto.price)}</div>
                              </div>
                              <div className="text-right">
                                <div className={`text-sm font-bold ${
                                  crypto.trend === 'bullish' ? 'text-green-400' : 
                                  crypto.trend === 'bearish' ? 'text-red-400' : 'text-amber-400'
                                }`}>
                                  {crypto.trend?.toUpperCase()}
                                </div>
                                <div className="text-xs text-amber-400/60">
                                  Strength: {(crypto.trend_strength * 100).toFixed(0)}%
                                </div>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-amber-400/70">RSI:</span>
                                <span className="text-amber-100">{crypto.rsi?.toFixed(1) || 'N/A'}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-amber-400/70">Recommendation:</span>
                                <span className={`font-bold ${
                                  crypto.recommendation?.action === 'BUY' ? 'text-green-400' : 
                                  crypto.recommendation?.action === 'SELL' ? 'text-red-400' : 'text-amber-400'
                                }`}>
                                  {crypto.recommendation?.action || 'HOLD'}
                                </span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-amber-400/70">Signals:</span>
                                <span className="text-amber-100">{crypto.signals_count || 0}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-amber-400/60">
                        <Activity className="mx-auto mb-3" size={48} />
                        <p>Loading market technical analysis...</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Symbol Selector */}
                <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                    <CardTitle className="text-amber-300 flex items-center gap-3 text-xl font-semibold">
                      <TrendingUpIcon className="text-amber-500" size={24} />
                      Technical Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="mb-4 flex flex-wrap gap-2">
                      {['BTC', 'ETH', 'ADA', 'XRP', 'SOL'].map((symbol) => (
                        <Button
                          key={symbol}
                          onClick={() => {
                            setSelectedTechnicalSymbol(symbol);
                            loadTechnicalAnalysis();
                            loadTechnicalIndicators(symbol);
                          }}
                          className={`${selectedTechnicalSymbol === symbol 
                            ? 'bg-gradient-to-r from-amber-600 to-amber-700 text-black' 
                            : 'bg-gray-700 text-amber-300 hover:bg-gray-600'} font-semibold`}
                        >
                          {symbol}
                        </Button>
                      ))}
                    </div>

                    {technicalAnalysis && (
                      <div className="space-y-6">
                        {/* Current Price and Trend */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="text-center p-4 bg-gradient-to-r from-blue-900/40 to-blue-800/40 rounded-xl border border-blue-600/30">
                            <div className="text-2xl font-bold font-mono text-blue-400">
                              {formatCurrency(technicalAnalysis.current_price)}
                            </div>
                            <div className="text-sm text-blue-300/80">Current Price</div>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-r from-green-900/40 to-green-800/40 rounded-xl border border-green-600/30">
                            <div className="text-2xl font-bold text-green-400">
                              {technicalAnalysis.trend_analysis?.trend?.toUpperCase()}
                            </div>
                            <div className="text-sm text-green-300/80">Trend Direction</div>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-r from-amber-900/40 to-amber-800/40 rounded-xl border border-amber-600/30">
                            <div className="text-2xl font-bold text-amber-400">
                              {technicalAnalysis.recommendation?.action}
                            </div>
                            <div className="text-sm text-amber-300/80">Recommendation</div>
                          </div>
                        </div>

                        {/* Technical Indicators */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {technicalAnalysis.technical_indicators?.rsi && (
                            <div className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-amber-400 font-medium">RSI</span>
                                <span className="text-amber-100 font-mono font-bold">
                                  {technicalAnalysis.technical_indicators.rsi.toFixed(1)}
                                </span>
                              </div>
                              <div className="w-full bg-gray-600 rounded-full h-2">
                                <div 
                                  className={`h-2 rounded-full ${
                                    technicalAnalysis.technical_indicators.rsi > 70 ? 'bg-red-500' :
                                    technicalAnalysis.technical_indicators.rsi < 30 ? 'bg-green-500' : 'bg-amber-500'
                                  }`}
                                  style={{width: `${technicalAnalysis.technical_indicators.rsi}%`}}
                                ></div>
                              </div>
                              <div className="text-xs text-amber-400/60 mt-1">
                                {technicalAnalysis.technical_indicators.rsi > 70 ? 'Overbought' :
                                 technicalAnalysis.technical_indicators.rsi < 30 ? 'Oversold' : 'Neutral'}
                              </div>
                            </div>
                          )}

                          {technicalAnalysis.technical_indicators?.macd && (
                            <div className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20">
                              <div className="text-amber-400 font-medium mb-2">MACD</div>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">MACD:</span>
                                  <span className="text-amber-100 font-mono">
                                    {technicalAnalysis.technical_indicators.macd.macd?.toFixed(4) || 'N/A'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Signal:</span>
                                  <span className="text-amber-100 font-mono">
                                    {technicalAnalysis.technical_indicators.macd.signal?.toFixed(4) || 'N/A'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Histogram:</span>
                                  <span className="text-amber-100 font-mono">
                                    {technicalAnalysis.technical_indicators.macd.histogram?.toFixed(4) || 'N/A'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}

                          {technicalAnalysis.technical_indicators?.bollinger_bands && (
                            <div className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20">
                              <div className="text-amber-400 font-medium mb-2">Bollinger Bands</div>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Upper:</span>
                                  <span className="text-amber-100 font-mono">
                                    {formatCurrency(technicalAnalysis.technical_indicators.bollinger_bands.upper || 0)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Middle:</span>
                                  <span className="text-amber-100 font-mono">
                                    {formatCurrency(technicalAnalysis.technical_indicators.bollinger_bands.middle || 0)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Lower:</span>
                                  <span className="text-amber-100 font-mono">
                                    {formatCurrency(technicalAnalysis.technical_indicators.bollinger_bands.lower || 0)}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}

                          {technicalAnalysis.technical_indicators?.support_resistance && (
                            <div className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20">
                              <div className="text-amber-400 font-medium mb-2">Support/Resistance</div>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Support:</span>
                                  <span className="text-green-400 font-mono">
                                    {formatCurrency(technicalAnalysis.technical_indicators.support_resistance.support || 0)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-amber-400/70">Resistance:</span>
                                  <span className="text-red-400 font-mono">
                                    {formatCurrency(technicalAnalysis.technical_indicators.support_resistance.resistance || 0)}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Trading Signals */}
                        {technicalAnalysis.trading_signals && technicalAnalysis.trading_signals.length > 0 && (
                          <div className="p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl border border-amber-600/20">
                            <div className="text-amber-400 font-medium mb-3">Trading Signals</div>
                            <div className="space-y-2">
                              {technicalAnalysis.trading_signals.map((signal, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                                  <div className="flex items-center gap-2">
                                    <Badge className={`${
                                      signal.type === 'BUY' ? 'bg-green-600' : 
                                      signal.type === 'SELL' ? 'bg-red-600' : 'bg-amber-600'
                                    } text-white font-semibold`}>
                                      {signal.type}
                                    </Badge>
                                    <span className="text-amber-100 text-sm">{signal.reason}</span>
                                  </div>
                                  <div className="text-xs text-amber-400/60">
                                    {signal.indicator} • {signal.strength}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Backtesting Tab */}
              <TabsContent value="backtesting" className="space-y-6">
                <BacktestingDashboard />
              </TabsContent>

            </Tabs>
          </div>
        </div>

      {/* Target Adjustment Modal */}
      {showTargetAdjustmentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-amber-300 mb-4">🎯 Adjust Monthly Targets</h3>
            
            <div className="space-y-4">
              <div className="bg-amber-900/20 border border-amber-600/30 rounded-lg p-3 mb-4">
                <p className="text-amber-400 text-sm font-semibold">💡 AI Target Adjustment</p>
                <p className="text-amber-300/80 text-xs mt-1">
                  You can also ask the AI: "Change my monthly target to R150k" or "Adjust my targets based on my performance"
                </p>
              </div>
              
              <div>
                <label className="block text-amber-400 text-sm font-medium mb-2">Monthly Target (ZAR)</label>
                <Input
                  type="number"
                  value={newTargetData.monthly_target}
                  onChange={(e) => setNewTargetData(prev => ({ 
                    ...prev, 
                    monthly_target: parseFloat(e.target.value),
                    weekly_target: parseFloat(e.target.value) / 4
                  }))}
                  className="bg-gray-700 border-amber-600/40 text-amber-100"
                  placeholder="100000"
                />
                <p className="text-xs text-amber-400/70 mt-1">Current: {formatCurrency(monthlyTargetState)}</p>
              </div>
              
              <div>
                <label className="block text-amber-400 text-sm font-medium mb-2">Weekly Target (Auto-calculated)</label>
                <Input
                  type="number"
                  value={newTargetData.weekly_target}
                  readOnly
                  className="bg-gray-600 border-amber-600/40 text-amber-100 cursor-not-allowed"
                />
                <p className="text-xs text-amber-400/70 mt-1">Automatically set to Monthly ÷ 4</p>
              </div>
              
              <div className="bg-blue-900/20 border border-blue-600/30 rounded-lg p-3">
                <p className="text-blue-400 text-sm font-semibold">📊 Target Analysis</p>
                <p className="text-blue-300/80 text-xs mt-1">
                  New target represents {((newTargetData.monthly_target / (portfolio?.total_value || 155000)) * 100).toFixed(1)}% of current portfolio value.
                  {((newTargetData.monthly_target / (portfolio?.total_value || 155000)) * 100) > 200 ? " ⚠️ Very aggressive target!" :
                   ((newTargetData.monthly_target / (portfolio?.total_value || 155000)) * 100) > 100 ? " 🎯 Challenging but achievable." :
                   " ✅ Conservative target."}
                </p>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <Button
                onClick={() => {
                  setShowTargetAdjustmentModal(false);
                  setNewTargetData({
                    monthly_target: monthlyTargetState,
                    weekly_target: weeklyTargetState
                  });
                }}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-amber-300"
              >
                Cancel
              </Button>
              <Button
                onClick={updateTargetsManually}
                disabled={isLoading}
                className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold"
              >
                {isLoading ? 'Updating...' : 'Update Targets'}
              </Button>
            </div>
          </div>
        </div>
      )}

        {/* Auto Trading Modal */}
        {showAutoTradeModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-xl border border-amber-600/40 shadow-2xl max-w-md w-full">
              <h3 className="text-xl font-bold text-amber-300 mb-4">Auto Trading Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-amber-400 text-sm font-medium">Auto Trading</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Button
                      onClick={() => setAutoTradeSettings({...autoTradeSettings, enabled: !autoTradeSettings?.enabled})}
                      className={`${autoTradeSettings?.enabled ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white font-semibold`}
                    >
                      {autoTradeSettings?.enabled ? 'ENABLED' : 'DISABLED'}
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="text-amber-400 text-sm font-medium">Max Trade Amount</label>
                  <Input
                    type="number"
                    value={autoTradeSettings?.max_trade_amount || 1000}
                    onChange={(e) => setAutoTradeSettings({...autoTradeSettings, max_trade_amount: parseFloat(e.target.value)})}
                    className="bg-gray-700 border-amber-600/40 text-white mt-1"
                    placeholder="1000"
                  />
                  <div className="text-xs text-amber-400/60 mt-1">Maximum ZAR per trade</div>
                </div>

                <div>
                  <label className="text-amber-400 text-sm font-medium">Daily Limit</label>
                  <Input
                    type="number"
                    value={autoTradeSettings?.daily_limit || 5000}
                    onChange={(e) => setAutoTradeSettings({...autoTradeSettings, daily_limit: parseFloat(e.target.value)})}
                    className="bg-gray-700 border-amber-600/40 text-white mt-1"
                    placeholder="5000"
                  />
                  <div className="text-xs text-amber-400/60 mt-1">Maximum ZAR per day</div>
                </div>

                <div>
                  <label className="text-amber-400 text-sm font-medium">Stop Loss %</label>
                  <Input
                    type="number"
                    value={autoTradeSettings?.stop_loss_percent || 5}
                    onChange={(e) => setAutoTradeSettings({...autoTradeSettings, stop_loss_percent: parseFloat(e.target.value)})}
                    className="bg-gray-700 border-amber-600/40 text-white mt-1"
                    placeholder="5"
                  />
                  <div className="text-xs text-amber-400/60 mt-1">Auto sell when down this %</div>
                </div>

                <div>
                  <label className="text-amber-400 text-sm font-medium">Take Profit %</label>
                  <Input
                    type="number"
                    value={autoTradeSettings?.take_profit_percent || 10}
                    onChange={(e) => setAutoTradeSettings({...autoTradeSettings, take_profit_percent: parseFloat(e.target.value)})}
                    className="bg-gray-700 border-amber-600/40 text-white mt-1"
                    placeholder="10"
                  />
                  <div className="text-xs text-amber-400/60 mt-1">Auto sell when up this %</div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <Button
                  onClick={() => setShowAutoTradeModal(false)}
                  className="bg-gray-600 hover:bg-gray-700 text-white font-semibold flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    try {
                      await axios.put(`${API}/autotrade/settings`, autoTradeSettings);
                      setShowAutoTradeModal(false);
                    } catch (error) {
                      console.error('Error saving auto trade settings:', error);
                    }
                  }}
                  className="bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold flex-1"
                >
                  Save Settings
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CryptoTraderCoach;