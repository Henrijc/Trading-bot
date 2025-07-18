import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { TrendingUp, TrendingDown, Target, AlertTriangle, MessageCircle, DollarSign, BarChart3, Shield, RefreshCw, Activity, PieChart, TrendingUpIcon, Zap } from 'lucide-react';
import axios from 'axios';

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
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [activeTab, setActiveTab] = useState('overview');
  const [lastRefresh, setLastRefresh] = useState(Date.now());
  const [monthlyTargetState, setMonthlyTargetState] = useState(100000);
  const [weeklyTargetState, setWeeklyTargetState] = useState(25000);
  const [targetSettings, setTargetSettings] = useState(null);
  const [autoTradeSettings, setAutoTradeSettings] = useState(null);
  const [showAutoTradeModal, setShowAutoTradeModal] = useState(false);
  const [technicalAnalysis, setTechnicalAnalysis] = useState(null);
  const [selectedTechnicalSymbol, setSelectedTechnicalSymbol] = useState('BTC');
  const [technicalIndicators, setTechnicalIndicators] = useState(null);
  const [marketOverview, setMarketOverview] = useState(null);
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

  const loadInitialData = async () => {
    try {
      await Promise.all([
        loadMarketData(),
        loadPortfolio(),
        loadDailyStrategy(),
        loadWeeklyTargets(),
        loadRiskMetrics(),
        loadChatHistory(),
        loadTargetSettings(),
        loadAutoTradeSettings()
      ]);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };

  const loadMarketData = async () => {
    try {
      const response = await axios.get(`${API}/market/data`);
      setMarketData(response.data);
    } catch (error) {
      console.error('Error loading market data:', error);
    }
  };

  const loadPortfolio = async () => {
    try {
      const response = await axios.get(`${API}/portfolio`);
      setPortfolio(response.data);
    } catch (error) {
      console.error('Error loading portfolio:', error);
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
      const response = await axios.get(`${API}/chat/history/${sessionId}`);
      setChatMessages(response.data);
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Start with a welcome message if no history
      setChatMessages([{
        id: 1,
        role: 'assistant',
        message: 'Hello! I am your AI Trading Coach and I am here to help you reach your R100,000 monthly target. I can analyze your portfolio, research market conditions, and help you make informed trading decisions. What would you like to know about your investments or the crypto market?',
        timestamp: new Date().toISOString()
      }]);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      message: inputMessage,
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/chat/send`, {
        session_id: sessionId,
        role: 'user',
        message: inputMessage
      });
      
      setChatMessages(prev => [...prev, response.data]);
      
      if (response.data.message.includes('adjust') && response.data.message.includes('target')) {
        try {
          const adjustResponse = await axios.post(`${API}/ai/adjust-targets`, {
            reason: inputMessage
          });
          
          if (adjustResponse.data.success) {
            await loadTargetSettings();
            // Add AI message about target adjustment
            setChatMessages(prev => [...prev, {
              id: Date.now() + 1,
              role: 'assistant',
              message: `Target Update: ${adjustResponse.data.message}\n\nNew Monthly Target: ${formatCurrency(adjustResponse.data.new_targets.monthly_target)}\n\nI have adjusted your targets based on current performance and market conditions.`,
              timestamp: new Date().toISOString()
            }]);
          }
        } catch (error) {
          console.error('Error adjusting targets:', error);
        }
      }
      
      // Check if AI suggests a trade
      if (response.data.message.includes('BUY') || response.data.message.includes('SELL')) {
        // Add a follow-up message with trading options
        setChatMessages(prev => [...prev, {
          id: Date.now() + 2,
          role: 'assistant',
          message: `Ready to Execute Trade?\n\nI can help you execute this trade on Luno. Just confirm and I will place the order for you.\n\nNote: This will be a real trade on your Luno account. Always double-check before confirming.`,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      setChatMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        message: 'Connection error. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLastRefresh(Date.now());
    await loadInitialData();
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

  const currentMonthProgress = portfolio?.total_value || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-900/20 via-transparent to-transparent"></div>
      
      <div className="relative z-10 container mx-auto p-4 lg:p-6">
        {/* Header */}
        <div className="mb-6 lg:mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-gradient-to-r from-transparent via-amber-700/50 to-transparent pb-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-amber-500 to-amber-700 rounded-xl shadow-lg">
                <Activity className="w-8 h-8 text-black" />
              </div>
              <div>
                <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 bg-clip-text text-transparent">
                  AI Trading Coach
                </h1>
                <p className="text-amber-600/80 text-sm lg:text-base font-medium">
                  Professional Cryptocurrency Trading Analysis
                </p>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <Button
                onClick={handleRefresh}
                className="bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-black font-semibold border border-amber-500/50 shadow-lg shadow-amber-500/25 transition-all duration-300"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Data
              </Button>
              <Button
                onClick={() => setShowAutoTradeModal(true)}
                className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold border border-blue-500/50 shadow-lg shadow-blue-500/25 transition-all duration-300"
              >
                <Activity className="w-4 h-4 mr-2" />
                Auto Trade: {autoTradeSettings?.enabled ? 'ON' : 'OFF'}
              </Button>
              <div className="text-center lg:text-right bg-gradient-to-r from-gray-800 to-gray-900 p-4 rounded-xl border border-amber-600/30 shadow-lg">
                <div className="text-2xl lg:text-3xl font-bold font-mono bg-gradient-to-r from-green-400 to-green-500 bg-clip-text text-transparent">
                  {formatCurrency(currentMonthProgress)}
                </div>
                <div className="text-xs lg:text-sm text-amber-400/80 font-medium">
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
            <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border border-amber-600/40 shadow-2xl shadow-amber-500/10 h-[500px] lg:h-[650px] flex flex-col">
              <CardHeader className="pb-3 border-b border-amber-600/30 bg-gradient-to-r from-amber-900/20 to-amber-800/20">
                <CardTitle className="text-amber-300 flex items-center gap-3 text-lg font-semibold">
                  <MessageCircle className="text-amber-500" size={22} />
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
                            {new Date(msg.timestamp).toLocaleTimeString()}
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
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 bg-gradient-to-r from-gray-800 to-gray-900 border border-amber-600/40 p-1 rounded-xl shadow-lg">
                <TabsTrigger value="overview" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-amber-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Overview
                </TabsTrigger>
                <TabsTrigger value="portfolio" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-amber-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Portfolio
                </TabsTrigger>
                <TabsTrigger value="strategy" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-amber-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Strategy
                </TabsTrigger>
                <TabsTrigger value="risk" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-amber-700 data-[state=active]:text-black data-[state=active]:font-semibold data-[state=active]:shadow-lg text-sm font-medium transition-all duration-300">
                  Risk
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
                        R100,000 Goal
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-gradient-to-r from-green-900/40 to-green-800/40 rounded-xl border border-green-600/30">
                          <div className="text-2xl font-bold font-mono text-green-400">
                            {formatCurrency(currentMonthProgress)}
                          </div>
                          <div className="text-sm text-green-300/80">Current Value</div>
                        </div>
                        <div className="text-center p-4 bg-gradient-to-r from-blue-900/40 to-blue-800/40 rounded-xl border border-blue-600/30">
                          <div className="text-2xl font-bold font-mono text-blue-400">
                            {formatCurrency(monthlyTargetState)}
                          </div>
                          <div className="text-sm text-blue-300/80">Monthly Target</div>
                        </div>
                        <div className="text-center p-4 bg-gradient-to-r from-amber-900/40 to-amber-800/40 rounded-xl border border-amber-600/30">
                          <div className="text-2xl font-bold font-mono text-amber-400">
                            {formatCurrency(monthlyTargetState - currentMonthProgress)}
                          </div>
                          <div className="text-sm text-amber-300/80">Remaining</div>
                        </div>
                      </div>
                      <div className="bg-gradient-to-r from-gray-700 to-gray-800 rounded-full h-6 border border-amber-600/30 overflow-hidden shadow-inner">
                        <div 
                          className="h-full bg-gradient-to-r from-amber-500 via-amber-400 to-amber-600 transition-all duration-1000 ease-out shadow-lg relative"
                          style={{width: `${Math.min((currentMonthProgress / monthlyTargetState) * 100, 100)}%`}}
                        >
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold font-mono bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent">
                          {((currentMonthProgress / monthlyTargetState) * 100).toFixed(1)}%
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

            </Tabs>
          </div>
        </div>

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