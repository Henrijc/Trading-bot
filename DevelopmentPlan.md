Project Plan: AI-Driven Portfolio Management System
This document provides a step-by-step guide for re-architecting the application into an automated trading system, following the principles outlined in the Development Framework.
Phase 0: Project Setup & Code Audit
Objective: To prepare the existing codebase for the new architecture.
1. Code to KEEP:
* /app/frontend/ (Entire Directory): The React application, including components, UI libraries (Shadcn, Tailwind), and build configuration, serves as the perfect foundation for the new "Cockpit."
* /app/backend/ (Directory & FastAPI setup): The core backend server structure is sound. We will build upon it.
* Authentication Logic: The complete, working login system (both frontend and backend) is critical and will be kept as-is.
* Luno API Connection Logic: The existing Python code that successfully connects to Luno and fetches data is valuable. It will be refactored into a dedicated service.
2. Code to REMOVE/REPLACE:
* Existing Chat-based AI: The concept of a conversational AI will be replaced by the FreqAI predictive model. The /api/chat endpoints and the ai_service.py can be removed.
* Direct Luno calls in API endpoints: All logic that currently calls the Luno API directly from within an endpoint in server.py will be moved into a dedicated service.
3. NEW Components to be Built:
* /app/freqtrade/ (New Directory): This will house the entire standalone Freqtrade trading bot, including its configuration, strategies, and AI models.
* New Backend Services: New Python files within /app/backend/services/ that encapsulate specific responsibilities.
Phase 1: Establish the Standalone Trader
Objective: To get a Freqtrade instance running and proven to work with your Luno account, completely independent of the main application.
* Step 1.1: Install Freqtrade. In your project root, create a new directory /app/freqtrade/. Follow the official Freqtrade documentation to install it within this directory.
* Step 1.2: Create Initial Configuration. Inside /app/freqtrade/, generate a config.json file. Edit it to include:
   * Your Luno API Key and Secret.
   * "dry_run": true (Crucial for testing without real money).
   * The trading pairs you want to use (e.g., "XBTZAR", "ETHZAR").
   * Enable the REST API: Set "api_server": { "enabled": true, "listen_ip_address": "0.0.0.0" }.
* Step 1.3: Create a Simple Test Strategy. In /app/freqtrade/user_data/strategies/, create a file test_strategy.py. Use a basic, non-AI strategy (like a simple EMA cross) to ensure signals can be generated.
* Step 1.4: Validate. Run the Freqtrade bot from the command line. Watch the logs to confirm that it successfully connects to Luno and starts processing market data for your chosen pairs without crashing. This step is complete when you see Freqtrade running smoothly.
Phase 2: Scaffold the Backend Orchestrator
Objective: To refactor the backend and create the API "scaffolding" needed to communicate with the frontend and (eventually) the Freqtrade bot.
* Step 2.1: Create New Service Files. In /app/backend/services/, create the following new Python files:
   * luno_service.py: Move your existing Luno connection and data-fetching logic into a class within this file.
   * freqtrade_service.py: Create a placeholder class. This will later contain the logic to call the Freqtrade API.
   * target_service.py: Create a placeholder class for managing user targets.
* Step 2.2: Refactor Existing Endpoints. In /app/backend/server.py, modify the /api/portfolio/status endpoint. Instead of containing the Luno logic itself, it should now call the method from your new luno_service.py.
* Step 2.3: Create New API Endpoints. In server.py, add the new routes: /api/bot/start, /api/bot/stop, and /api/bot/status. For now, their functions should simply return a JSON response like {"status": "not implemented"}. This allows the frontend to be developed in parallel.
Phase 3: Connect the Frontend Cockpit
Objective: To update the user interface to include controls for the trading bot and to connect them to the new backend scaffolding.
* Step 3.1: Add Bot Status UI. In your main dashboard component (CryptoTraderCoach.jsx), add UI elements to display the bot's status (e.g., an indicator for "Running" or "Stopped") and its current overall profit/loss.
* Step 3.2: Add Bot Control UI. Add "Start Bot" and "Stop Bot" buttons to the dashboard.
* Step 3.3: Wire the UI. Use axios or fetch to make the new UI elements interactive.
   * The status indicators should periodically call the /api/bot/status endpoint.
   * The "Start Bot" button should call the /api/bot/start endpoint.
   * The "Stop Bot" button should call the /api/bot/stop endpoint.
* Step 3.4: Validate. Run the application. You should be able to click the buttons and see the "not implemented" responses from your backend in the browser's network tab. This confirms the frontend and backend are correctly wired.
Phase 4: Integrate Orchestrator and Trader
Objective: To make the backend's API endpoints functional by having them communicate with the live Freqtrade instance.
* Step 4.1: Implement the Freqtrade Service. In /app/backend/services/freqtrade_service.py, use a Python HTTP client library (like httpx or requests) to implement the functions.
   * The start_bot function should make a POST request to the Freqtrade API's /api/v1/start endpoint.
   * The stop_bot function should make a POST request to /api/v1/stop.
   * The get_status function should make a GET request to /api/v1/status.
* Step 4.2: Connect in server.py. Update the placeholder functions for /api/bot/... in server.py to call the corresponding, now-functional methods from your freqtrade_service.py.
* Step 4.3: End-to-End Test. With both the Freqtrade bot and the main application running, go to the frontend dashboard. Clicking the "Start Bot" button should now actually start the Freqtrade instance, and the status indicator should update to show it's running.
Phase 5: Develop FreqAI Intelligence
Objective: To replace the simple test strategy with a predictive AI model.
* Step 5.1: Acquire Data. Use Freqtrade's built-in scripts to download at least 1-2 years of historical candle data from Luno for your trading pairs.
* Step 5.2: Feature Engineering. Create a new strategy file, luno_freqai_strategy.py. In this file, define the technical indicators (RSI, MACD, Bollinger Bands, etc.) that will serve as "features" for your AI model.
* Step 5.3: Train and Backtest. Use the FreqAI commands to train your first model on the historical data. FreqAI will use the features you defined to predict future price movements. Run a backtest to see how the AI model would have performed.
* Step 5.4: Activate AI Model. Once you have a model that shows promise in backtesting, update your Freqtrade config.json to use the luno_freqai_strategy.py and the associated trained model file.
Phase 6: Implement the Decision Engine
Objective: To implement the final layer of intelligence where high-level portfolio goals guide the AI's trading actions.
* Step 6.1: Implement Target Management. Fully implement the target_service.py and the /api/targets endpoints, allowing the user to save and update their financial goals in the database.
* Step 6.2: Implement the Decision Engine. In the backend, create the core DecisionEngine logic. This logic will be called before any trade is approved. It will:
   1. Fetch the user's current portfolio value (luno_service).
   2. Fetch the user's target (target_service).
   3. Fetch the proposed trade signal from FreqAI (freqtrade_service).
   4. Apply a set of rules. (e.g., IF portfolio_is_above_target AND signal_is_sell THEN approve_trade, or IF portfolio_is_below_target AND signal_is_high_confidence_buy THEN approve_trade).
* Step 6.3: Final Integration. Route all trading decisions through this engine, completing the system architecture.