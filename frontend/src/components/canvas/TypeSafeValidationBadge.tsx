import React from 'react';
import { Shield, AlertCircle, CheckCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';

interface TypeSafeValidationBadgeProps {
  validation: any;
  className?: string;
}

export const TypeSafeValidationBadge: React.FC<TypeSafeValidationBadgeProps> = ({ 
  validation, 
  className = '' 
}) => {
  if (!validation) return null;

  const gates = validation.gates || {};
  const scores = validation.scores || {};
  const classifications = validation.classifications || {};
  const recommendations = validation.recommendations || [];
  
  const totalGates = Object.keys(gates).length;
  const passedGates = Object.values(gates).filter((g: any) => g.passed).length;
  const failedGates = totalGates - passedGates;
  
  const avgScore = Object.keys(scores).length > 0
    ? Object.values(scores).reduce((acc: number, s: any) => acc + (s.value || 0), 0) / Object.keys(scores).length
    : 0;

  const isAllPassed = failedGates === 0;
  const [isExpanded, setIsExpanded] = React.useState(false);

  const getScoreColor = (score: number) => {
    if (score >= 3.5) return 'text-green-600';
    if (score >= 2.5) return 'text-yellow-600';
    if (score >= 1.5) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 3.5) return 'Excellent';
    if (score >= 2.5) return 'Good';
    if (score >= 1.5) return 'Fair';
    return 'Poor';
  };

  return (
    <div className={`fixed top-4 right-4 z-20 ${className}`}>
      <div className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg overflow-hidden min-w-[280px] animate-in slide-in-from-top-2">
        {/* Header */}
        <div className={`flex items-center gap-2 p-3 ${isAllPassed ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'} border-b border-slate-200 dark:border-slate-700`}>
          <div className={`p-1.5 rounded-lg ${isAllPassed ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
            {isAllPassed ? <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" /> : <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-xs text-slate-800 dark:text-slate-200 truncate">TypeSafe Validation</div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400">
              {isAllPassed ? 'All gates passed' : `${failedGates} of ${totalGates} gates failed`}
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${getScoreColor(avgScore)} bg-opacity-10`}>
              {avgScore.toFixed(1)}/4.0
            </span>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="p-3 space-y-3 max-h-[400px] overflow-y-auto">
            {/* Gates */}
            {totalGates > 0 && (
              <div>
                <div className="flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">
                  <span>Quality Gates</span>
                  <span className={`font-mono ${passedGates === totalGates ? 'text-green-600' : 'text-red-600'}`}>
                    {passedGates}/{totalGates}
                  </span>
                </div>
                <div className="space-y-1">
                  {Object.entries(gates).map(([key, gate]: [string, any]) => (
                    <div key={key} className="flex items-center justify-between text-[10px] px-2 py-1 rounded bg-slate-50 dark:bg-slate-800/50">
                      <span className="text-slate-600 dark:text-slate-300 capitalize truncate max-w-[160px]">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className={`font-mono ${gate.passed ? 'text-green-600' : 'text-red-600'}`}>
                        {gate.passed ? '✓ Pass' : '✗ Fail'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Classifications */}
            {Object.keys(classifications).length > 0 && (
              <div className="border-t border-slate-200 dark:border-slate-700 pt-3">
                <div className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">Classifications</div>
                <div className="space-y-1">
                  {Object.entries(classifications).map(([key, cls]: [string, any]) => (
                    <div key={key} className="text-[10px] text-slate-600 dark:text-slate-300">
                      <span className="font-medium capitalize">{key.replace(/_/g, ' ')}: </span>
                      <span className="text-slate-800 dark:text-slate-200 font-mono">{cls.value}</span>
                      <span className="text-slate-400 ml-1">({(cls.confidence * 100).toFixed(0)}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scores */}
            {Object.keys(scores).length > 0 && (
              <div className="border-t border-slate-200 dark:border-slate-700 pt-3">
                <div className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">Quality Scores</div>
                <div className="space-y-1">
                  {Object.entries(scores).map(([key, score]: [string, any]) => (
                    <div key={key} className="space-y-0.5">
                      <div className="flex justify-between text-[10px]">
                        <span className="text-slate-600 dark:text-slate-300 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className={`${getScoreColor(score.value)} font-mono font-medium`}>
                          {score.value.toFixed(1)}/4.0
                        </span>
                      </div>
                      <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${getScoreColor(score.value).replace('text', 'bg')}`}
                          style={{ width: `${(score.value / 4) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <div className="border-t border-slate-200 dark:border-slate-700 pt-3">
                <div className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">Recommendations</div>
                <div className="space-y-1">
                  {recommendations.slice(0, 5).map((rec: any, idx: number) => (
                    <div key={idx} className="text-[10px] p-2 rounded bg-slate-50 dark:bg-slate-800/50 border-l-2 border-red-500">
                      <div className="flex items-start gap-1.5">
                        <span className="text-red-500 font-bold">•</span>
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-red-700 dark:text-red-400">{rec.action}</span>
                          <div className="text-slate-500 dark:text-slate-400 truncate">{rec.rationale}</div>
                        </div>
                        <span className={`px-1 py-0.5 rounded text-[9px] font-mono ${rec.priority === 'critical' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                          {rec.priority}
                        </span>
                      </div>
                    </div>
                  ))}
                  {recommendations.length > 5 && (
                    <div className="text-[10px] text-slate-500 text-center py-1">
                      +{recommendations.length - 5} more...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Also export a compact inline version for nodes
export const TypeSafeNodeIndicator: React.FC<{ validation: any }> = ({ validation }) => {
  if (!validation) return null;
  
  const gates = validation.gates || {};
  const failedGates = Object.values(gates).filter((g: any) => !g.passed).length;
  
  if (failedGates === 0) return null;
  
  return (
    <div className="absolute -top-2 -right-2 z-10">
      <div className="bg-red-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full shadow-lg flex items-center gap-1 animate-pulse">
        <AlertCircle className="w-2.5 h-2.5" />
        {failedGates}
      </div>
    </div>
  );
};