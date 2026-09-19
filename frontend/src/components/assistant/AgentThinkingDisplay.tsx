import React, { useState, useEffect } from 'react';
import { Brain, Zap, CheckCircle, AlertCircle, Clock, Cpu, GitBranch, Layers, ArrowRight, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { AgentThinkingStep } from '../../types/architecture';

interface AgentThinkingDisplayProps {
  thinkingSteps: AgentThinkingStep[];
  messageId: string;
}

const AGENT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  repo_fetcher: GitBranch,
  architecture_analyst: Layers,
  diagram_builder: Cpu,
};

const AGENT_NAMES: Record<string, string> = {
  repo_fetcher: 'Repo Fetcher',
  architecture_analyst: 'Architecture Analyst',
  diagram_builder: 'Diagram Builder',
};

const AGENT_COLORS: Record<string, string> = {
  repo_fetcher: 'blue',
  architecture_analyst: 'purple',
  diagram_builder: 'green',
};

const STATUS_CONFIG = {
  starting: { icon: Clock, className: 'animate-spin text-slate-500', label: 'Starting' },
  running: { icon: Cpu, className: 'animate-pulse text-blue-600', label: 'Running' },
  completed: { icon: CheckCircle, className: 'text-green-600', label: 'Completed' },
  failed: { icon: AlertCircle, className: 'text-red-600', label: 'Failed' },
};

export const AgentThinkingDisplay: React.FC<AgentThinkingDisplayProps> = ({ 
  thinkingSteps, 
  messageId 
}) => {
  if (!thinkingSteps || thinkingSteps.length === 0) return null;

  const [isExpanded, setIsExpanded] = useState(false);
  const [showDetails, setShowDetails] = useState<Record<number, boolean>>({});

  const completedSteps = thinkingSteps.filter(s => s.status === 'completed' || s.status === 'failed').length;
  const totalSteps = thinkingSteps.length;
  const hasRunning = thinkingSteps.some(s => s.status === 'running' || s.status === 'starting');
  const allCompleted = completedSteps === totalSteps && totalSteps > 0;

  // Auto-expand when running, collapse when all completed
  useEffect(() => {
    if (hasRunning) {
      setIsExpanded(true);
    } else if (allCompleted && !hasRunning) {
      // Keep expanded for a moment then allow collapse
    }
  }, [hasRunning, allCompleted]);

  return (
    <div className="mt-2 ml-10 border-l-2 border-slate-200 pl-3 space-y-2 animate-in fade-in slide-in-from-top-2">
      {/* Summary Header - Always visible */}
      <div className="flex items-center gap-2 text-xs">
        <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
          <Brain className="w-3.5 h-3.5 text-purple-600" />
          <span className="font-medium text-slate-700">Agent Pipeline</span>
          <span className="text-slate-400 px-1.5 py-0.5 rounded bg-slate-100 font-mono">
            {completedSteps}/{totalSteps} 
            {hasRunning ? (
              <span className="flex items-center gap-1 text-blue-600">
                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                Running...
              </span>
            ) : allCompleted ? (
              <span className="text-green-600">✓ Complete</span>
            ) : (
              '• Ready'
            )}
          </span>
        </div>
        <ChevronDown 
          className={`ml-auto w-3.5 h-3.5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </div>

      {/* Expandable Details */}
      <div className={`overflow-hidden transition-all duration-200 ${isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
        <div className="space-y-2 mt-1">
          {thinkingSteps.map((step, idx) => (
            <AgentStepCard 
              key={`${step.agent}-${step.timestamp}-${idx}`}
              step={step}
              index={idx}
              showDetails={showDetails[idx]}
              onToggleDetails={() => setShowDetails(prev => ({ ...prev, [idx]: !prev[idx] }))}
            />
          ))}

          {/* Consensus info if available */}
          {thinkingSteps.some(s => s.agent === 'consensus') && (
            <div className="mt-2 p-2 bg-purple-50 border border-purple-200 rounded-lg animate-in">
              <div className="flex items-center gap-1.5 text-xs text-purple-800">
                <GitBranch className="w-3.5 h-3.5" />
                <span className="font-medium">Consensus Reached</span>
              </div>
            </div>
          )}

          {/* Completion badge */}
          {allCompleted && !hasRunning && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-lg animate-in flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-xs font-medium text-green-800">All agents completed</div>
                <div className="text-[9px] text-green-600">Click to collapse</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const AgentStepCard: React.FC<{ 
  step: AgentThinkingStep; 
  index: number;
  showDetails: boolean;
  onToggleDetails: () => void;
}> = ({ step, index, showDetails, onToggleDetails }) => {
  const Icon = AGENT_ICONS[step.agent] || Brain;
  const agentName = AGENT_NAMES[step.agent] || step.agentName || step.agent;
  const color = AGENT_COLORS[step.agent] || 'slate';
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    purple: 'bg-purple-50 border-purple-200 text-purple-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    slate: 'bg-slate-50 border-slate-200 text-slate-800',
  };

  const statusConfig = STATUS_CONFIG[step.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.starting;
  const StatusIcon = statusConfig.icon;

  return (
    <div className={`rounded-lg border p-2.5 transition-all ${colorClasses[color as keyof typeof colorClasses]}`}>
      {/* Step Header - Always visible */}
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5" />
          <span className="font-medium text-xs">{agentName}</span>
          {step.modelUsed && (
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/70">
              {step.modelFallback ? '↻ ' : ''}{step.modelUsed}
            </span>
          )}
        </div>
        <span className="ml-auto flex items-center gap-1">
          <StatusIcon className={`w-3.5 h-3.5 ${statusConfig.className}`} />
          <span className="text-[10px] font-mono capitalize">{statusConfig.label}</span>
          {step.confidence !== undefined && (
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-white/70">
              {Math.round(step.confidence * 100)}%
            </span>
          )}
        </span>
      </div>

      {/* Expandable Details */}
      <button
        onClick={onToggleDetails}
        className="w-full text-left flex items-center gap-1.5 text-[9px] text-current/70 hover:text-current py-1"
      >
        <span>{showDetails ? 'Hide details' : 'Show details'}</span>
        <ChevronDown className={`w-2.5 h-2.5 transition-transform ${showDetails ? 'rotate-180' : ''}`} />
      </button>

      {showDetails && (
        <div className="mt-1.5 space-y-1.5 animate-in slide-in-from-top-2">
          {/* Reasoning */}
          {step.reasoning && (
            <div className="text-[10px] leading-relaxed whitespace-pre-wrap bg-white/50 p-2 rounded border border-white/50">
              {step.reasoning}
            </div>
          )}

          {/* Tool Calls */}
          {step.toolCalls && step.toolCalls.length > 0 && (
            <div className="space-y-1 ml-2 border-l border-white/50 pl-2">
              <div className="text-[9px] font-medium text-current/60">Tools Used</div>
              {step.toolCalls.map((tc, tcIdx) => (
                <div key={tcIdx} className="flex items-center gap-1.5 text-[9px]">
                  <ArrowRight className="w-2.5 h-2.5 text-current/60" />
                  <span className="font-mono">{tc.tool}</span>
                  <span className={`px-1 py-0.5 rounded text-[8px] ${tc.result === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {tc.result}
                  </span>
                  {tc.durationMs && (
                    <span className="text-current/50 font-mono">{tc.durationMs}ms</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Output Preview */}
          {step.outputPreview && step.status === 'completed' && (
            <details className="mt-1.5 group">
              <summary className="flex items-center gap-1 text-[9px] text-current/70 cursor-pointer hover:text-current">
                <Zap className="w-2.5 h-2.5" />
                Output Preview
                <ChevronDown className="w-2.5 h-2.5 transition-transform group-open:rotate-180" />
              </summary>
              <div className="mt-1.5 p-2 bg-white/50 rounded text-[9px] font-mono whitespace-pre-wrap overflow-x-auto max-h-24 overflow-y-auto border border-white/50">
                {step.outputPreview}
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
};

// Live thinking indicator for when orchestration is in progress
export const LiveAgentThinking: React.FC<{ 
  currentAgent?: string; 
  step?: string;
  modelUsed?: string;
}> = ({ currentAgent, step, modelUsed }) => {
  if (!currentAgent) return null;

  const Icon = AGENT_ICONS[currentAgent] || Brain;
  const agentName = AGENT_NAMES[currentAgent] || currentAgent;

  return (
    <div className="flex items-center gap-2 ml-10 p-2 bg-purple-50 border border-purple-200 rounded-lg animate-pulse">
      <Icon className="w-4 h-4 text-purple-600 animate-spin" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 text-xs">
          <span className="font-medium text-purple-800">{agentName}</span>
          <span className="text-purple-600">•</span>
          <span className="text-purple-700">{step || 'Processing...'}</span>
        </div>
        {modelUsed && (
          <div className="text-[9px] text-purple-500 font-mono">Model: {modelUsed}</div>
        )}
      </div>
    </div>
  );
};