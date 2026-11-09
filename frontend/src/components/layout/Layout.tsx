import React, { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { GlossaryDrawer } from '../common/GlossaryDrawer';
import { GlobalSearchModal } from '../common/GlobalSearchModal';
import { NotificationDrawer } from '../common/NotificationDrawer';
import { useTelemetry } from '../../hooks/useTelemetry';
import { api } from '../../services/api';
import { DiscoveredDevice } from '../../types/network';

interface LayoutProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onNavigateTabWithParam?: (tab: string, param?: string) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  activeTab,
  setActiveTab,
  onNavigateTabWithParam,
  children
}) => {
  const [glossaryOpen, setGlossaryOpen] = useState<boolean>(false);
  const [searchOpen, setSearchOpen] = useState<boolean>(false);
  const [notificationsOpen, setNotificationsOpen] = useState<boolean>(false);
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const { telemetry, isConnected } = useTelemetry();

  // Load devices for global search palette
  useEffect(() => {
    api.getDevices()
      .then((data) => setDevices(data))
      .catch((err) => console.debug('Search devices cache load:', err));
  }, [activeTab]);

  // Global Ctrl+K / Cmd+K handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleGlobalNavigate = (tab: string, extraParam?: string) => {
    if (onNavigateTabWithParam) {
      onNavigateTabWithParam(tab, extraParam);
    } else {
      setActiveTab(tab);
    }
  };

  return (
    <div className="flex h-screen bg-cyber-bg text-cyber-text overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenGlossary={() => setGlossaryOpen(true)}
      />

      {/* Main View Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar
          telemetry={telemetry}
          wsConnected={isConnected}
          onOpenGlossary={() => setGlossaryOpen(true)}
          onOpenSearch={() => setSearchOpen(true)}
          onOpenNotifications={() => setNotificationsOpen(true)}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-cyber-bg">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>

      {/* Global Command Palette (Ctrl+K) */}
      <GlobalSearchModal
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        devices={devices}
        onNavigateTab={handleGlobalNavigate}
      />

      {/* System Notification Drawer */}
      <NotificationDrawer
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />

      {/* Educational Learning Center Slide-out */}
      <GlossaryDrawer
        isOpen={glossaryOpen}
        onClose={() => setGlossaryOpen(false)}
      />
    </div>
  );
};
