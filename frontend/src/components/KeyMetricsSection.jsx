import React from 'react';
import { Activity, AlertTriangle, TrendingUp, HeartPulse } from 'lucide-react';
import './KeyMetricsSection.css';

const KeyMetricsSection = () => {
  const metrics = [
    {
      label: 'Total Patients',
      value: '5',
      icon: <Activity size={24} className="text-blue" />,
      colorClass: 'metric-blue'
    },
    {
      label: 'Critical Risk',
      value: '1',
      icon: <AlertTriangle size={24} className="text-critical" />,
      colorClass: 'metric-red'
    },
    {
      label: 'High Risk',
      value: '2',
      icon: <TrendingUp size={24} className="text-warning" />,
      colorClass: 'metric-orange'
    },
    {
      label: 'Active Today',
      value: '5',
      icon: <HeartPulse size={24} className="text-success" />,
      colorClass: 'metric-green'
    }
  ];

  return (
    <section className="metrics-section container mt-8 mb-8">
      
      {/* Hero Header */}
      <div className="metrics-header mb-6">
        <h1 className="text-3xl font-bold text-dark mb-2">Patient Overview</h1>
        <p className="text-base text-grey font-medium">Monitor CKD patients with real-time BP tracking</p>
      </div>

      {/* Grid of KPI Cards */}
      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div key={index} className="metric-card card animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex flex-col gap-2">
              <span className="text-grey font-semibold text-sm">{metric.label}</span>
              <span className="text-4xl font-bold text-dark">{metric.value}</span>
            </div>
            
            <div className={`metric-icon-circle ${metric.colorClass} flex items-center justify-center`}>
              {metric.icon}
            </div>
          </div>
        ))}
      </div>

    </section>
  );
};

export default KeyMetricsSection;
