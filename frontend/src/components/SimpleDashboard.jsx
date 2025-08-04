import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SimpleDashboard = ({ onLogout }) => {
  const [healthStatus, setHealthStatus] = useState(null);
  const [lunoData, setLunoData] = useState(null);

  useEffect(() => {
    fetchHealthStatus();
    fetchLunoData();
  }, []);

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/health`);
      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'error', message: 'Backend unavailable' });
    }
  };

  const fetchLunoData = async () => {
    try {
      // This would call your simplified luno service
      setLunoData({ pair: 'XBTZAR', price: '1000000', status: 'mock' });
    } catch (error) {
      console.error('Luno data fetch failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-cyan-400">Crypto Trading Coach</h1>
          <Button onClick={onLogout} variant="outline">
            Logout
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-cyan-400">System Status</CardTitle>
            </CardHeader>
            <CardContent>
              {healthStatus ? (
                <div>
                  <p className={`text-lg font-semibold ${healthStatus.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                    {healthStatus.status === 'healthy' ? '✅ System Online' : '❌ System Error'}
                  </p>
                  <p className="text-gray-300 mt-2">{healthStatus.message}</p>
                </div>
              ) : (
                <p className="text-gray-400">Loading...</p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-cyan-400">Market Data</CardTitle>
            </CardHeader>
            <CardContent>
              {lunoData ? (
                <div>
                  <p className="text-lg font-semibold text-white">
                    {lunoData.pair}: R{parseInt(lunoData.price).toLocaleString()}
                  </p>
                  <p className="text-gray-300 mt-2">Status: {lunoData.status}</p>
                </div>
              ) : (
                <p className="text-gray-400">Loading...</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-8">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-cyan-400">Simple Trading Interface</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-300 mb-4">
                This is a simplified crypto trading dashboard. Core functionality working without complex AI features.
              </p>
              <div className="flex gap-4">
                <Button className="bg-cyan-600 hover:bg-cyan-700">
                  View Portfolio
                </Button>
                <Button className="bg-cyan-600 hover:bg-cyan-700">
                  Market Analysis
                </Button>
                <Button className="bg-cyan-600 hover:bg-cyan-700">
                  Trading History
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SimpleDashboard;