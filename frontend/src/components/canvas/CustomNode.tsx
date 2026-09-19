import React, { memo } from 'react';
import { Handle, Position, NodeProps, useStore } from '@xyflow/react';
import {
  Network,
  Split,
  Globe,
  ShieldCheck,
  ShoppingCart,
  Users,
  Search,
  Bell,
  Database,
  FileSpreadsheet,
  Layers,
  Zap,
  Flame,
  Radio,
  FastForward,
  HardDrive,
  Laptop,
  Smartphone,
  Server,
  AlertTriangle,
  Cpu,
  Activity,
} from 'lucide-react';
import { ArchitectureNode, ComponentCategory } from '../../types/architecture';

const CATEGORY_STYLES: Record<
  ComponentCategory,
  {
    border: string;
    bgBadge: string;
    textBadge: string;
    iconBg: string;
    iconColor: string;
    accentGlow: string;
    dark: {
      border: string;
      bgBadge: string;
      textBadge: string;
      iconBg: string;
      iconColor: string;
      accentGlow: string;
    }
  }
> = {
  service: {
    border: 'border-blue-400 hover:border-blue-500',
    bgBadge: 'bg-blue-50',
    textBadge: 'text-blue-700 border-blue-200',
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-600',
    accentGlow: 'hover:shadow-blue-100',
    dark: {
      border: 'border-blue-500 hover:border-blue-400',
      bgBadge: 'bg-blue-900/30',
      textBadge: 'text-blue-300 border-blue-700',
      iconBg: 'bg-blue-500/20',
      iconColor: 'text-blue-400',
      accentGlow: 'hover:shadow-blue-900/30',
    }
  },
  database: {
    border: 'border-emerald-400 hover:border-emerald-500',
    bgBadge: 'bg-emerald-50',
    textBadge: 'text-emerald-700 border-emerald-200',
    iconBg: 'bg-emerald-500/10',
    iconColor: 'text-emerald-600',
    accentGlow: 'hover:shadow-emerald-100',
    dark: {
      border: 'border-emerald-500 hover:border-emerald-400',
      bgBadge: 'bg-emerald-900/30',
      textBadge: 'text-emerald-300 border-emerald-700',
      iconBg: 'bg-emerald-500/20',
      iconColor: 'text-emerald-400',
      accentGlow: 'hover:shadow-emerald-900/30',
    }
  },
  queue: {
    border: 'border-purple-400 hover:border-purple-500',
    bgBadge: 'bg-purple-50',
    textBadge: 'text-purple-700 border-purple-200',
    iconBg: 'bg-purple-500/10',
    iconColor: 'text-purple-600',
    accentGlow: 'hover:shadow-purple-100',
    dark: {
      border: 'border-purple-500 hover:border-purple-400',
      bgBadge: 'bg-purple-900/30',
      textBadge: 'text-purple-300 border-purple-700',
      iconBg: 'bg-purple-500/20',
      iconColor: 'text-purple-400',
      accentGlow: 'hover:shadow-purple-900/30',
    }
  },
  gateway: {
    border: 'border-orange-400 hover:border-orange-500',
    bgBadge: 'bg-orange-50',
    textBadge: 'text-orange-700 border-orange-200',
    iconBg: 'bg-orange-500/10',
    iconColor: 'text-orange-600',
    accentGlow: 'hover:shadow-orange-100',
    dark: {
      border: 'border-orange-500 hover:border-orange-400',
      bgBadge: 'bg-orange-900/30',
      textBadge: 'text-orange-300 border-orange-700',
      iconBg: 'bg-orange-500/20',
      iconColor: 'text-orange-400',
      accentGlow: 'hover:shadow-orange-900/30',
    }
  },
  cache: {
    border: 'border-amber-400 hover:border-amber-500',
    bgBadge: 'bg-amber-50',
    textBadge: 'text-amber-700 border-amber-200',
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-600',
    accentGlow: 'hover:shadow-amber-100',
    dark: {
      border: 'border-amber-500 hover:border-amber-400',
      bgBadge: 'bg-amber-900/30',
      textBadge: 'text-amber-300 border-amber-700',
      iconBg: 'bg-amber-500/20',
      iconColor: 'text-amber-400',
      accentGlow: 'hover:shadow-amber-900/30',
    }
  },
  api: {
    border: 'border-cyan-400 hover:border-cyan-500',
    bgBadge: 'bg-cyan-50',
    textBadge: 'text-cyan-700 border-cyan-200',
    iconBg: 'bg-cyan-500/10',
    iconColor: 'text-cyan-600',
    accentGlow: 'hover:shadow-cyan-100',
    dark: {
      border: 'border-cyan-500 hover:border-cyan-400',
      bgBadge: 'bg-cyan-900/30',
      textBadge: 'text-cyan-300 border-cyan-700',
      iconBg: 'bg-cyan-500/20',
      iconColor: 'text-cyan-400',
      accentGlow: 'hover:shadow-cyan-900/30',
    }
  },
  storage: {
    border: 'border-slate-400 hover:border-slate-500',
    bgBadge: 'bg-slate-100',
    textBadge: 'text-slate-700 border-slate-300',
    iconBg: 'bg-slate-500/10',
    iconColor: 'text-slate-600',
    accentGlow: 'hover:shadow-slate-200',
    dark: {
      border: 'border-slate-500 hover:border-slate-400',
      bgBadge: 'bg-slate-700',
      textBadge: 'text-slate-300 border-slate-600',
      iconBg: 'bg-slate-500/20',
      iconColor: 'text-slate-400',
      accentGlow: 'hover:shadow-slate-700',
    }
  },
};

export const CustomNode = memo(({ data, selected }: NodeProps<ArchitectureNode>) => {
  const zoom = useStore((s) => s.transform[2]);

  const category = data.category || 'service';
  const style = CATEGORY_STYLES[category] || CATEGORY_STYLES.service;
  const isDark = document.documentElement.classList.contains('dark');
  const s = isDark ? style.dark : style;
  
  const isOverloaded = data.status === 'overloaded';
  const isWarning = data.status === 'warning';

  // Semantic Zoom Levels
  const isLowZoom = zoom < 0.5;
  const isHighZoom = zoom > 0.8;

  // Icon selection
  let IconComponent = Server;
  if (category === 'database') IconComponent = Database;
  else if (category === 'queue') IconComponent = Radio;
  else if (category === 'cache') IconComponent = Zap;
  else if (category === 'gateway') IconComponent = Split;
  else if (category === 'api') IconComponent = Laptop;
  else if (category === 'storage') IconComponent = HardDrive;

  // Calculate capacity percentage
  const utilization = data.utilization ?? Math.min(100, Math.round(((data.rps || 0) / (data.capacity || 1)) * 100));

  // Determine dynamic border & pulse styles
  let containerBorder = style.border;
  let containerShadow = 'shadow-sm';
  let pulseClass = '';

  if (isOverloaded) {
    containerBorder = 'border-red-500';
    containerShadow = 'shadow-lg shadow-red-200';
    pulseClass = 'animate-pulse-danger ring-2 ring-red-400';
  } else if (isWarning) {
    containerBorder = 'border-amber-500';
    containerShadow = 'shadow-md shadow-amber-100';
    pulseClass = 'ring-2 ring-amber-300';
} else if (selected) {
    containerBorder = isDark ? 'border-slate-300 ring-2 ring-slate-400' : 'border-slate-800 ring-2 ring-slate-400';
  }

  // Handle styles
  const handleStyle = '!w-2.5 !h-2.5 !bg-slate-400 !border-2 !border-white hover:!bg-blue-600 dark:!bg-slate-500 dark:hover:!bg-blue-500 transition-colors';

  // LOW ZOOM VIEW (< 0.5x)
  if (isLowZoom) {
    return (
      <div
        className={`relative rounded-xl border bg-white dark:bg-slate-800 px-3 py-2 transition-all ${containerBorder} ${containerShadow} ${pulseClass} min-w-[140px] flex items-center gap-2`}
      >
        <Handle type="target" position={Position.Top} className={handleStyle} />
        <Handle type="target" position={Position.Left} className={handleStyle} />

        <div className={`p-1.5 rounded-lg ${s.iconBg} ${s.iconColor} shrink-0`}>
          <IconComponent className="w-4 h-4" />
        </div>
      <div className="truncate">
        <p className="font-semibold text-xs text-slate-800 dark:text-slate-200 truncate">{data.label}</p>
        <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">{data.tech || category}</span>
      </div>

        {isOverloaded && (
          <div className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-0.5">
            <AlertTriangle className="w-3 h-3" />
          </div>
        )}

        <Handle type="source" position={Position.Right} className={handleStyle} />
        <Handle type="source" position={Position.Bottom} className={handleStyle} />
      </div>
    );
  }

  // MID ZOOM (0.5x - 0.8x) AND HIGH ZOOM (> 0.8x)
  return (
    <div
      className={`group relative rounded-xl border bg-white dark:bg-slate-800 transition-all ${containerBorder} ${containerShadow} ${pulseClass} min-w-[260px] max-w-[300px] overflow-hidden`}
    >
      {/* Target connection handles */}
      <Handle type="target" position={Position.Top} className={handleStyle} id="t-top" />
      <Handle type="target" position={Position.Left} className={handleStyle} id="t-left" />

      {/* Top Header Card */}
      <div className="p-3 bg-gradient-to-b from-slate-50/80 dark:from-slate-800/80 to-white dark:to-slate-800 border-b border-slate-100 dark:border-slate-700 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${s.iconBg} ${s.iconColor} transition-transform group-hover:scale-105`}>
            <IconComponent className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-200 leading-tight">{data.label}</h3>
            <span className="inline-block font-mono text-[11px] text-slate-500 dark:text-slate-400 font-medium">
              {data.tech || category}
            </span>
          </div>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-1 shrink-0">
          {isOverloaded ? (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
              <AlertTriangle className="w-2.5 h-2.5" />
              100%+
            </span>
          ) : isWarning ? (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full">
              <Activity className="w-2.5 h-2.5" />
              {utilization}%
            </span>
          ) : (
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border uppercase tracking-wider font-mono ${s.bgBadge} ${s.textBadge}`}>
              {category}
            </span>
          )}
        </div>
      </div>

      {/* Mid Zoom Standard Body */}
      <div className="p-3 space-y-2.5">
        {/* RPS & Utilization Gauge */}
        <div>
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-slate-500 dark:text-slate-400 font-medium">Traffic / Capacity</span>
            <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
              {data.rps?.toLocaleString() || 0} <span className="text-slate-400 dark:text-slate-500 font-normal">/ {data.capacity?.toLocaleString()} rps</span>
            </span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                isOverloaded
                  ? 'bg-red-500'
                  : isWarning
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, utilization)}%` }}
            />
          </div>
        </div>

        {/* HIGH ZOOM VIEW (> 0.8x): DEEP CONFIGURATION SPECS */}
        {isHighZoom && (
          <div className="pt-2 border-t border-slate-100 dark:border-slate-700 space-y-2 text-[11px]">
            <div className="grid grid-cols-2 gap-2 text-slate-600 dark:text-slate-400">
              <div className="bg-slate-50 dark:bg-slate-700/50 p-1.5 rounded border border-slate-100 dark:border-slate-600">
                <span className="block text-[9px] text-slate-400 dark:text-slate-500 uppercase font-mono">Latency</span>
                <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                  {data.effectiveLatency ?? data.latency ?? 20} ms
                </span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-700/50 p-1.5 rounded border border-slate-100 dark:border-slate-600">
                <span className="block text-[9px] text-slate-400 dark:text-slate-500 uppercase font-mono">Fail Rate</span>
                <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                  {data.effectiveErrorRate ?? data.failureRate ?? 0.1}%
                </span>
              </div>
            </div>

            {data.replication && (
              <div className="bg-slate-50 dark:bg-slate-700/50 p-1.5 rounded border border-slate-100 dark:border-slate-600 text-[10px]">
                <span className="block text-[9px] text-slate-400 dark:text-slate-500 uppercase font-mono">Replication</span>
                <span className="text-slate-700 dark:text-slate-300 font-medium truncate block">{data.replication}</span>
              </div>
            )}

            {data.explanation && (
              <div className="p-2 rounded bg-blue-50/60 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 text-[10px] text-slate-600 dark:text-slate-400 leading-relaxed">
                <span className="font-semibold text-blue-800 dark:text-blue-400 block mb-0.5">Architectural Note:</span>
                {data.explanation}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Source connection handles */}
      <Handle type="source" position={Position.Right} className={handleStyle} id="s-right" />
      <Handle type="source" position={Position.Bottom} className={handleStyle} id="s-bottom" />
    </div>
  );
});
