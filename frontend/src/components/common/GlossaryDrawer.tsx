import React, { useState, useEffect } from 'react';
import { X, BookOpen, Network, Shield, Cpu, Activity, Globe, Server, Hash, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { LearningTopic } from '../../types/network';

interface GlossaryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const FALLBACK_TERMS: LearningTopic[] = [
  {
    id: 'ip-addressing',
    title: 'IP Address (IPv4 / IPv6)',
    category: 'Addressing',
    difficulty: 'beginner',
    summary: 'A unique logical identifier assigned to each device on an IP network.',
    explanation:
      'IPv4 uses 32-bit addresses formatted in four octets (e.g. 192.168.1.70). Private ranges (RFC 1918) like 192.168.0.0/16 are used inside your local Wi-Fi or LAN, while public IPs identify you on the global Internet.',
    key_takeaways: [
      'IPv4 addresses are 32 bits divided into 4 octets',
      'Private addresses are non-routable on the public Internet',
      'IPv6 provides 128-bit addresses to eliminate address exhaustion'
    ],
    live_metric_key: 'local_ip'
  },
  {
    id: 'mac-vendor',
    title: 'MAC Address & OUI Vendor',
    category: 'Hardware',
    difficulty: 'beginner',
    summary: 'Physical 48-bit address burned into the Network Interface Card (NIC).',
    explanation:
      'Formatted as XX:XX:XX:XX:XX:XX. The first 3 octets constitute the Organizationally Unique Identifier (OUI) assigned by the IEEE, allowing NetScope to identify whether a device was manufactured by Apple, Intel, TP-Link, Samsung, etc.',
    key_takeaways: [
      'MAC addresses operate at Layer 2 (Data Link)',
      'First 24 bits are the IEEE Organizationally Unique Identifier (OUI)',
      'MAC addresses do not route across routers'
    ],
    live_metric_key: 'gateway_mac'
  },
  {
    id: 'default-gateway',
    title: 'Default Gateway',
    category: 'Routing',
    difficulty: 'beginner',
    summary: 'The local router interface connecting your LAN to the outside world.',
    explanation:
      'Whenever your computer sends packets to an IP outside your local subnet (such as 1.1.1.1 or a website), it transmits the packets directly to the default gateway (often 192.168.1.1 or 192.168.1.254).',
    key_takeaways: [
      'Acts as the exit door for all non-local traffic',
      'Usually assigned via DHCP option 3',
      'Gateway MAC spoofing is a key vector for ARP poisoning'
    ],
    live_metric_key: 'default_gateway'
  },
  {
    id: 'dns-resolution',
    title: 'DNS (Domain Name System)',
    category: 'Resolution',
    difficulty: 'beginner',
    summary: 'The phonebook of the Internet translating names to IP addresses.',
    explanation:
      'Translates human-readable names like "google.com" into machine-routable IPs like 142.250.190.46. Includes record types such as A (IPv4), AAAA (IPv6), MX (Mail Exchange), and TXT (Verification).',
    key_takeaways: [
      'Translates hostnames into IP addresses over UDP/TCP port 53',
      'DNS caching minimizes lookup latency',
      'Unencrypted DNS (plaintext) can be intercepted without DoH/DoT'
    ],
    live_metric_key: 'dns_servers'
  },
  {
    id: 'tcp-ports',
    title: 'TCP Ports & Service Discovery',
    category: 'Security',
    difficulty: 'intermediate',
    summary: 'Software communication endpoints (0 to 65535) multiplexed on an IP.',
    explanation:
      'Ports allow multiple services to run on one device. Standard services: 80 (HTTP), 443 (HTTPS), 22 (SSH), 53 (DNS). Unfiltered open management ports like 23 (Telnet) or 3389 (RDP) can pose security risks if exposed to untrusted segments.',
    key_takeaways: [
      'Ports 0-1023 are well-known system ports',
      'Ports 1024-49151 are registered user ports',
      'Closed ports actively reject SYN; filtered ports drop packets silently'
    ],
    live_metric_key: 'open_ports'
  }
];

export const GlossaryDrawer: React.FC<GlossaryDrawerProps> = ({ isOpen, onClose }) => {
  const [topics, setTopics] = useState<LearningTopic[]>(FALLBACK_TERMS);
  const [categories, setCategories] = useState<string[]>(['All']);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      api.getLearningTopics()
        .then((res) => {
          if (res.topics && res.topics.length > 0) {
            setTopics(res.topics);
            setCategories(['All', ...(res.categories || [])]);
          }
        })
        .catch((err) => {
          console.debug('Using fallback learning topics:', err);
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredTopics = selectedCategory === 'All'
    ? topics
    : topics.filter((t) => t.category.toLowerCase() === selectedCategory.toLowerCase());

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case 'beginner': return 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40';
      case 'intermediate': return 'text-sky-400 bg-sky-950/40 border-sky-800/40';
      case 'advanced': return 'text-amber-400 bg-amber-950/40 border-amber-800/40';
      default: return 'text-slate-400 bg-slate-800/40 border-slate-700/40';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-xl bg-cyber-surface border-l border-cyber-border h-full flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-cyber-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyber-cyan">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-cyber-text">Networking Learning Center</h2>
              <p className="text-xs text-cyber-subtext">Interactive cybersecurity & network concepts with live engine telemetry</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-cyber-subtext hover:text-cyber-text hover:bg-cyber-card transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Category Pill Filters */}
        <div className="px-5 py-3 border-b border-cyber-border bg-cyber-bg/40 flex items-center gap-1.5 overflow-x-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-xs px-2.5 py-1 rounded-md font-mono transition-colors whitespace-nowrap ${
                selectedCategory === cat
                  ? 'bg-cyber-cyan text-black font-semibold'
                  : 'bg-cyber-card text-cyber-subtext hover:text-cyber-text border border-cyber-border'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading && topics.length === 0 ? (
            <div className="text-center py-10 text-xs text-cyber-subtext">Loading learning modules...</div>
          ) : (
            filteredTopics.map((topic) => (
              <div
                key={topic.id}
                className="bg-cyber-card border border-cyber-border rounded-xl p-4 hover:border-cyan-800/50 transition-colors space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded bg-slate-900 border border-slate-800 text-cyber-cyan">
                      <Network className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-cyber-text">{topic.title}</h3>
                      <span className="text-[10px] font-mono text-cyber-subtext uppercase">{topic.category}</span>
                    </div>
                  </div>
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${getDifficultyColor(topic.difficulty)}`}>
                    {topic.difficulty}
                  </span>
                </div>

                <p className="text-xs font-medium text-cyber-cyan">{topic.summary}</p>
                <p className="text-xs text-cyber-subtext leading-relaxed">{topic.explanation}</p>

                {topic.key_takeaways && topic.key_takeaways.length > 0 && (
                  <div className="bg-cyber-surface/60 rounded-lg p-2.5 border border-cyber-border/60">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-cyber-cyan" />
                      Key Principles
                    </div>
                    <ul className="space-y-1 text-xs text-cyber-subtext">
                      {topic.key_takeaways.map((point, pIdx) => (
                        <li key={pIdx} className="flex items-start gap-1.5">
                          <span className="text-cyber-cyan leading-4">•</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {topic.live_metric_key && (
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1 border-t border-cyber-border/40">
                    <span className="text-cyber-subtext">Monitored in NetScope:</span>
                    <span className="text-cyber-cyan bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                      {topic.live_metric_key}
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
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
