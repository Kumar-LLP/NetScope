import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { GlossaryDrawer } from '../common/GlossaryDrawer';
import { useTelemetry } from '../../hooks/useTelemetry';

interface LayoutProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  activeTab,
  setActiveTab,
  children
}) => {
  const [glossaryOpen, setGlossaryOpen] = useState<boolean>(false);
  const { telemetry, isConnected } = useTelemetry();

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
        />

        <main className="flex-1 overflow-y-auto p-6 bg-cyber-bg">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>

      {/* Educational Learning Center Slide-out */}
      <GlossaryDrawer
        isOpen={glossaryOpen}
        onClose={() => setGlossaryOpen(false)}
      />
    </div>
  );
};
