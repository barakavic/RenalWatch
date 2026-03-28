import React from 'react';
import { Activity, Users, Bell, Stethoscope } from 'lucide-react';
import './TopNav.css';

const TopNav = () => {
  return (
    <nav className="topnav glass-panel">
      <div className="container topnav-content">
        
        {/* Logo Section */}
        <div className="logo-section flex items-center gap-4">
          <div className="logo-icon flex items-center justify-center">
            <Activity color="white" size={24} />
          </div>
          <div className="flex-col">
            <span className="logo-title font-bold text-dark text-lg">RenalWatch</span>
            <span className="logo-subtitle font-medium text-grey text-xs">Doctor Portal</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="nav-tabs flex items-center gap-2">
          <div className="nav-tab active flex items-center gap-2">
            <Users size={18} />
            <span className="font-semibold text-sm">Patients</span>
          </div>
          <div className="nav-tab flex items-center gap-2">
            <Bell size={18} />
            <span className="font-medium text-sm">Alerts</span>
          </div>
        </div>

        {/* Doctor Profile */}
        <div className="doctor-profile flex items-center gap-4">
          <div className="flex-col profile-text">
            <span className="font-bold text-dark text-sm">Dr. Mwangi</span>
            <span className="font-medium text-grey text-xs">Nephrologist</span>
          </div>
          <div className="profile-icon flex items-center justify-center">
            <Stethoscope size={20} className="text-grey" />
          </div>
        </div>

      </div>
    </nav>
  );
};

export default TopNav;
