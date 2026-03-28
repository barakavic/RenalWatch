import React from 'react';
import TopNav from './components/TopNav';
import KeyMetricsSection from './components/KeyMetricsSection';
import PatientTable from './components/PatientTable';

function App() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <main>
        <KeyMetricsSection />
        <PatientTable />
      </main>
    </div>
  );
}

export default App;
