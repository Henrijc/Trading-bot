Project: AI-Driven Portfolio Management System
Last Updated: Saturday, July 26, 2025 - 4:58 PM SAST
1. Core Objective & Philosophy
The goal is to evolve the current application from a passive monitoring dashboard into an active, AI-driven trading system. This system will manage a live Luno portfolio with the primary objective of achieving user-defined performance targets.
The core philosophy is a separation of concerns:
* Freqtrade/FreqAI (The Trader): A specialized service that runs 24/7. Its sole job is to analyze market data, generate predictive signals (buy/sell/hold), and execute trades on the Luno exchange.
* Backend Orchestrator (The Brain): A central service that monitors the overall portfolio health, understands the user's high-level targets, and uses signals from "The Trader" to make strategic decisions.
* Frontend Dashboard (The Cockpit): The user's interface to monitor the system, set targets, and view performance.
2. System Architecture Blueprint
The application will be re-architected into three distinct, communicating components.
Component A: Frontend Dashboard (React)
* Responsibilities:
   * Target Management: Allow the user to set, view, and update performance targets (e.g., monthly profit goal).
   * Portfolio Monitoring: Display real-time portfolio value, asset allocation, and performance metrics fetched from the Backend Orchestrator.
   * Bot Control & Status: Display the live status of the Freqtrade bot (running, stopped, profit/loss of current trades). Provide controls to start/stop the bot via the Orchestrator.
   * Trade History: Show a log of all trades executed by the system.
Component B: Backend Orchestrator (Python/FastAPI)
* This is the central nervous system. It does not contain the trading strategy logic itself but manages the overall operation.
* Key Services:
   * LunoService: Communicates directly with the Luno API to get the current, real-world state of the portfolio (balances, asset values).
   * TargetManagerService: A new service to store and retrieve the user's performance targets from the database.
   * FreqtradeAPIService: A new, critical service that communicates with the Freqtrade instance via its REST API. It will be responsible for:
      * Starting/stopping the Freqtrade bot.
      * Querying the status of the bot (running, trades open, profit).
      * Fetching trade signals or predictions from FreqAI.
   * DecisionEngine: The core logic that combines information to make strategic decisions. Example Logic: "Check the portfolio value from LunoService. We are 20% below our monthly target. Now, ask FreqtradeAPIService for its latest signal. If the signal is a high-confidence BUY, approve the trade. If we are 50% above our target, instruct Freqtrade to take partial profits, even if its signal is to hold."
* API Endpoints:
   * /api/portfolio/status: Provides the frontend with live data from the LunoService.
   * /api/targets: CRUD endpoints for managing user targets.
   * /api/bot/start, /api/bot/stop, /api/bot/status: Endpoints that use the FreqtradeAPIService to control and monitor the trading bot.
Component C: Freqtrade Instance (with FreqAI)
* This is a separate, dedicated process managed by Supervisor.
* Responsibilities:
   * Exchange Connection: Maintains a persistent connection to the Luno exchange.
   * Feature Engineering: Uses a Python strategy file (luno_strategy.py) to calculate technical indicators and features from market data.
   * AI Model Prediction: Feeds the engineered features into a trained FreqAI model (e.g., LightGBM, XGBoost) to get a predictive output (e.g., "probability of 2% price increase in the next hour").
   * Trade Execution: Places buy/sell orders on Luno based on the AI's predictions and the rules defined in the strategy.
* Configuration (config.json):
   * Must have the Luno API keys and the desired trading pairs configured.
   * Crucially, the REST API must be enabled so the Backend Orchestrator can communicate with it.
   * Defines stake amount, stop-loss, and other core trading parameters.
3. Phased Implementation Plan
Phase 1: Establish the Freqtrade Trader
1. Standalone Setup: Install and configure a standard Freqtrade instance completely separate from the existing application.
2. Luno Connection: Configure it with the Luno API keys and ensure it can pull market data for BTC/ZAR, ETH/ZAR, etc.
3. Run a Simple Strategy: Use a basic, non-AI strategy (e.g., a simple EMA cross) to confirm that the bot can execute trades correctly in dry-run mode on Luno. This validates the core connection.
Phase 2: Develop FreqAI Intelligence
1. Data Acquisition: Download a substantial amount of historical candle data for the Luno pairs you intend to trade.
2. Feature Engineering: Create a new strategy file (luno_freqai_strategy.py). Define the indicators and data points (features) you believe are predictive. Start simple.
3. Model Training & Backtesting: Use FreqAI to train a machine learning model on the historical data. Backtest rigorously to validate that the model has predictive power. The goal is to find a model that is consistently profitable in backtests.
Phase 3: Build the Backend Orchestrator
1. Develop Services: Implement the LunoService and FreqtradeAPIService in the existing FastAPI backend.
2. API Endpoints: Create the new API endpoints (/api/bot/..., /api/targets/...) that the frontend will use.
3. Decision Logic: Implement the initial version of the DecisionEngine. At first, it can be a simple pass-through that just approves whatever FreqAI suggests.
Phase 4: Integrate Frontend Cockpit
1. Connect to New Endpoints: Modify the React dashboard to call the new orchestrator endpoints.
2. Display Status: Show the live status of the Freqtrade bot, its P&L, and the portfolio's progress towards the user's target.
3. Implement Controls: Build the UI buttons to start and stop the bot.
4. Key Files for Redevelopment
* /app/backend/services/ (New Files):
   * luno_service.py: To replace direct Luno calls in endpoints.
   * freqtrade_service.py: To handle communication with the Freqtrade REST API.
   * target_service.py: To manage user goals.
* /app/backend/server.py:
   * Update to include new API routes for bot control and targets.
   * Integrate the new services and the decision engine logic.
* /app/freqtrade/ (New Directory):
   * config.json: The main configuration for the Freqtrade bot.
   * user_data/strategies/luno_freqai_strategy.py: The Python file containing your custom FreqAI logic.
   * user_data/freqaimodels/: Directory where trained AI models will be stored.
* /app/frontend/src/components/CryptoTraderCoach.jsx:
   * Update to fetch data from and send commands to the new orchestrator endpoints.
5. Critical Considerations
* Risk Management: The Freqtrade config.json must have a mandatory stop-loss defined. The Backend Orchestrator should also have its own risk rules, such as a maximum daily drawdown limit that, if hit, stops all trading regardless of FreqAI's signals.
* Environment Variables: All API keys (Luno, Gemini for analysis) must be managed securely in .env files and not hardcoded.
* Asynchronous Communication: The communication between the Orchestrator and Freqtrade should be asynchronous to prevent the main application from freezing while waiting for a trade signal.