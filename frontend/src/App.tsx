import React, { useState } from 'react';
import { Layout } from './components/layout/Layout';
import { OverviewPage } from './pages/OverviewPage';
import { DeviceDiscoveryPage } from './pages/DeviceDiscoveryPage';
import { TopologyPage } from './pages/TopologyPage';
import { DiagnosticsPage } from './pages/DiagnosticsPage';
import { PortDiagnosticsPage } from './pages/PortDiagnosticsPage';
import { TrafficAnalyticsPage } from './pages/TrafficAnalyticsPage';
import { SecurityInsightsPage } from './pages/SecurityInsightsPage';
import { ScanHistoryPage } from './pages/ScanHistoryPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === 'overview' && <OverviewPage />}
      {activeTab === 'discovery' && <DeviceDiscoveryPage />}
      {activeTab === 'topology' && <TopologyPage />}
      {activeTab === 'diagnostics' && <DiagnosticsPage />}
      {activeTab === 'ports' && <PortDiagnosticsPage />}
      {activeTab === 'traffic' && <TrafficAnalyticsPage />}
      {activeTab === 'security' && <SecurityInsightsPage />}
      {activeTab === 'history' && <ScanHistoryPage />}
      {activeTab === 'settings' && <SettingsPage />}
    </Layout>
  );
}

export default App;
