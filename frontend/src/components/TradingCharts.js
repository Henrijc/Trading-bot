import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement
);

const TradingCharts = ({ performanceData, marketData, trades }) => {
  // Generate sample data for demonstration
  const generateTimeLabels = (hours = 24) => {
    const labels = [];
    const now = new Date();
    for (let i = hours; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      labels.push(time.toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' }));
    }
    return labels;
  };

  const generatePriceData = (basePrice = 2076763) => {
    const data = [];
    for (let i = 0; i <= 24; i++) {
      const variation = Math.sin(i / 4) * 50000 + (Math.random() - 0.5) * 20000;
      data.push(basePrice + variation);
    }
    return data;
  };

  const generateProfitData = () => {
    const data = [];
    let cumulative = 0;
    for (let i = 0; i <= 24; i++) {
      const profit = (Math.random() - 0.4) * 100;
      cumulative += profit;
      data.push(cumulative);
    }
    return data;
  };

  const priceChartData = {
    labels: generateTimeLabels(),
    datasets: [
      {
        label: 'BTC/ZAR Price',
        data: generatePriceData(),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderWidth: 2,
        fill: false,
        tension: 0.1,
      },
    ],
  };

  const profitChartData = {
    labels: generateTimeLabels(),
    datasets: [
      {
        label: 'Cumulative P&L (ZAR)',
        data: generateProfitData(),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
      },
    ],
  };

  const volumeChartData = {
    labels: generateTimeLabels(12),
    datasets: [
      {
        label: 'Trading Volume (ZAR)',
        data: Array.from({length: 13}, () => Math.random() * 100000 + 20000),
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 205, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(199, 199, 199, 0.6)',
          'rgba(83, 102, 255, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 205, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 205, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(199, 199, 199, 1)',
          'rgba(83, 102, 255, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 205, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
  };

  const priceChartOptions = {
    ...chartOptions,
    plugins: {
      ...chartOptions.plugins,
      title: {
        ...chartOptions.plugins.title,
        text: 'BTC/ZAR Price Movement (24h)',
      },
    },
    scales: {
      ...chartOptions.scales,
      y: {
        ...chartOptions.scales.y,
        ticks: {
          callback: function(value) {
            return new Intl.NumberFormat('en-ZA', {
              style: 'currency',
              currency: 'ZAR',
              minimumFractionDigits: 0,
            }).format(value);
          },
        },
      },
    },
  };

  const profitChartOptions = {
    ...chartOptions,
    plugins: {
      ...chartOptions.plugins,
      title: {
        ...chartOptions.plugins.title,
        text: 'Cumulative Profit & Loss (24h)',
      },
    },
    scales: {
      ...chartOptions.scales,
      y: {
        ...chartOptions.scales.y,
        ticks: {
          callback: function(value) {
            return new Intl.NumberFormat('en-ZA', {
              style: 'currency',
              currency: 'ZAR',
            }).format(value);
          },
        },
      },
    },
  };

  const volumeChartOptions = {
    ...chartOptions,
    plugins: {
      ...chartOptions.plugins,
      title: {
        ...chartOptions.plugins.title,
        text: 'Trading Volume (12h)',
      },
    },
    scales: {
      ...chartOptions.scales,
      y: {
        ...chartOptions.scales.y,
        ticks: {
          callback: function(value) {
            return new Intl.NumberFormat('en-ZA', {
              style: 'currency',
              currency: 'ZAR',
              minimumFractionDigits: 0,
            }).format(value);
          },
        },
      },
    },
  };

  return (
    <div className="trading-charts">
      <div className="charts-grid">
        {/* Price Chart */}
        <div className="chart-container price-chart">
          <div style={{ height: '300px', position: 'relative' }}>
            <Line data={priceChartData} options={priceChartOptions} />
          </div>
        </div>

        {/* P&L Chart */}
        <div className="chart-container profit-chart">
          <div style={{ height: '300px', position: 'relative' }}>
            <Line data={profitChartData} options={profitChartOptions} />
          </div>
        </div>

        {/* Volume Chart */}
        <div className="chart-container volume-chart">
          <div style={{ height: '300px', position: 'relative' }}>
            <Bar data={volumeChartData} options={volumeChartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingCharts;