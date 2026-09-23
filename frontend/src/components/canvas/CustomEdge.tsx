import React, { memo, useState, useRef, useEffect } from 'react';
import { EdgeProps, getSmoothStepPath, useReactFlow } from '@xyflow/react';
import { ArchitectureEdge } from '../../types/architecture';
import { createPortal } from 'react-dom';

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

interface EdgeProtocolDropdownProps {
  protocol: string;
  onChange: (value: string) => void;
  onClose: () => void;
  anchorEl: { x: number; y: number } | null;
}

const EdgeProtocolDropdown: React.FC<EdgeProtocolDropdownProps> = ({ 
  protocol, 
  onChange, 
  onClose,
  anchorEl 
}) => {
  const [searchText, setSearchText] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const justOpenedRef = useRef(true);

  useEffect(() => {
    justOpenedRef.current = true;
    const timer = setTimeout(() => {
      justOpenedRef.current = false;
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (justOpenedRef.current) return;
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  useEffect(() => {
    setTimeout(() => searchRef.current?.focus(), 0);
  }, []);

  const filteredProtocols = PROTOCOLS.filter(p => 
    p.value.toLowerCase().includes(searchText.toLowerCase()) ||
    p.description.toLowerCase().includes(searchText.toLowerCase())
  );

  const handleSelect = (value: string) => {
    onChange(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!anchorEl) return null;

  const dropdownContent = (
    <div
      ref={dropdownRef}
      className="fixed z-[9999] w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg overflow-hidden animate-in fade-in slide-in-from-top-2"
      onKeyDown={handleKeyDown}
      style={{
        left: `${anchorEl.x}px`,
        top: `${anchorEl.y}px`,
        transform: 'translate(-50%, -100%)',
      }}
    >
      <div className="p-2 border-b border-slate-100 dark:border-slate-800">
        <input
          ref={searchRef}
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onKeyDown={(e) => e.stopPropagation()}
          placeholder="Search protocols..."
          className="w-full px-2 py-1.5 text-xs text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div className="max-h-64 overflow-y-auto py-1">
        {PROTOCOLS.filter(p => 
          p.value.toLowerCase().includes(searchText.toLowerCase()) ||
          p.description.toLowerCase().includes(searchText.toLowerCase())
        ).map((p) => (
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
      </div>
    </div>
  );

  return createPortal(dropdownContent, document.body);
};

export const CustomEdge = memo((props: EdgeProps<ArchitectureEdge>) => {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data,
    label,
    animated,
  } = props;

  const { screenToFlowPosition } = useReactFlow();
  const [showSelector, setShowSelector] = useState<string | null>(null);
  const dropdownAnchorRef = useRef<{ x: number; y: number } | null>(null);
  const [anchorPos, setAnchorPos] = useState<{ x: number; y: number } | null>(null);

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
  });

  // Ensure protocol is always a string, fallback to 'Unknown' if neither protocol nor label available
  // Always ensure we have a valid string for protocol
  const rawProtocol = data?.protocol || (typeof label === 'string' ? label : (label ? String(label) : ''));
  const protocol = rawProtocol || 'Unknown';

  const handleProtocolChange = (newProtocol: string) => {
    window.dispatchEvent(new CustomEvent('edge-protocol-change', {
      detail: { edgeId: id, newProtocol }
    }));
    setShowSelector(null);
    setAnchorPos(null);
  };

  const flowPos = screenToFlowPosition({ x: labelX, y: labelY });

  return (
    <>
      <path
        id={id}
        style={{
          ...style,
          strokeWidth: 2,
          stroke: '#94A3B8',
        }}
        className={`react-flow__edge-path transition-colors hover:!stroke-blue-500 ${
          animated ? 'stroke-dash-animated' : ''
        }`}
        d={edgePath}
        markerEnd={markerEnd}
      />

      {protocol && (
        <>
          <div
            style={{
              position: 'absolute',
              left: `${flowPos.x}px`,
              top: `${flowPos.y}px`,
              transform: 'translate(-50%, -50%)',
              pointerEvents: 'auto',
              zIndex: 1000,
            }}
            className="nodrag nopan"
            onMouseDown={(e) => e.stopPropagation()}
            onTouchStart={(e) => e.stopPropagation()}
          >
            <button
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                const buttonRect = (e.currentTarget as HTMLButtonElement).getBoundingClientRect();
                const anchor = {
                  x: buttonRect.left + buttonRect.width / 2,
                  y: buttonRect.top - 8,
                };
                dropdownAnchorRef.current = anchor;
                setAnchorPos(anchor);
                setShowSelector(id);
              }}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-white/95 backdrop-blur-sm border border-slate-200 text-slate-600 shadow-sm hover:border-blue-400 hover:text-blue-600 transition-colors cursor-pointer select-none"
            >
              <span>{protocol}</span>
            </button>
            {showSelector === id && anchorPos && (
              <EdgeProtocolDropdown
                protocol={protocol}
                onChange={handleProtocolChange}
                onClose={() => { setShowSelector(null); setAnchorPos(null); }}
                anchorEl={anchorPos}
              />
            )}
          </div>
        </>
      )}
    </>
  );
});

export default CustomEdge;