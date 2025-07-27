// Mock data for crypto trading coach app
export const mockPortfolio = {
  totalValue: 45670.50,
  currency: 'ZAR',
  monthlyTarget: 100000,
  currentMonthProgress: 45670.50,
  holdings: [
    {
      symbol: 'BTC',
      name: 'Bitcoin',
      amount: 0.5234,
      value: 25400.00,
      change24h: 3.2,
      allocation: 55.6
    },
    {
      symbol: 'ETH',
      name: 'Ethereum',
      amount: 8.2341,
      value: 12890.30,
      change24h: -1.8,
      allocation: 28.2
    },
    {
      symbol: 'LTC',
      name: 'Litecoin',
      amount: 42.12,
      value: 4380.20,
      change24h: 2.1,
      allocation: 9.6
    },
    {
      symbol: 'XRP',
      name: 'Ripple',
      amount: 1250.45,
      value: 3000.00,
      change24h: -0.5,
      allocation: 6.6
    }
  ]
};

export const mockMarketData = [
  {
    symbol: 'BTC',
    name: 'Bitcoin',
    price: 485000.00,
    change24h: 3.2,
    volume: 28500000000,
    marketCap: 9450000000000,
    trend: 'up'
  },
  {
    symbol: 'ETH',
    name: 'Ethereum',
    price: 15650.00,
    change24h: -1.8,
    volume: 15200000000,
    marketCap: 1890000000000,
    trend: 'down'
  },
  {
    symbol: 'LTC',
    name: 'Litecoin',
    price: 104.00,
    change24h: 2.1,
    volume: 2100000000,
    marketCap: 7800000000,
    trend: 'up'
  },
  {
    symbol: 'XRP',
    name: 'Ripple',
    price: 2.40,
    change24h: -0.5,
    volume: 1800000000,
    marketCap: 135000000000,
    trend: 'down'
  }
];

export const mockDailyStrategy = {
  date: '2025-07-17',
  mainRecommendation: 'BTC showing strong support at R480,000. Consider accumulating on dips below R475,000',
  riskLevel: 'Medium',
  expectedReturn: '5-8%',
  timeframe: '1-3 days',
  keyLevels: {
    support: 'R475,000',
    resistance: 'R520,000',
    target: 'R510,000'
  },
  actions: [
    {
      type: 'BUY',
      asset: 'BTC',
      amount: 'R10,000',
      price: 'R475,000 - R480,000',
      reasoning: 'Strong support level with high volume'
    },
    {
      type: 'TAKE_PROFIT',
      asset: 'ETH',
      amount: '30%',
      price: 'R16,200',
      reasoning: 'Approaching resistance, secure profits'
    }
  ]
};

export const mockWeeklyTargets = {
  weekOf: '2025-07-14',
  target: 25000,
  achieved: 18750,
  remaining: 6250,
  daysLeft: 3,
  dailyRequired: 2083.33,
  progress: 75,
  milestones: [
    { day: 'Monday', target: 3571, achieved: 4200, status: 'exceeded' },
    { day: 'Tuesday', target: 3571, achieved: 2890, status: 'below' },
    { day: 'Wednesday', target: 3571, achieved: 3950, status: 'exceeded' },
    { day: 'Thursday', target: 3571, achieved: 4210, status: 'exceeded' },
    { day: 'Friday', target: 3571, achieved: 3500, status: 'pending' },
    { day: 'Saturday', target: 3571, achieved: 0, status: 'pending' },
    { day: 'Sunday', target: 3571, achieved: 0, status: 'pending' }
  ]
};

export const mockRiskMetrics = {
  riskScore: 6.2,
  maxRisk: 10,
  portfolioVaR: 8.5, // Value at Risk percentage
  sharpeRatio: 1.8,
  maxDrawdown: 12.3,
  diversificationScore: 7.5,
  recommendations: [
    'Consider reducing BTC allocation to below 60%',
    'Add stablecoin allocation for better risk management',
    'Set stop-loss at 5% below current portfolio value'
  ]
};

export const mockChatHistory = [
  {
    id: 1,
    role: 'assistant',
    message: 'Good morning! I\'ve analyzed your portfolio and market conditions. BTC is showing strong momentum today. Ready to discuss your trading strategy?',
    timestamp: '2025-07-17T08:00:00Z'
  },
  {
    id: 2,
    role: 'user',
    message: 'What\'s your take on the current BTC price action?',
    timestamp: '2025-07-17T08:02:00Z'
  },
  {
    id: 3,
    role: 'assistant',
    message: 'BTC is consolidating above R480,000 with strong volume. The 4-hour RSI shows healthy correction from overbought levels. I recommend watching for a break above R485,000 for continuation or accumulating on any dip to R475,000 support.',
    timestamp: '2025-07-17T08:02:30Z'
  }
];

export const mockNews = [
  {
    id: 1,
    title: 'Bitcoin ETF Sees Record Inflows',
    summary: 'Institutional investors pour R2.5 billion into Bitcoin ETFs this week',
    impact: 'bullish',
    timestamp: '2025-07-17T07:30:00Z'
  },
  {
    id: 2,
    title: 'Ethereum Upgrade Scheduled',
    summary: 'Major network upgrade expected to improve transaction speeds by 40%',
    impact: 'bullish',
    timestamp: '2025-07-17T06:45:00Z'
  },
  {
    id: 3,
    title: 'Regulatory Clarity in South Africa',
    summary: 'SARB announces clearer guidelines for crypto trading and taxation',
    impact: 'neutral',
    timestamp: '2025-07-17T05:15:00Z'
  }
];