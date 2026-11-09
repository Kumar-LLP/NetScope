import React from 'react';
import { X, BookOpen, Network, Shield, Cpu, Activity, Globe, Server, Hash } from 'lucide-react';

interface GlossaryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const GLOSSARY_TERMS = [
  {
    icon: Globe,
    title: 'IP Address (IPv4 / IPv6)',
    category: 'Addressing',
    summary: 'A unique logical identifier assigned to each device on an IP network.',
    description:
      'IPv4 uses 32-bit addresses formatted in four octets (e.g. 192.168.1.70). Private ranges (RFC 1918) like 192.168.0.0/16 are used inside your local Wi-Fi or LAN, while public IPs identify you on the global Internet.'
  },
  {
    icon: Cpu,
    title: 'MAC Address & OUI Vendor',
    category: 'Hardware',
    summary: 'Physical 48-bit address burned into the Network Interface Card (NIC).',
    description:
      'Formatted as XX:XX:XX:XX:XX:XX. The first 3 octets constitute the Organizationally Unique Identifier (OUI) assigned by the IEEE, allowing NetScope to identify whether a device was manufactured by Apple, Intel, TP-Link, Samsung, etc.'
  },
  {
    icon: Network,
    title: 'Default Gateway',
    category: 'Routing',
    summary: 'The local router interface connecting your LAN to the outside world.',
    description:
      'Whenever your computer sends packets to an IP outside your local subnet (such as 1.1.1.1 or a website), it transmits the packets directly to the default gateway (often 192.168.1.1 or 192.168.1.254).'
  },
  {
    icon: Server,
    title: 'DNS (Domain Name System)',
    category: 'Resolution',
    summary: 'The phonebook of the Internet translating names to IP addresses.',
    description:
      'Translates human-readable names like "google.com" into machine-routable IPs like 142.250.190.46. Includes record types such as A (IPv4), AAAA (IPv6), MX (Mail Exchange), and TXT (Verification).'
  },
  {
    icon: Hash,
    title: 'Subnet & CIDR Notation',
    category: 'Architecture',
    summary: 'Splitting networks into manageable broadcast domains.',
    description:
      'CIDR (Classless Inter-Domain Routing) like /24 indicates that the first 24 bits are fixed for the network, leaving 8 bits (254 usable hosts) for devices on the same local segment.'
  },
  {
    icon: Activity,
    title: 'Latency & Round-Trip Time (RTT)',
    category: 'Performance',
    summary: 'The time taken for a data packet to travel to a destination and return.',
    description:
      'Measured in milliseconds (ms). Latency under 25ms is considered excellent for gaming and video calls, while latency exceeding 100ms indicates geographic distance or network bufferbloat.'
  },
  {
    icon: Shield,
    title: 'TCP Ports & Service Discovery',
    category: 'Security',
    summary: 'Software communication endpoints (0 to 65535) multiplexed on an IP.',
    description:
      'Ports allow multiple services to run on one device. Standard services: 80 (HTTP), 443 (HTTPS), 22 (SSH), 53 (DNS). Unfiltered open management ports like 23 (Telnet) or 3389 (RDP) can pose security risks if exposed to untrusted segments.'
  }
];

export const GlossaryDrawer: React.FC<GlossaryDrawerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-lg bg-cyber-surface border-l border-cyber-border h-full flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-cyber-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyber-cyan">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-cyber-text">Networking Learning Center</h2>
              <p className="text-xs text-cyber-subtext">Interactive cybersecurity & networking guide</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-cyber-subtext hover:text-cyber-text hover:bg-cyber-card transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {GLOSSARY_TERMS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="bg-cyber-card border border-cyber-border rounded-xl p-4 hover:border-cyan-800/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-cyber-blue mt-0.5">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-cyber-text">{item.title}</h3>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800/60 text-slate-400">
                        {item.category}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-cyber-cyan mt-1">{item.summary}</p>
                    <p className="text-xs text-cyber-subtext mt-2 leading-relaxed">{item.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-cyber-border bg-cyber-bg/50 flex justify-between items-center text-xs text-cyber-subtext">
          <span>NetScope Educational Engine</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-muted text-cyber-text text-xs"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
