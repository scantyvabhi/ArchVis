import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Clock,
  Zap,
  TrendingUp,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { SimulationMetrics } from '../../types/architecture';

interface MetricsOverlayProps {
  metrics: SimulationMetrics;
  onFocusNode?: (nodeId: string) => void;
}

export const MetricsOverlay: React.FC<MetricsOverlayProps> = ({ metrics, onFocusNode }) => {
  const [collapsed, setCollapsed] = useState(false);

  if (!metrics.isRunning && metrics.totalThroughput === 0) {
    return null;
  }

  const hasBottlenecks = metrics.bottlenecksCount > 0;

  return (
    <div className="absolute top-4 left-4 z-10 bg-white/95 backdrop-blur-md border border-slate-200/90 rounded-xl shadow-lg transition-all duration-200 overflow-hidden min-w-[280px] max-w-sm select-none">
      {/* Header */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        className="px-3.5 py-2.5 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between cursor-pointer hover:bg-slate-100/70 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              metrics.isRunning ? 'bg-emerald-500 animate-ping' : 'bg-slate-400'
            }`}
          />
          <span className="font-semibold text-xs text-slate-800 tracking-tight">
            Live Telemetry Engine
          </span>
        </div>
        <div className="flex items-center gap-2">
          {hasBottlenecks && (
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full animate-pulse">
              <AlertTriangle className="w-3 h-3" />
              {metrics.bottlenecksCount} Bottleneck{metrics.bottlenecksCount > 1 ? 's' : ''}
            </span>
          )}
          <button className="text-slate-400 hover:text-slate-600">
            {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Body Stats */}
      {!collapsed && (
        <div className="p-3.5 space-y-3">
          <div className="grid grid-cols-2 gap-2.5">
            {/* Throughput */}
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase font-mono">
                <TrendingUp className="w-3 h-3 text-blue-500" />
                Throughput
              </div>
              <p className="text-sm font-bold font-mono text-slate-800 mt-1">
                {metrics.totalThroughput.toLocaleString()} <span className="text-[10px] font-normal text-slate-400">rps</span>
              </p>
            </div>

            {/* Average Latency */}
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase font-mono">
                <Clock className="w-3 h-3 text-amber-500" />
                Avg Latency
              </div>
              <p className="text-sm font-bold font-mono text-slate-800 mt-1">
                {metrics.averageLatency} <span className="text-[10px] font-normal text-slate-400">ms</span>
              </p>
            </div>

            {/* P99 Latency */}
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase font-mono">
                <Zap className="w-3 h-3 text-purple-500" />
                P99 Tail Latency
              </div>
              <p className="text-sm font-bold font-mono text-slate-800 mt-1">
                {metrics.p99Latency} <span className="text-[10px] font-normal text-slate-400">ms</span>
              </p>
            </div>

            {/* System Error Rate */}
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase font-mono">
                <Activity
                  className={`w-3 h-3 ${metrics.systemErrorRate > 1 ? 'text-red-500' : 'text-emerald-500'}`}
                />
                Error Rate
              </div>
              <p
                className={`text-sm font-bold font-mono mt-1 ${
                  metrics.systemErrorRate > 1 ? 'text-red-600' : 'text-slate-800'
                }`}
              >
                {metrics.systemErrorRate}%
              </p>
            </div>
          </div>

          {/* Bottlenecks Warning List */}
          {hasBottlenecks && (
            <div className="p-2.5 rounded-lg bg-red-50/80 border border-red-200/70 text-xs">
              <div className="flex items-center gap-1 text-red-800 font-semibold text-[11px] mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                <span>Overloaded Components:</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-1">
                {metrics.overloadedNodes.map((nodeId) => (
                  <button
                    key={nodeId}
                    onClick={() => onFocusNode?.(nodeId)}
                    className="px-2 py-0.5 rounded bg-red-200/70 hover:bg-red-300/80 text-red-900 font-mono text-[10px] font-medium transition-colors"
                  >
                    {nodeId}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-red-600 mt-1.5">
                Incoming traffic exceeds maximum node capacity. Increase node capacity or introduce caching/message queues.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
