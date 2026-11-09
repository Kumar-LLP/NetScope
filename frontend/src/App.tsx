import React, { useState, useCallback } from 'react';
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
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ToastProvider } from './components/common/Toast';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [diagnosticTarget, setDiagnosticTarget] = useState<string>('1.1.1.1');
  const [portTarget, setPortTarget] = useState<string>('127.0.0.1');

  const handleNavigateToPing = useCallback((ip: string) => {
    setDiagnosticTarget(ip);
    setActiveTab('diagnostics');
  }, []);

  const handleNavigateToPortScan = useCallback((ip: string) => {
    setPortTarget(ip);
    setActiveTab('ports');
  }, []);

  const handleNavigateTabWithParam = useCallback((tab: string, param?: string) => {
    if (param) {
      if (tab === 'diagnostics') setDiagnosticTarget(param);
      if (tab === 'ports') setPortTarget(param);
    }
    setActiveTab(tab);
  }, []);

  return (
    <ErrorBoundary>
      <ToastProvider>
        <Layout
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onNavigateTabWithParam={handleNavigateTabWithParam}
        >
          {activeTab === 'overview' && <OverviewPage />}
          {activeTab === 'discovery' && (
            <DeviceDiscoveryPage
              onNavigateToPing={handleNavigateToPing}
              onNavigateToPortScan={handleNavigateToPortScan}
            />
          )}
          {activeTab === 'topology' && <TopologyPage />}
          {activeTab === 'diagnostics' && (
            <DiagnosticsPage initialTarget={diagnosticTarget} />
          )}
          {activeTab === 'ports' && (
            <PortDiagnosticsPage initialTarget={portTarget} />
          )}
          {activeTab === 'traffic' && <TrafficAnalyticsPage />}
          {activeTab === 'security' && <SecurityInsightsPage />}
          {activeTab === 'history' && <ScanHistoryPage />}
          {activeTab === 'settings' && <SettingsPage />}
        </Layout>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
