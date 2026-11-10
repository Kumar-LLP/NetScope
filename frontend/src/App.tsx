import React, { useState, useCallback, Suspense, lazy } from 'react';
import { Layout } from './components/layout/Layout';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ToastProvider } from './components/common/Toast';

// Lazy-loaded page components for optimal bundle splitting
const OverviewPage = lazy(() => import('./pages/OverviewPage').then(m => ({ default: m.OverviewPage })));
const DeviceDiscoveryPage = lazy(() => import('./pages/DeviceDiscoveryPage').then(m => ({ default: m.DeviceDiscoveryPage })));
const TopologyPage = lazy(() => import('./pages/TopologyPage').then(m => ({ default: m.TopologyPage })));
const DiagnosticsPage = lazy(() => import('./pages/DiagnosticsPage').then(m => ({ default: m.DiagnosticsPage })));
const PortDiagnosticsPage = lazy(() => import('./pages/PortDiagnosticsPage').then(m => ({ default: m.PortDiagnosticsPage })));
const TrafficAnalyticsPage = lazy(() => import('./pages/TrafficAnalyticsPage').then(m => ({ default: m.TrafficAnalyticsPage })));
const SecurityInsightsPage = lazy(() => import('./pages/SecurityInsightsPage').then(m => ({ default: m.SecurityInsightsPage })));
const ScanHistoryPage = lazy(() => import('./pages/ScanHistoryPage').then(m => ({ default: m.ScanHistoryPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));

function PageFallback() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
      <div className="w-8 h-8 rounded-full border-2 border-cyber-cyan border-t-transparent animate-spin" />
      <span className="text-xs text-cyber-subtext tracking-wider uppercase font-mono">Loading module...</span>
    </div>
  );
}

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
          <Suspense fallback={<PageFallback />}>
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
          </Suspense>
        </Layout>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
