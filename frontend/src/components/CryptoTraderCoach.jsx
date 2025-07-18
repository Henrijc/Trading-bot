import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { TrendingUp, TrendingDown, Target, AlertTriangle, MessageCircle, DollarSign, BarChart3, Shield, RefreshCw } from 'lucide-react';
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
        message: 'Welcome to your AI Trading Coach. I am here to assist you in achieving your monthly target of R100,000. How may I help you today?',
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

  const monthlyTarget = 100000;
  const currentMonthProgress = portfolio?.total_value || 0;

  return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto p-4 lg:p-6">
        {/* Header */}
        <div className="mb-6 lg:mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-amber-900/30 pb-4">
            <div>
              <h1 className="text-2xl lg:text-3xl font-light text-amber-400 mb-1">
                AI Trading Coach
              </h1>
              <p className="text-amber-600/70 text-sm">
                Monthly Target: R100,000
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <Button
                onClick={handleRefresh}
                variant="outline"
                className="border-amber-800/50 text-amber-400 hover:bg-amber-900/20 hover:border-amber-700"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <div className="text-right">
                <div className="text-xl lg:text-2xl font-mono text-amber-300">
                  {formatCurrency(currentMonthProgress)}
                </div>
                <div className="text-xs lg:text-sm text-amber-600/60">
                  Portfolio Value
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
          
          {/* Chat Interface */}
          <div className="lg:col-span-1 order-2 lg:order-1">
            <Card className="bg-black border border-amber-900/40 h-[500px] lg:h-[600px] flex flex-col">
              <CardHeader className="pb-3 border-b border-amber-900/30">
                <CardTitle className="text-amber-400 flex items-center gap-2 text-lg font-normal">
                  <MessageCircle className="text-amber-500" size={20} />
                  AI Trading Assistant
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col p-4">
                <ScrollArea className="flex-1 mb-4 max-h-[320px] lg:max-h-[400px]">
                  <div className="space-y-3">
                    {chatMessages.map((msg) => (
                      <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] p-3 rounded border ${
                          msg.role === 'user' 
                            ? 'bg-amber-900/20 text-amber-100 border-amber-800/50' 
                            : 'bg-gray-900/60 text-gray-100 border-gray-700/50'
                        }`}>
                          <p className="text-sm leading-relaxed">{msg.message}</p>
                          <p className="text-xs opacity-60 mt-2 font-mono">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-900/60 text-gray-100 p-3 rounded border border-gray-700/50">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div>
                            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
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
                    placeholder="Enter your query..."
                    className="bg-gray-900/50 border-amber-900/40 text-amber-100 placeholder-amber-600/50 focus:border-amber-700"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button 
                    onClick={handleSendMessage}
                    disabled={isLoading}
                    className="bg-amber-900/60 hover:bg-amber-800/60 text-amber-100 border border-amber-800/50"
                  >
                    Send
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Dashboard Content */}
          <div className="lg:col-span-2 order-1 lg:order-2">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4 lg:space-y-6">
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 bg-black border border-amber-900/40">
                <TabsTrigger value="overview" className="text-amber-400 data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-300 text-xs lg:text-sm font-normal">
                  Overview
                </TabsTrigger>
                <TabsTrigger value="portfolio" className="text-amber-400 data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-300 text-xs lg:text-sm font-normal">
                  Portfolio
                </TabsTrigger>
                <TabsTrigger value="strategy" className="text-amber-400 data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-300 text-xs lg:text-sm font-normal">
                  Strategy
                </TabsTrigger>
                <TabsTrigger value="risk" className="text-amber-400 data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-300 text-xs lg:text-sm font-normal">
                  Risk
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4 lg:space-y-6">
                
                {/* Monthly Progress */}
                <Card className="bg-black border border-amber-900/40">
                  <CardHeader className="border-b border-amber-900/30">
                    <CardTitle className="text-amber-400 flex items-center gap-2 text-lg font-normal">
                      <Target className="text-amber-500" size={20} />
                      Monthly Progress
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 lg:p-6">
                    <div className="space-y-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-amber-500/70">Current Month</span>
                        <span className="text-amber-200 font-mono">
                          {formatCurrency(currentMonthProgress)} / {formatCurrency(monthlyTarget)}
                        </span>
                      </div>
                      <div className="bg-gray-900/60 rounded h-2 border border-amber-900/30">
                        <div 
                          className="h-full bg-gradient-to-r from-amber-600 to-amber-500 rounded transition-all duration-500"
                          style={{width: `${Math.min((currentMonthProgress / monthlyTarget) * 100, 100)}%`}}
                        />
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-mono text-amber-300">
                          {((currentMonthProgress / monthlyTarget) * 100).toFixed(1)}%
                        </div>
                        <div className="text-amber-500/60 text-sm mt-1">
                          Remaining: {formatCurrency(monthlyTarget - currentMonthProgress)}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Market Overview */}
                <Card className="bg-black border border-amber-900/40">
                  <CardHeader className="border-b border-amber-900/30">
                    <CardTitle className="text-amber-400 flex items-center gap-2 text-lg font-normal">
                      <BarChart3 className="text-amber-500" size={20} />
                      Market Overview
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 lg:p-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {marketData.map((crypto) => (
                        <div key={crypto.symbol} className="p-4 bg-gray-900/40 rounded border border-amber-900/20">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-mono text-amber-300 text-base">{crypto.symbol}</div>
                              <div className="text-sm text-amber-500/70">{crypto.name}</div>
                            </div>
                            <div className="text-right">
                              <div className="text-amber-200 font-mono text-sm">{formatCurrency(crypto.price)}</div>
                              <div className={`text-sm flex items-center gap-1 justify-end ${
                                crypto.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {crypto.change_24h >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
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
                  <Card className="bg-black border border-amber-900/40">
                    <CardHeader className="border-b border-amber-900/30">
                      <CardTitle className="text-amber-400 flex items-center gap-2 text-lg font-normal">
                        <DollarSign className="text-amber-500" size={20} />
                        Weekly Targets
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 lg:p-6">
                      <div className="space-y-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-amber-500/70">Target</span>
                          <span className="text-amber-200 font-mono">{formatCurrency(weeklyTargets.target)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-amber-500/70">Achieved</span>
                          <span className="text-green-400 font-mono">{formatCurrency(weeklyTargets.achieved)}</span>
                        </div>
                        <div className="bg-gray-900/60 rounded h-2 border border-amber-900/30">
                          <div 
                            className="h-full bg-gradient-to-r from-amber-600 to-amber-500 rounded transition-all duration-500"
                            style={{width: `${Math.min(weeklyTargets.progress, 100)}%`}}
                          />
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-mono text-amber-300">
                            {formatCurrency(weeklyTargets.remaining)}
                          </div>
                          <div className="text-amber-500/60 text-sm mt-1">
                            Remaining ({weeklyTargets.days_left} days)
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

              </TabsContent>

              {/* Portfolio Tab */}
              <TabsContent value="portfolio" className="space-y-4 lg:space-y-6">
                <Card className="bg-black border border-amber-900/40">
                  <CardHeader className="border-b border-amber-900/30">
                    <CardTitle className="text-amber-400 text-lg font-normal">Portfolio Holdings</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 lg:p-6">
                    <div className="space-y-4">
                      {portfolio?.holdings?.map((holding) => (
                        <div key={holding.symbol} className="p-4 bg-gray-900/40 rounded border border-amber-900/20">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-mono text-amber-300 text-base">{holding.symbol}</div>
                              <div className="text-sm text-amber-500/70">{holding.name}</div>
                              <div className="text-sm text-amber-500/50 mt-1 font-mono">{holding.amount.toFixed(6)} units</div>
                            </div>
                            <div className="text-right">
                              <div className="text-amber-200 font-mono text-sm">{formatCurrency(holding.value)}</div>
                              <div className={`text-sm font-mono ${
                                holding.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {formatPercentage(holding.change_24h)}
                              </div>
                              <div className="text-sm text-amber-500/50 mt-1 font-mono">
                                {holding.allocation.toFixed(1)}%
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
                  <Card className="bg-black border border-amber-900/40">
                    <CardHeader className="border-b border-amber-900/30">
                      <CardTitle className="text-amber-400 text-lg font-normal">Daily Strategy</CardTitle>
                      <Badge className="w-fit bg-amber-900/30 text-amber-300 border border-amber-800/50">
                        {dailyStrategy.risk_level} Risk
                      </Badge>
                    </CardHeader>
                    <CardContent className="p-4 lg:p-6">
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-amber-400 font-normal mb-2">Primary Recommendation</h4>
                          <p className="text-amber-100 bg-gray-900/40 p-3 rounded border border-amber-900/20 leading-relaxed">
                            {dailyStrategy.main_recommendation}
                          </p>
                        </div>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                          <div className="text-center p-3 bg-gray-900/40 rounded border border-green-800/30">
                            <div className="text-sm text-amber-500/70">Expected Return</div>
                            <div className="text-green-400 font-mono text-base">{dailyStrategy.expected_return}</div>
                          </div>
                          <div className="text-center p-3 bg-gray-900/40 rounded border border-blue-800/30">
                            <div className="text-sm text-amber-500/70">Timeframe</div>
                            <div className="text-blue-400 font-mono text-base">{dailyStrategy.timeframe}</div>
                          </div>
                          <div className="text-center p-3 bg-gray-900/40 rounded border border-purple-800/30">
                            <div className="text-sm text-amber-500/70">Target</div>
                            <div className="text-purple-400 font-mono text-base">{dailyStrategy.key_levels.target}</div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-amber-400 font-normal mb-3">Recommended Actions</h4>
                          <div className="space-y-3">
                            {dailyStrategy.actions.map((action, index) => (
                              <div key={index} className="p-4 bg-gray-900/40 rounded border border-amber-900/20">
                                <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-3">
                                  <div>
                                    <Badge className={`${
                                      action.type === 'BUY' ? 'bg-green-900/40 text-green-300 border-green-800/50' : 'bg-red-900/40 text-red-300 border-red-800/50'
                                    } font-mono`}>
                                      {action.type}
                                    </Badge>
                                    <div className="text-amber-300 font-mono mt-2">{action.asset}</div>
                                    <div className="text-sm text-amber-500/70 mt-1 leading-relaxed">{action.reasoning}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-amber-200 font-mono text-sm">{action.amount}</div>
                                    <div className="text-sm text-amber-500/60 font-mono">@ {action.price}</div>
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
                  <Card className="bg-black border border-amber-900/40">
                    <CardHeader className="border-b border-amber-900/30">
                      <CardTitle className="text-amber-400 flex items-center gap-2 text-lg font-normal">
                        <Shield className="text-amber-500" size={20} />
                        Risk Management
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 lg:p-6">
                      <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center p-4 bg-gray-900/40 rounded border border-red-800/30">
                            <div className="text-xl font-mono text-red-400">
                              {riskMetrics.risk_score}/10
                            </div>
                            <div className="text-sm text-amber-500/70">Risk Score</div>
                          </div>
                          <div className="text-center p-4 bg-gray-900/40 rounded border border-orange-800/30">
                            <div className="text-xl font-mono text-orange-400">
                              {riskMetrics.portfolio_var}%
                            </div>
                            <div className="text-sm text-amber-500/70">Value at Risk</div>
                          </div>
                          <div className="text-center p-4 bg-gray-900/40 rounded border border-green-800/30">
                            <div className="text-xl font-mono text-green-400">
                              {riskMetrics.sharpe_ratio}
                            </div>
                            <div className="text-sm text-amber-500/70">Sharpe Ratio</div>
                          </div>
                          <div className="text-center p-4 bg-gray-900/40 rounded border border-purple-800/30">
                            <div className="text-xl font-mono text-purple-400">
                              {riskMetrics.diversification_score}/10
                            </div>
                            <div className="text-sm text-amber-500/70">Diversification</div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-amber-400 font-normal mb-3 flex items-center gap-2">
                            <AlertTriangle className="text-amber-500" size={18} />
                            Risk Recommendations
                          </h4>
                          <div className="space-y-3">
                            {riskMetrics.recommendations.map((rec, index) => (
                              <div key={index} className="p-3 bg-gray-900/40 rounded border border-amber-900/20">
                                <p className="text-amber-100 leading-relaxed">{rec}</p>
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