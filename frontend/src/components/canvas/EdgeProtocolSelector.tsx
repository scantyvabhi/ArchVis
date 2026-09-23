import React, { useState, useRef, useEffect } from 'react';
import { ExternalLink } from 'lucide-react';
import { createPortal } from 'react-dom';

interface EdgeProtocolSelectorProps {
  protocol: string;
  onProtocolChange: (newProtocol: string) => void;
}

const PROTOCOLS = [
  { value: 'HTTP/REST', label: 'HTTP/REST', icon: '🌐', description: 'Standard REST API over HTTP' },
  { value: 'gRPC', label: 'gRPC', icon: '⚡', description: 'High-performance RPC with protobuf' },
  { value: 'GraphQL', label: 'GraphQL', icon: '🔮', description: 'Flexible query language' },
  { value: 'Kafka', label: 'Kafka', icon: '📦', description: 'Event streaming platform' },
  { value: 'AMQP', label: 'AMQP/RabbitMQ', icon: '🐰', description: 'Message queuing protocol' },
  { value: 'WebSocket', label: 'WebSocket', icon: '🔌', description: 'Full-duplex communication' },
  { value: 'gRPC-Web', label: 'gRPC-Web', icon: '🌐', description: 'gRPC for browser clients' },
  { value: 'MQTT', label: 'MQTT', icon: '📡', description: 'Lightweight IoT messaging' },
  { value: 'TCP', label: 'Raw TCP', icon: '🔗', description: 'Low-level TCP connection' },
  { value: 'UDP', label: 'UDP', icon: '📤', description: 'Fast datagram protocol' },
];

export const EdgeProtocolSelector: React.FC<EdgeProtocolSelectorProps> = ({ 
  protocol, 
  onProtocolChange 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchText('');
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => searchRef.current?.focus(), 0);
    }
  }, [isOpen]);

  const filteredProtocols = PROTOCOLS.filter(p => 
    p.value.toLowerCase().includes(searchText.toLowerCase()) ||
    p.description.toLowerCase().includes(searchText.toLowerCase())
  );

  const handleSelect = (value: string) => {
    onProtocolChange(value);
    setIsOpen(false);
    setSearchText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setSearchText('');
    }
  };

  const dropdownContent = (
    <div
      ref={dropdownRef}
      className="fixed z-[9999] w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg overflow-hidden animate-in fade-in slide-in-from-top-2"
      onKeyDown={handleKeyDown}
    >
      {/* Search */}
      <div className="p-2 border-b border-slate-100 dark:border-slate-800">
        <input
          ref={searchRef}
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onKeyDown={(e) => { e.stopPropagation(); }}
          placeholder="Search protocols..."
          className="w-full px-2 py-1.5 text-xs text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Protocol List */}
      <div className="max-h-64 overflow-y-auto py-1">
        {filteredProtocols.map((p) => (
          <button
            key={p.value}
            onClick={() => handleSelect(p.value)}
            onMouseDown={(e) => e.preventDefault()}
            className={`w-full flex items-center gap-2 px-2 py-1.5 text-left transition-colors ${
              protocol === p.value 
                ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' 
                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50'
            }`}
          >
            <span className="text-lg">{p.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-xs truncate">{p.label}</div>
              <div className="text-[9px] text-slate-500 dark:text-slate-400 truncate">{p.description}</div>
            </div>
            {protocol === p.value && <span className="text-blue-500 text-xs">✓</span>}
          </button>
        ))}
        {filteredProtocols.length === 0 && (
          <div className="px-2 py-2 text-center text-xs text-slate-500 dark:text-slate-400">
            No protocols match "{searchText}"
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-white/95 backdrop-blur-sm border border-slate-200 text-slate-600 shadow-sm hover:border-blue-400 hover:text-blue-600 transition-colors cursor-pointer select-none"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span>{protocol}</span>
        <ExternalLink className="w-2.5 h-2.5 opacity-60 hover:opacity-100" />
      </button>

      {isOpen && createPortal(dropdownContent, document.body)}
    </>
  );
};