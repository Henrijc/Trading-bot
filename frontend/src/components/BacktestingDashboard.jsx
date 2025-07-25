import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { AlertTriangle, TrendingUp, TrendingDown, BarChart3, Play, RefreshCw, Target } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BacktestingDashboard = () => {
  const [backtestResults, setBacktestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/ZAR');
  const [simulationMode, setSimulationMode] = useState(false);
  const [autoBacktest, setAutoBacktest] = useState(false);
  const [backtestConfig, setBacktestConfig] = useState({
    symbol: 'BTC/ZAR',
    timeframe: '1h',
    days_back: 30,
    initial_capital: 154273.71,
    risk_per_trade: 0.04,
    monthly_target: 8000,
    xrp_hold_amount: 1000
  });
  const [simulationConfig, setSimulationConfig] = useState({
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    timeframe: '1h',
    enable_auto_backtest: false,
    backtest_frequency: 'daily'
  });
  const [multiPairResults, setMultiPairResults] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);

  const symbols = ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR'];

  const runAutoBacktest = async () => {
    setAutoBacktest(true);
    try {
      const response = await axios.post(`${API}/backtest/schedule`);
      console.log('Auto backtest scheduled:', response.data);
      
      // Run multi-pair backtest automatically
      setTimeout(() => {
        runMultiPairBacktest();
      }, 2000);
      
    } catch (error) {
      console.error('Auto backtest error:', error);
    } finally {
      setAutoBacktest(false);
    }
  };

  const runSimulationBacktest = async () => {
    setIsRunning(true);
    try {
      // Convert dates to days_back format
      const startDate = new Date(simulationConfig.start_date);
      const endDate = new Date(simulationConfig.end_date);
      const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
      
      const response = await axios.post(`${API}/backtest/run`, {
        ...backtestConfig,
        timeframe: simulationConfig.timeframe,
        days_back: daysDiff
      });
      
      setBacktestResults(response.data);
    } catch (error) {
      console.error('Simulation backtest error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const runSingleBacktest = async () => {
    setIsRunning(true);
    try {
      const response = await axios.post(`${API}/backtest/run`, backtestConfig);
      setBacktestResults(response.data);
    } catch (error) {
      console.error('Backtest error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const runMultiPairBacktest = async () => {
    setIsRunning(true);
    try {
      const response = await axios.post(`${API}/backtest/multi-pair`, {
        symbols: ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR'],
        timeframe: '1h',
        days_back: 30,
        initial_capital: 154273.71,
        risk_per_trade: 0.04,
        monthly_target: 8000,
        xrp_hold_amount: 1000
      });
      setMultiPairResults(response.data);
    } catch (error) {
      console.error('Multi-pair backtest error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const getHistoricalData = async (symbol) => {
    try {
      const response = await axios.post(`${API}/backtest/historical-data`, {
        symbol,
        timeframe: '1h',
        days_back: 7
      });
      setHistoricalData(response.data);
    } catch (error) {
      console.error('Historical data error:', error);
    }
  };

  useEffect(() => {
    getHistoricalData(selectedSymbol);
  }, [selectedSymbol]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'LOW': return 'text-green-500';
      case 'MEDIUM': return 'text-yellow-500';
      case 'HIGH': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getPerformanceColor = (percentage) => {
    if (percentage > 0) return 'text-green-500';
    if (percentage < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-cyan-300">Strategy Backtesting</h2>
          <p className="text-gray-400">Test your trading strategies with historical data</p>
        </div>
        <div className="flex gap-3">
          <Button 
            onClick={simulationMode ? runSimulationBacktest : runSingleBacktest}
            disabled={isRunning}
            className="bg-cyan-600 hover:bg-cyan-700"
          >
            {isRunning ? <RefreshCw className="animate-spin mr-2" size={16} /> : <Play className="mr-2" size={16} />}
            {simulationMode ? 'Run Simulation' : 'Run Single Test'}
          </Button>
          <Button 
            onClick={runMultiPairBacktest}
            disabled={isRunning}
            variant="outline"
            className="border-cyan-600 text-cyan-300 hover:bg-cyan-600/10"
          >
            {isRunning ? <RefreshCw className="animate-spin mr-2" size={16} /> : <BarChart3 className="mr-2" size={16} />}
            Multi-Pair Test
          </Button>
          <Button 
            onClick={runAutoBacktest}
            disabled={autoBacktest}
            variant="outline"
            className="border-green-600 text-green-300 hover:bg-green-600/10"
          >
            {autoBacktest ? <RefreshCw className="animate-spin mr-2" size={16} /> : <RefreshCw className="mr-2" size={16} />}
            Auto Backtest
          </Button>
        </div>
      </div>

      {/* Configuration Panel */}
      <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-cyan-600/40">
        <CardHeader>
          <CardTitle className="text-cyan-300 flex items-center gap-2">
            <Target size={20} />
            Backtest Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Trading Pair</label>
              <select 
                value={backtestConfig.symbol}
                onChange={(e) => {
                  setBacktestConfig({...backtestConfig, symbol: e.target.value});
                  setSelectedSymbol(e.target.value);
                }}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                {symbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Days Back</label>
              <input 
                type="number"
                value={backtestConfig.days_back}
                onChange={(e) => setBacktestConfig({...backtestConfig, days_back: parseInt(e.target.value)})}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                min="7"
                max="365"
                disabled={simulationMode}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Risk per Trade (%)</label>
              <input 
                type="number"
                value={backtestConfig.risk_per_trade * 100}
                onChange={(e) => setBacktestConfig({...backtestConfig, risk_per_trade: parseFloat(e.target.value) / 100})}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                min="1"
                max="10"
                step="0.5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Mode</label>
              <button
                onClick={() => setSimulationMode(!simulationMode)}
                className={`w-full p-2 rounded text-white font-medium ${
                  simulationMode 
                    ? 'bg-cyan-600 hover:bg-cyan-700' 
                    : 'bg-gray-600 hover:bg-gray-700'
                }`}
              >
                {simulationMode ? 'Simulation' : 'Standard'}
              </button>
            </div>
          </div>

          {/* Simulation Mode Controls */}
          {simulationMode && (
            <div className="border-t border-gray-600 pt-4">
              <h4 className="text-lg font-semibold text-cyan-300 mb-3">Simulation Parameters</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Start Date</label>
                  <input 
                    type="date"
                    value={simulationConfig.start_date}
                    onChange={(e) => setSimulationConfig({...simulationConfig, start_date: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">End Date</label>
                  <input 
                    type="date"
                    value={simulationConfig.end_date}
                    onChange={(e) => setSimulationConfig({...simulationConfig, end_date: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Timeframe</label>
                  <select 
                    value={simulationConfig.timeframe}
                    onChange={(e) => setSimulationConfig({...simulationConfig, timeframe: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                  >
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="1d">1 Day</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Historical Data Overview */}
      {historicalData && (
        <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-cyan-600/40">
          <CardHeader>
            <CardTitle className="text-cyan-300">Historical Data - {selectedSymbol}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{historicalData.data_points}</div>
                <div className="text-sm text-gray-400">Data Points</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-cyan-300">{formatCurrency(historicalData.latest_price)}</div>
                <div className="text-sm text-gray-400">Latest Price</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{formatCurrency(historicalData.price_range.max)}</div>
                <div className="text-sm text-gray-400">Period High</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">{formatCurrency(historicalData.price_range.min)}</div>
                <div className="text-sm text-gray-400">Period Low</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Single Backtest Results */}
      {backtestResults && (
        <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-cyan-600/40">
          <CardHeader>
            <CardTitle className="text-cyan-300 flex items-center gap-2">
              <TrendingUp size={20} />
              Backtest Results - {backtestResults.symbol}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gray-700/50 rounded">
                <div className={`text-2xl font-bold ${getPerformanceColor(backtestResults.total_profit)}`}>
                  {formatCurrency(backtestResults.total_profit)}
                </div>
                <div className="text-sm text-gray-400">Total Profit</div>
                <div className={`text-xs ${getPerformanceColor(backtestResults.total_percentage)}`}>
                  {backtestResults.total_percentage.toFixed(2)}%
                </div>
              </div>
              <div className="text-center p-4 bg-gray-700/50 rounded">
                <div className="text-2xl font-bold text-white">{backtestResults.total_trades}</div>
                <div className="text-sm text-gray-400">Total Trades</div>
                <div className="text-xs text-amber-400">{backtestResults.win_rate.toFixed(1)}% Win Rate</div>
              </div>
              <div className="text-center p-4 bg-gray-700/50 rounded">
                <div className={`text-2xl font-bold ${getPerformanceColor(backtestResults.monthly_profit)}`}>
                  {formatCurrency(backtestResults.monthly_profit)}
                </div>
                <div className="text-sm text-gray-400">Monthly Profit</div>
                <div className="text-xs text-cyan-400">Target: R8,000</div>
              </div>
              <div className="text-center p-4 bg-gray-700/50 rounded">
                <div className={`text-2xl font-bold ${getRiskColor(backtestResults.risk_level)}`}>
                  {backtestResults.risk_level}
                </div>
                <div className="text-sm text-gray-400">Risk Level</div>
                <div className="text-xs text-red-400">{backtestResults.max_drawdown.toFixed(2)}% Max DD</div>
              </div>
            </div>

            {/* Target Achievement */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-300">Monthly Target Achievement</span>
                <span className={`text-sm font-bold ${getPerformanceColor(backtestResults.target_achievement)}`}>
                  {backtestResults.target_achievement.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={Math.min(Math.max(backtestResults.target_achievement, 0), 200)} 
                className="h-3"
              />
            </div>

            {/* Recent Trades */}
            {backtestResults.trades_summary && backtestResults.trades_summary.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-cyan-300 mb-3">Recent Trades</h4>
                <div className="space-y-2">
                  {backtestResults.trades_summary.slice(-5).map((trade, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
                      <div className="flex items-center gap-3">
                        <Badge variant={trade.profit_loss > 0 ? "default" : "destructive"}>
                          {trade.profit_loss > 0 ? "WIN" : "LOSS"}
                        </Badge>
                        <span className="text-sm text-gray-300">{trade.entry_time}</span>
                        <span className="text-sm text-gray-400">{trade.pair}</span>
                      </div>
                      <div className="text-right">
                        <div className={`font-bold ${getPerformanceColor(trade.profit_loss)}`}>
                          {formatCurrency(trade.profit_loss)}
                        </div>
                        <div className={`text-xs ${getPerformanceColor(trade.profit_percentage)}`}>
                          {trade.profit_percentage.toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Multi-Pair Comparison */}
      {multiPairResults && multiPairResults.success && (
        <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-cyan-600/40">
          <CardHeader>
            <CardTitle className="text-cyan-300 flex items-center gap-2">
              <BarChart3 size={20} />
              Multi-Pair Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-6 text-center">
              <div className="text-3xl font-bold text-cyan-300 mb-2">
                {multiPairResults.best_performer}
              </div>
              <div className="text-sm text-gray-400">Best Performing Pair</div>
              <div className="text-lg font-semibold text-green-400">
                {formatCurrency(multiPairResults.summary.best_total_profit)}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(multiPairResults.comparison).map(([symbol, data]) => (
                <div key={symbol} className="p-4 bg-gray-700/30 rounded">
                  <div className="text-center mb-3">
                    <div className="text-lg font-bold text-white">{symbol}</div>
                    <div className={`text-2xl font-bold ${getPerformanceColor(data.total_profit)}`}>
                      {formatCurrency(data.total_profit)}
                    </div>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Monthly:</span>
                      <span className={getPerformanceColor(data.monthly_profit)}>
                        {formatCurrency(data.monthly_profit)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Win Rate:</span>
                      <span className="text-white">{data.win_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className={getPerformanceColor(data.target_achievement)}>
                        {data.target_achievement.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Strategy Information */}
      <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-cyan-600/40">
        <CardHeader>
          <CardTitle className="text-cyan-300 flex items-center gap-2">
            <AlertTriangle size={20} />
            Strategy Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-white mb-3">RSI + Bollinger Bands Strategy</h4>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>• RSI Period: 14 (Oversold: 30, Overbought: 70)</li>
                <li>• Bollinger Bands: 20 period, 2 std dev</li>
                <li>• Entry: Both indicators align for buy/sell</li>
                <li>• Stop Loss: 4% trailing stop</li>
                <li>• Position Size: Risk-based (4% max risk per trade)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-3">Risk Management</h4>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>• Max Risk per Trade: 4% of capital</li>
                <li>• XRP Long-term Hold: 1,000 XRP reserved</li>
                <li>• Monthly Target: R8,000 profit</li>
                <li>• Max Open Positions: 3</li>
                <li>• Capital Preservation: Conservative approach</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BacktestingDashboard;