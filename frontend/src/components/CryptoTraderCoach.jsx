import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { TrendingUp, TrendingDown, Target, AlertTriangle, MessageCircle, DollarSign, BarChart3, Shield, RefreshCw, Zap, TrendingUpIcon } from 'lucide-react';
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
        loadChatHistory()
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
        message: '⚡ Welcome to your AI Crypto Trading Coach! I\'m here to help you reach your R100,000 monthly target. Ready to dominate the crypto market? 🚀',
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
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      setChatMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        message: '⚠️ Connection issue detected. Rebooting systems... Try again in a moment.',
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
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const monthlyTarget = 100000;
  const currentMonthProgress = portfolio?.total_value || 0;

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Tron-style grid background */}
      <div className="absolute inset-0 bg-black">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,215,0,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,215,0,0.1)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
        <div className="absolute inset-0 bg-gradient-to-br from-amber-900/20 via-black to-rose-900/20"></div>
      </div>
      
      {/* Lightning bolt decorative elements */}
      <div className="absolute top-10 right-10 text-amber-500/30 transform rotate-12">
        <Zap size={60} />
      </div>
      <div className="absolute bottom-20 left-10 text-rose-500/20 transform -rotate-12">
        <Zap size={40} />
      </div>

      <div className="relative z-10 container mx-auto p-4 lg:p-6">
        {/* Header */}
        <div className="mb-6 lg:mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="text-center lg:text-left">
              <h1 className="text-3xl lg:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-yellow-300 to-rose-400 mb-2">
                ⚡ AI CRYPTO COACH ⚡
              </h1>
              <p className="text-amber-300/80 text-sm lg:text-base">
                🎯 TARGET: R100,000 Monthly Domination
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <Button
                onClick={handleRefresh}
                className="bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-700 hover:to-rose-700 text-black font-bold border-2 border-amber-400/50 shadow-lg shadow-amber-500/25 transform transition-all duration-200 hover:scale-105"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                REFRESH
              </Button>
              <div className="text-center lg:text-right">
                <div className="text-xl lg:text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-300">
                  {formatCurrency(currentMonthProgress)}
                </div>
                <div className="text-xs lg:text-sm text-amber-400/60">
                  Portfolio Power
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
          
          {/* Chat Interface - Full width on mobile */}
          <div className="lg:col-span-1 order-2 lg:order-1">
            <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10 h-[500px] lg:h-[600px] flex flex-col">
              <CardHeader className="pb-4 border-b border-amber-500/20">
                <CardTitle className="text-amber-300 flex items-center gap-2 text-lg">
                  <MessageCircle className="text-amber-400" />
                  ⚡ AI COACH TERMINAL
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col p-3 lg:p-4">
                <ScrollArea className="flex-1 mb-4 max-h-[320px] lg:max-h-[400px]">
                  <div className="space-y-3">
                    {chatMessages.map((msg) => (
                      <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] p-3 rounded-lg border ${
                          msg.role === 'user' 
                            ? 'bg-gradient-to-r from-amber-600 to-rose-600 text-black border-amber-400/50 shadow-lg shadow-amber-500/25' 
                            : 'bg-black/60 text-amber-100 border-amber-500/30 shadow-lg shadow-amber-500/10'
                        }`}>
                          <p className="text-sm">{msg.message}</p>
                          <p className="text-xs opacity-60 mt-1">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-black/60 text-amber-100 p-3 rounded-lg border border-amber-500/30">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                            <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </ScrollArea>
                <div className="flex gap-2">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask your AI coach..."
                    className="bg-black/60 border-2 border-amber-500/30 text-amber-100 placeholder-amber-400/60 focus:border-amber-400 focus:ring-amber-400/50"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button 
                    onClick={handleSendMessage}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-700 hover:to-rose-700 text-black font-bold border border-amber-400/50 px-3 lg:px-4"
                  >
                    ⚡
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Dashboard Content - Full width on mobile */}
          <div className="lg:col-span-2 order-1 lg:order-2">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4 lg:space-y-6">
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 bg-black/60 border-2 border-amber-500/30 p-1">
                <TabsTrigger value="overview" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-rose-600 data-[state=active]:text-black data-[state=active]:font-bold text-xs lg:text-sm">
                  📊 OVERVIEW
                </TabsTrigger>
                <TabsTrigger value="portfolio" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-rose-600 data-[state=active]:text-black data-[state=active]:font-bold text-xs lg:text-sm">
                  💰 PORTFOLIO
                </TabsTrigger>
                <TabsTrigger value="strategy" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-rose-600 data-[state=active]:text-black data-[state=active]:font-bold text-xs lg:text-sm">
                  ⚡ STRATEGY
                </TabsTrigger>
                <TabsTrigger value="risk" className="text-amber-300 data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-600 data-[state=active]:to-rose-600 data-[state=active]:text-black data-[state=active]:font-bold text-xs lg:text-sm">
                  🛡️ RISK
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4 lg:space-y-6">
                
                {/* Monthly Progress */}
                <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-500/20">
                    <CardTitle className="text-amber-300 flex items-center gap-2 text-lg">
                      <Target className="text-green-400" />
                      🎯 MONTHLY TARGET PROGRESS
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 lg:p-6">
                    <div className="space-y-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-amber-400/70">Current Month</span>
                        <span className="text-amber-100">
                          {formatCurrency(currentMonthProgress)} / {formatCurrency(monthlyTarget)}
                        </span>
                      </div>
                      <div className="bg-black/60 rounded-full h-4 border border-amber-500/30 overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-1000 ease-out shadow-lg shadow-green-500/50"
                          style={{width: `${Math.min((currentMonthProgress / monthlyTarget) * 100, 100)}%`}}
                        />
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-300">
                          {((currentMonthProgress / monthlyTarget) * 100).toFixed(1)}% COMPLETE
                        </div>
                        <div className="text-amber-400/60 text-sm mt-1">
                          ⚡ {formatCurrency(monthlyTarget - currentMonthProgress)} TO FREEDOM
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Market Overview */}
                <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-500/20">
                    <CardTitle className="text-amber-300 flex items-center gap-2 text-lg">
                      <BarChart3 className="text-blue-400" />
                      📈 MARKET BATTLEFIELD
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 lg:p-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {marketData.map((crypto) => (
                        <div key={crypto.symbol} className="p-4 bg-black/60 rounded-lg border border-amber-500/20 shadow-lg shadow-amber-500/5">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <div className="font-bold text-amber-300 text-lg">{crypto.symbol}</div>
                              <div className="text-sm text-amber-400/70">{crypto.name}</div>
                            </div>
                            <div className="text-right">
                              <div className="text-amber-100 font-mono text-sm lg:text-base">{formatCurrency(crypto.price)}</div>
                              <div className={`text-sm flex items-center gap-1 justify-end ${
                                crypto.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {crypto.change_24h >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                {formatPercentage(crypto.change_24h)}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Weekly Targets */}
                {weeklyTargets && (
                  <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10">
                    <CardHeader className="border-b border-amber-500/20">
                      <CardTitle className="text-amber-300 flex items-center gap-2 text-lg">
                        <DollarSign className="text-yellow-400" />
                        💸 WEEKLY CASH-OUT TARGETS
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 lg:p-6">
                      <div className="space-y-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-amber-400/70">This Week Target</span>
                          <span className="text-amber-100">{formatCurrency(weeklyTargets.target)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-amber-400/70">Achieved</span>
                          <span className="text-green-400">{formatCurrency(weeklyTargets.achieved)}</span>
                        </div>
                        <div className="bg-black/60 rounded-full h-4 border border-amber-500/30 overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-yellow-400 to-amber-500 transition-all duration-1000 ease-out shadow-lg shadow-yellow-500/50"
                            style={{width: `${Math.min(weeklyTargets.progress, 100)}%`}}
                          />
                        </div>
                        <div className="text-center">
                          <div className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-amber-300">
                            {formatCurrency(weeklyTargets.remaining)} REMAINING
                          </div>
                          <div className="text-amber-400/60 text-sm mt-1">
                            ⚡ {weeklyTargets.days_left} DAYS LEFT TO DOMINATE
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

              </TabsContent>

              {/* Portfolio Tab */}
              <TabsContent value="portfolio" className="space-y-4 lg:space-y-6">
                <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10">
                  <CardHeader className="border-b border-amber-500/20">
                    <CardTitle className="text-amber-300 text-lg">💰 PORTFOLIO HOLDINGS</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 lg:p-6">
                    <div className="space-y-4">
                      {portfolio?.holdings?.map((holding) => (
                        <div key={holding.symbol} className="p-4 bg-black/60 rounded-lg border border-amber-500/20 shadow-lg shadow-amber-500/5">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-bold text-amber-300 text-lg">{holding.symbol}</div>
                              <div className="text-sm text-amber-400/70">{holding.name}</div>
                              <div className="text-sm text-amber-400/60 mt-1">{holding.amount} coins</div>
                            </div>
                            <div className="text-right">
                              <div className="text-amber-100 font-mono text-sm lg:text-base">{formatCurrency(holding.value)}</div>
                              <div className={`text-sm ${
                                holding.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {formatPercentage(holding.change_24h)}
                              </div>
                              <div className="text-sm text-amber-400/60 mt-1">
                                {holding.allocation.toFixed(1)}% of portfolio
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Strategy Tab */}
              <TabsContent value="strategy" className="space-y-4 lg:space-y-6">
                {dailyStrategy && (
                  <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10">
                    <CardHeader className="border-b border-amber-500/20">
                      <CardTitle className="text-amber-300 text-lg">⚡ DAILY STRATEGY</CardTitle>
                      <Badge className="w-fit bg-gradient-to-r from-orange-500 to-red-500 text-black border-2 border-orange-400/50">
                        🔥 {dailyStrategy.risk_level} RISK
                      </Badge>
                    </CardHeader>
                    <CardContent className="p-4 lg:p-6">
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-amber-300 font-bold mb-2">📋 MAIN RECOMMENDATION</h4>
                          <p className="text-amber-100 bg-black/40 p-3 rounded-lg border border-amber-500/20">{dailyStrategy.main_recommendation}</p>
                        </div>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-green-500/30">
                            <div className="text-sm text-amber-400/70">Expected Return</div>
                            <div className="text-green-400 font-bold text-lg">{dailyStrategy.expected_return}</div>
                          </div>
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-blue-500/30">
                            <div className="text-sm text-amber-400/70">Timeframe</div>
                            <div className="text-blue-400 font-bold text-lg">{dailyStrategy.timeframe}</div>
                          </div>
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-purple-500/30">
                            <div className="text-sm text-amber-400/70">Target</div>
                            <div className="text-purple-400 font-bold text-lg">{dailyStrategy.key_levels.target}</div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-amber-300 font-bold mb-3">⚡ RECOMMENDED ACTIONS</h4>
                          <div className="space-y-3">
                            {dailyStrategy.actions.map((action, index) => (
                              <div key={index} className="p-4 bg-black/60 rounded-lg border border-amber-500/20">
                                <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-3">
                                  <div>
                                    <Badge className={`${
                                      action.type === 'BUY' ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-orange-500 to-red-500'
                                    } text-black border-2 font-bold`}>
                                      {action.type === 'BUY' ? '🚀 BUY' : '💰 SELL'}
                                    </Badge>
                                    <div className="text-amber-300 font-bold mt-2 text-lg">{action.asset}</div>
                                    <div className="text-sm text-amber-400/70 mt-1">{action.reasoning}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-amber-100 font-mono">{action.amount}</div>
                                    <div className="text-sm text-amber-400/60">@ {action.price}</div>
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
              <TabsContent value="risk" className="space-y-4 lg:space-y-6">
                {riskMetrics && (
                  <Card className="bg-black/80 border-2 border-amber-500/30 backdrop-blur-sm shadow-2xl shadow-amber-500/10">
                    <CardHeader className="border-b border-amber-500/20">
                      <CardTitle className="text-amber-300 flex items-center gap-2 text-lg">
                        <Shield className="text-red-400" />
                        🛡️ RISK MANAGEMENT
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 lg:p-6">
                      <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-red-500/30">
                            <div className="text-2xl font-bold text-red-400">
                              {riskMetrics.risk_score}/10
                            </div>
                            <div className="text-sm text-amber-400/70">Risk Score</div>
                          </div>
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-orange-500/30">
                            <div className="text-2xl font-bold text-orange-400">
                              {riskMetrics.portfolio_var}%
                            </div>
                            <div className="text-sm text-amber-400/70">Value at Risk</div>
                          </div>
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-green-500/30">
                            <div className="text-2xl font-bold text-green-400">
                              {riskMetrics.sharpe_ratio}
                            </div>
                            <div className="text-sm text-amber-400/70">Sharpe Ratio</div>
                          </div>
                          <div className="text-center p-4 bg-black/60 rounded-lg border border-purple-500/30">
                            <div className="text-2xl font-bold text-purple-400">
                              {riskMetrics.diversification_score}/10
                            </div>
                            <div className="text-sm text-amber-400/70">Diversification</div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-amber-300 font-bold mb-3 flex items-center gap-2">
                            <AlertTriangle className="text-yellow-400" />
                            ⚠️ RISK RECOMMENDATIONS
                          </h4>
                          <div className="space-y-3">
                            {riskMetrics.recommendations.map((rec, index) => (
                              <div key={index} className="p-4 bg-black/60 rounded-lg border border-amber-500/20">
                                <p className="text-amber-100">⚡ {rec}</p>
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
      </div>
    </div>
  );
};

export default CryptoTraderCoach;