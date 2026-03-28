import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import './PatientTable.css';

const MOCK_PATIENTS = [
  {
    id: 1,
    name: 'Joseph Kamau',
    email: 'joseph.kamau@example.com',
    initials: 'JK',
    age: 58,
    ckdStage: 3,
    riskLevel: 'HIGH',
    lastReading: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    phone: '+254 712 345678'
  },
  {
    id: 2,
    name: 'Sarah Njoroge',
    email: 'sarah.njoroge@example.com',
    initials: 'SN',
    age: 62,
    ckdStage: 4,
    riskLevel: 'CRITICAL',
    lastReading: new Date(Date.now() - 1000 * 60 * 30), // 30 mins ago
    phone: '+254 799 123456'
  },
  {
    id: 3,
    name: 'Peter Ochieng',
    email: 'peter.ochieng@example.com',
    initials: 'PO',
    age: 45,
    ckdStage: 2,
    riskLevel: 'LOW',
    lastReading: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
    phone: '+254 722 987654'
  },
  {
    id: 4,
    name: 'Mary Wanjiku',
    email: 'mary.wanjiku@example.com',
    initials: 'MW',
    age: 51,
    ckdStage: 3,
    riskLevel: 'MEDIUM',
    lastReading: new Date(Date.now() - 1000 * 60 * 60 * 5), // 5 hours ago
    phone: '+254 733 456789'
  },
  {
    id: 5,
    name: 'John Doe',
    email: 'john.doe@example.com',
    initials: 'JD',
    age: 70,
    ckdStage: 4,
    riskLevel: 'HIGH',
    lastReading: new Date(Date.now() - 1000 * 60 * 60 * 12), // 12 hours ago
    phone: '+254 700 112233'
  }
];

const PatientTable = () => {
  
  const getRiskBadgeClass = (risk) => {
    switch(risk) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MEDIUM': return 'badge-medium';
      default: return 'badge-low';
    }
  };

  const getStageBadgeClass = (stage) => {
    switch(stage) {
      case 4: return 'badge-stage-4';
      case 3: return 'badge-stage-3';
      default: return 'badge-stage-2';
    }
  };

  return (
    <section className="container mb-12 animate-fade-in" style={{ animationDelay: '0.4s' }}>
      <div className="table-card card">
        <div className="table-responsive">
          <table className="patient-table text-left w-full">
            
            <thead>
              <tr>
                <th>Patient Name</th>
                <th className="text-center">Age</th>
                <th>CKD Stage</th>
                <th>Risk Level</th>
                <th>Last Reading</th>
                <th>Phone</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            
            <tbody>
              {MOCK_PATIENTS.map((patient) => (
                <tr key={patient.id} className="table-row">
                  
                  {/* Name Col */}
                  <td className="flex items-center gap-3">
                    <div className="avatar flex items-center justify-center font-bold text-sm">
                      {patient.initials}
                    </div>
                    <div className="flex-col">
                      <span className="font-bold text-dark text-base">{patient.name}</span>
                      <span className="text-grey text-xs mt-1">{patient.email}</span>
                    </div>
                  </td>
                  
                  {/* Age Col */}
                  <td className="text-center font-medium text-dark">{patient.age}</td>
                  
                  {/* Stage Col */}
                  <td>
                    <span className={`badge ${getStageBadgeClass(patient.ckdStage)}`}>
                      Stage {patient.ckdStage}
                    </span>
                  </td>
                  
                  {/* Risk Col */}
                  <td>
                    <span className={`badge ${getRiskBadgeClass(patient.riskLevel)}`}>
                      {patient.riskLevel}
                    </span>
                  </td>
                  
                  {/* Last Reading Col */}
                  <td className="text-grey font-medium text-sm">
                    {formatDistanceToNow(patient.lastReading, { addSuffix: true })}
                  </td>
                  
                  {/* Phone Col */}
                  <td className="font-medium text-dark text-sm">{patient.phone}</td>
                  
                  {/* Actions Col */}
                  <td className="text-right">
                    <button className="primary-btn view-dashboard-btn">
                      View Dashboard
                    </button>
                  </td>
                  
                </tr>
              ))}
            </tbody>
            
          </table>
        </div>
      </div>
    </section>
  );
};

export default PatientTable;
