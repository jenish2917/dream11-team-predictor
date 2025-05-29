import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

// Register the required components for Chart.js
ChartJS.register(ArcElement, Tooltip, Legend);

const CompositionGraph = ({ teamData }) => {
  // Count players by role
  const roleCount = {
    'Batsman': 0,
    'Bowler': 0,
    'All-rounder': 0,
    'Wicketkeeper': 0
  };

  // Calculate team composition
  teamData.players.forEach(player => {
    if (roleCount.hasOwnProperty(player.role)) {
      roleCount[player.role] += 1;
    }
  });

  // Chart data
  const chartData = {
    labels: Object.keys(roleCount),
    datasets: [
      {
        data: Object.values(roleCount),
        backgroundColor: [
          'rgba(54, 162, 235, 0.7)',  // Batsman - Blue
          'rgba(75, 192, 192, 0.7)',   // Bowler - Green
          'rgba(153, 102, 255, 0.7)',  // All-rounder - Purple
          'rgba(255, 206, 86, 0.7)'    // Wicketkeeper - Yellow
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 206, 86, 1)'
        ],
        borderWidth: 1,
      },
    ],
  };

  // Chart options
  const options = {
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          font: {
            size: 12
          },
          color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
        }
      },
      tooltip: {
        backgroundColor: document.documentElement.classList.contains('dark') ? '#374151' : '#ffffff',
        titleColor: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111827',
        bodyColor: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151',
        borderColor: document.documentElement.classList.contains('dark') ? '#4b5563' : '#e5e7eb',
        borderWidth: 1
      }
    },
    cutout: '60%'
  };

  const roleStats = [
    { role: 'Batsman', color: 'bg-blue-500' },
    { role: 'Bowler', color: 'bg-green-500' },
    { role: 'All-rounder', color: 'bg-purple-500' },
    { role: 'Wicketkeeper', color: 'bg-yellow-500' }
  ];

  return (
    <div className="flex flex-col">
      <div className="mb-6 h-64">
        <Doughnut data={chartData} options={options} />
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        {roleStats.map((item) => (
          <div key={item.role} className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className={`w-3 h-3 rounded-full ${item.color} mr-2`}></div>
            <div>
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{item.role}</p>
              <p className="text-sm font-bold text-gray-900 dark:text-white">{roleCount[item.role]}</p>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Team Balance</h3>
        <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full">
          <div 
            className="h-2 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-green-500" 
            style={{ 
              width: `${(roleCount['Batsman'] + roleCount['All-rounder'] / 2) / 
                      (roleCount['Batsman'] + roleCount['Bowler'] + roleCount['All-rounder'] + roleCount['Wicketkeeper']) * 100}%` 
            }}
          ></div>
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-blue-500 dark:text-blue-400">Batting</span>
          <span className="text-xs text-green-500 dark:text-green-400">Bowling</span>
        </div>
      </div>
    </div>
  );
};

export default CompositionGraph;
