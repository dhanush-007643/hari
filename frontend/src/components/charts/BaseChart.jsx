import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Pie, Doughnut, Scatter } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const BaseChart = ({ type = 'bar', data, title, height = 300 }) => {
  if (!data) return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>Loading chart data...</div>;

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#A3AED0',
          font: { family: 'Inter', size: 12 }
        }
      },
      title: {
        display: !!title,
        text: title,
        color: '#2B3674',
        font: { family: 'Outfit', size: 16, weight: '600' }
      },
      tooltip: {
        backgroundColor: 'rgba(17, 28, 68, 0.9)',
        titleFont: { family: 'Inter', size: 13 },
        bodyFont: { family: 'Inter', size: 13 },
        padding: 12,
        cornerRadius: 8,
        displayColors: true
      }
    },
    scales: type === 'pie' || type === 'doughnut' ? {} : {
      x: {
        grid: { display: false },
        ticks: { color: '#A3AED0', font: { family: 'Inter' } }
      },
      y: {
        grid: { color: 'rgba(163, 174, 208, 0.1)' },
        ticks: { color: '#A3AED0', font: { family: 'Inter' } }
      }
    },
    interaction: {
      mode: 'index',
      intersect: false,
    },
  };

  // Auto-apply glass/dark styling adjustments based on body theme if needed
  // We're keeping it simple for now, using standard colors

  let ChartComponent;
  switch (type) {
    case 'line': ChartComponent = Line; break;
    case 'bar': ChartComponent = Bar; break;
    case 'pie': ChartComponent = Pie; break;
    case 'doughnut': ChartComponent = Doughnut; break;
    case 'scatter': ChartComponent = Scatter; break;
    default: ChartComponent = Bar;
  }

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      <ChartComponent options={options} data={data} />
    </div>
  );
};

export default BaseChart;
