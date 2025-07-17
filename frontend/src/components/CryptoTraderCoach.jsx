import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { TrendingUp, TrendingDown, Target, AlertTriangle, MessageCircle, DollarSign, BarChart3, Shield } from 'lucide-react';
import { 
  mockPortfolio, 
  mockMarketData, 
  mockDailyStrategy, 
  mockWeeklyTargets, 
  mockRiskMetrics, 
  mockChatHistory, 
  mockNews 
} from './mockData';

const CryptoTraderCoach = () => {
  const [chatMessages, setChatMessages] = useState(mockChatHistory);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = {
      id: chatMessages.length + 1,
      role: 'user',
      message: inputMessage,
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    // Mock AI response
    setTimeout(() => {
      const responses = [
        "Based on current market analysis, I recommend a cautious approach. The RSI indicators suggest potential consolidation.",
        "Your portfolio allocation looks good, but consider taking some profits if BTC reaches R520,000 resistance.",
        "Risk management is key. With current volatility, keep position sizes moderate and maintain stop-losses.",
        "The weekly target is achievable. Focus on the ETH position - it's showing strong momentum patterns."
      ];
      
      const aiResponse = {
        id: chatMessages.length + 2,
        role: 'assistant',
        message: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date().toISOString()
      };
      
      setChatMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                AI Crypto Trading Coach
              </h1>
              <p className="text-purple-300">
                Your path to R100,000 monthly earnings
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-400">
                {formatCurrency(mockPortfolio.totalValue)}
              </div>
              <div className="text-sm text-gray-400">
                Portfolio Value
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column - Chat Interface */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm h-[600px] flex flex-col">
              <CardHeader className="pb-4">
                <CardTitle className="text-white flex items-center gap-2">
                  <MessageCircle className="text-purple-400" />
                  AI Coach Chat
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <ScrollArea className="flex-1 mb-4 max-h-[400px]">
                  <div className="space-y-4">
                    {chatMessages.map((msg) => (
                      <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-lg ${
                          msg.role === 'user' 
                            ? 'bg-purple-600 text-white' 
                            : 'bg-slate-700 text-gray-100'
                        }`}>
                          <p className="text-sm">{msg.message}</p>
                          <p className="text-xs opacity-70 mt-1">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-slate-700 text-gray-100 p-3 rounded-lg">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
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
                    className="bg-slate-700 border-purple-500/20 text-white placeholder-gray-400"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button 
                    onClick={handleSendMessage}
                    disabled={isLoading}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    Send
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Dashboard Content */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="overview" className="space-y-6">
              <TabsList className="grid w-full grid-cols-4 bg-slate-800/50 border-purple-500/20">
                <TabsTrigger value="overview" className="text-white data-[state=active]:bg-purple-600">
                  Overview
                </TabsTrigger>
                <TabsTrigger value="portfolio" className="text-white data-[state=active]:bg-purple-600">
                  Portfolio
                </TabsTrigger>
                <TabsTrigger value="strategy" className="text-white data-[state=active]:bg-purple-600">
                  Strategy
                </TabsTrigger>
                <TabsTrigger value="risk" className="text-white data-[state=active]:bg-purple-600">
                  Risk
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-6">
                
                {/* Monthly Progress */}
                <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Target className="text-green-400" />
                      Monthly Progress to R100,000
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Current Month</span>
                        <span className="text-white">
                          {formatCurrency(mockPortfolio.currentMonthProgress)} / {formatCurrency(mockPortfolio.monthlyTarget)}
                        </span>
                      </div>
                      <Progress 
                        value={(mockPortfolio.currentMonthProgress / mockPortfolio.monthlyTarget) * 100} 
                        className="bg-slate-700"
                      />
                      <div className="text-center text-lg font-semibold text-green-400">
                        {((mockPortfolio.currentMonthProgress / mockPortfolio.monthlyTarget) * 100).toFixed(1)}% Complete
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Market Overview */}
                <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <BarChart3 className="text-blue-400" />
                      Market Overview
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      {mockMarketData.map((crypto) => (
                        <div key={crypto.symbol} className="p-4 bg-slate-700/50 rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <div className="font-semibold text-white">{crypto.symbol}</div>
                              <div className="text-sm text-gray-400">{crypto.name}</div>
                            </div>
                            <div className="text-right">
                              <div className="text-white font-mono">{formatCurrency(crypto.price)}</div>
                              <div className={`text-sm flex items-center gap-1 ${
                                crypto.change24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {crypto.change24h >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                {formatPercentage(crypto.change24h)}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Weekly Targets */}
                <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <DollarSign className="text-yellow-400" />
                      Weekly Cash-Out Targets
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between">
                        <span className="text-gray-400">This Week Target</span>
                        <span className="text-white">{formatCurrency(mockWeeklyTargets.target)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Achieved</span>
                        <span className="text-green-400">{formatCurrency(mockWeeklyTargets.achieved)}</span>
                      </div>
                      <Progress value={mockWeeklyTargets.progress} className="bg-slate-700" />
                      <div className="text-center text-lg font-semibold text-yellow-400">
                        {formatCurrency(mockWeeklyTargets.remaining)} remaining
                      </div>
                    </div>
                  </CardContent>
                </Card>

              </TabsContent>

              {/* Portfolio Tab */}
              <TabsContent value="portfolio" className="space-y-6">
                <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white">Portfolio Holdings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {mockPortfolio.holdings.map((holding) => (
                        <div key={holding.symbol} className="p-4 bg-slate-700/50 rounded-lg">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-semibold text-white">{holding.symbol}</div>
                              <div className="text-sm text-gray-400">{holding.name}</div>
                              <div className="text-sm text-gray-400 mt-1">{holding.amount} coins</div>
                            </div>
                            <div className="text-right">
                              <div className="text-white font-mono">{formatCurrency(holding.value)}</div>
                              <div className={`text-sm ${
                                holding.change24h >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {formatPercentage(holding.change24h)}
                              </div>
                              <div className="text-sm text-gray-400 mt-1">
                                {holding.allocation}% of portfolio
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
              <TabsContent value="strategy" className="space-y-6">
                <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white">Daily Strategy</CardTitle>
                    <Badge variant="outline" className="w-fit text-orange-400 border-orange-400">
                      {mockDailyStrategy.riskLevel} Risk
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-white font-semibold mb-2">Main Recommendation</h4>
                        <p className="text-gray-300">{mockDailyStrategy.mainRecommendation}</p>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                          <div className="text-sm text-gray-400">Expected Return</div>
                          <div className="text-green-400 font-semibold">{mockDailyStrategy.expectedReturn}</div>
                        </div>
                        <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                          <div className="text-sm text-gray-400">Timeframe</div>
                          <div className="text-white font-semibold">{mockDailyStrategy.timeframe}</div>
                        </div>
                        <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                          <div className="text-sm text-gray-400">Target</div>
                          <div className="text-purple-400 font-semibold">{mockDailyStrategy.keyLevels.target}</div>
                        </div>
                      </div>

                      <div>
                        <h4 className="text-white font-semibold mb-2">Recommended Actions</h4>
                        <div className="space-y-2">
                          {mockDailyStrategy.actions.map((action, index) => (
                            <div key={index} className="p-3 bg-slate-700/50 rounded-lg">
                              <div className="flex justify-between items-start">
                                <div>
                                  <Badge className={`${
                                    action.type === 'BUY' ? 'bg-green-600' : 'bg-orange-600'
                                  } text-white`}>
                                    {action.type}
                                  </Badge>
                                  <div className="text-white font-semibold mt-1">{action.asset}</div>
                                  <div className="text-sm text-gray-400">{action.reasoning}</div>
                                </div>
                                <div className="text-right">
                                  <div className="text-white">{action.amount}</div>
                                  <div className="text-sm text-gray-400">@ {action.price}</div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Risk Tab */}
              <TabsContent value="risk" className="space-y-6">
                <Card className="bg-slate-800/50 border-purple-500/20 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Shield className="text-red-400" />
                      Risk Management
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                          <div className="text-2xl font-bold text-red-400">
                            {mockRiskMetrics.riskScore}/10
                          </div>
                          <div className="text-sm text-gray-400">Risk Score</div>
                        </div>
                        <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                          <div className="text-2xl font-bold text-orange-400">
                            {mockRiskMetrics.portfolioVaR}%
                          </div>
                          <div className="text-sm text-gray-400">Value at Risk</div>
                        </div>
                        <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                          <div className="text-2xl font-bold text-green-400">
                            {mockRiskMetrics.sharpeRatio}
                          </div>
                          <div className="text-sm text-gray-400">Sharpe Ratio</div>
                        </div>
                        <div className="text-center p-4 bg-slate-700/50 rounded-lg">
                          <div className="text-2xl font-bold text-purple-400">
                            {mockRiskMetrics.diversificationScore}/10
                          </div>
                          <div className="text-sm text-gray-400">Diversification</div>
                        </div>
                      </div>

                      <div>
                        <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                          <AlertTriangle className="text-yellow-400" />
                          Risk Recommendations
                        </h4>
                        <div className="space-y-2">
                          {mockRiskMetrics.recommendations.map((rec, index) => (
                            <div key={index} className="p-3 bg-slate-700/50 rounded-lg">
                              <p className="text-gray-300">{rec}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CryptoTraderCoach;