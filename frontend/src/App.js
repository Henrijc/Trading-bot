import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import "./App.css";

// Import components
import Dashboard from "./components/Dashboard";
import TradingView from "./components/TradingView";
import AIConfig from "./components/AIConfig";
import PerformanceAnalytics from "./components/PerformanceAnalytics";
import GoalTracking from "./components/GoalTracking";
import Navigation from "./components/Navigation";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [wsConnection, setWsConnection] = useState(null);

  useEffect(() => {
    // Check system health on startup
    checkSystemHealth();
    
    // Establish WebSocket connection for real-time updates
    connectWebSocket();
    
    // Set up periodic health checks
    const healthInterval = setInterval(checkSystemHealth, 30000); // Every 30 seconds
    
    return () => {
      clearInterval(healthInterval);
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, []);

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

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`${API.replace('http', 'ws')}/ws/live-data`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Handle real-time updates
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('WebSocket message parsing error:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      setWsConnection(ws);
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnectionStatus('error');
    }
  };

  const handleWebSocketMessage = (data) => {
    // This would be handled by individual components through context or state management
    console.log('Received real-time data:', data);
  };

  return (
    <div className="App">
      <BrowserRouter>
        {/* System Status Header */}
        <div className={`status-header ${connectionStatus}`}>
          <div className="container mx-auto px-4 py-2 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-white">AI Crypto Trading Bot</h1>
              <div className={`status-indicator ${connectionStatus}`}>
                <span className="status-dot"></span>
                <span className="text-sm capitalize">{connectionStatus}</span>
              </div>
            </div>
            <div className="system-health">
              {systemHealth && (
                <div className="flex items-center space-x-2 text-sm">
                  <span>Luno: {systemHealth.services?.luno || 'unknown'}</span>
                  <span>DB: {systemHealth.services?.database || 'unknown'}</span>
                  <span>FreqTrade: {systemHealth.services?.freqtrade || 'unknown'}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trading" element={<TradingView />} />
            <Route path="/ai-config" element={<AIConfig />} />
            <Route path="/analytics" element={<PerformanceAnalytics />} />
            <Route path="/goals" element={<GoalTracking />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;