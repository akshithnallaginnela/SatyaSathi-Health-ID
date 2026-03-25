import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface TrendChartProps {
  data: Array<{ date: string; value: number; value2?: number }>;
  label: string;
  label2?: string;
  color: string;
  color2?: string;
  yAxisLabel: string;
  showTrend?: boolean;
}

export default function TrendChart({ 
  data, 
  label, 
  label2,
  color, 
  color2,
  yAxisLabel,
  showTrend = true 
}: TrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
        <p className="text-gray-400 text-sm">No data yet</p>
        <p className="text-gray-300 text-xs mt-1">Start logging to see trends</p>
      </div>
    );
  }

  const chartData = {
    labels: data.map(d => {
      const date = new Date(d.date);
      return `${date.getDate()}/${date.getMonth() + 1}`;
    }),
    datasets: [
      {
        label: label,
        data: data.map(d => d.value),
        borderColor: color,
        backgroundColor: `${color}20`,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
      ...(label2 && data[0]?.value2 !== undefined ? [{
        label: label2,
        data: data.map(d => d.value2 || 0),
        borderColor: color2 || '#F59E0B',
        backgroundColor: `${color2 || '#F59E0B'}20`,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: color2 || '#F59E0B',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      }] : [])
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: { size: 11, weight: '600' as const },
          color: '#333',
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: { size: 12, weight: '600' as const },
        bodyFont: { size: 11 },
        cornerRadius: 8,
        displayColors: true,
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false,
        },
        ticks: {
          font: { size: 10 },
          color: '#666',
          padding: 8,
        },
        title: {
          display: true,
          text: yAxisLabel,
          font: { size: 11, weight: '600' as const },
          color: '#333',
        }
      },
      x: {
        grid: {
          display: false,
          drawBorder: false,
        },
        ticks: {
          font: { size: 10 },
          color: '#666',
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 8,
        }
      }
    }
  };

  // Calculate trend
  let trendText = '';
  let trendColor = '';
  if (showTrend && data.length >= 2) {
    const firstVal = data[0].value;
    const lastVal = data[data.length - 1].value;
    const change = lastVal - firstVal;
    const percentChange = ((change / firstVal) * 100).toFixed(1);
    
    if (Math.abs(change) < 2) {
      trendText = 'Stable';
      trendColor = 'text-gray-600';
    } else if (change < 0) {
      trendText = `↓ ${Math.abs(parseFloat(percentChange))}% (Improving)`;
      trendColor = 'text-green-600';
    } else {
      trendText = `↑ ${percentChange}% (Rising)`;
      trendColor = 'text-orange-600';
    }
  }

  return (
    <div className="space-y-2">
      {showTrend && trendText && (
        <div className="flex justify-between items-center">
          <span className="text-xs font-semibold text-gray-500">Last {data.length} readings</span>
          <span className={`text-xs font-bold ${trendColor}`}>{trendText}</span>
        </div>
      )}
      <div className="h-48">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
