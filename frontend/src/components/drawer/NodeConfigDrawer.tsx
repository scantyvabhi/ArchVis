import React, { useState, useEffect } from 'react';
import { X, Trash2, Save, Cpu, Gauge, AlertCircle, RefreshCw } from 'lucide-react';
import { ArchitectureNode, ComponentCategory } from '../../types/architecture';

interface NodeConfigDrawerProps {
  selectedNode: ArchitectureNode | null;
  onClose: () => void;
  onUpdateNode: (id: string, updatedData: any) => void;
  onDeleteNode: (id: string) => void;
}

export const NodeConfigDrawer: React.FC<NodeConfigDrawerProps> = ({
  selectedNode,
  onClose,
  onUpdateNode,
  onDeleteNode,
}) => {
  const [formData, setFormData] = useState<any>(null);
  const isDark = document.documentElement.classList.contains('dark');

  useEffect(() => {
    if (selectedNode) {
      setFormData({
        label: selectedNode.data.label || '',
        category: selectedNode.data.category || 'service',
        tech: selectedNode.data.tech || '',
        latency: selectedNode.data.latency ?? 20,
        rps: selectedNode.data.rps ?? 1000,
        capacity: selectedNode.data.capacity ?? 5000,
        failureRate: selectedNode.data.failureRate ?? 0.1,
        replication: selectedNode.data.replication || '',
        description: selectedNode.data.description || '',
        explanation: selectedNode.data.explanation || '',
      });
    } else {
      setFormData(null);
    }
  }, [selectedNode]);

  if (!selectedNode || !formData) return null;

  const handleChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    onUpdateNode(selectedNode.id, formData);
  };

  const handleDelete = () => {
    onDeleteNode(selectedNode.id);
    onClose();
  };

  const bg = isDark ? 'bg-slate-900/98' : 'bg-white/98';
  const border = isDark ? 'border-slate-700' : 'border-slate-200';
  const headerBg = isDark ? 'bg-slate-800/70' : 'bg-slate-50/70';
  const textPrimary = isDark ? 'text-slate-100' : 'text-slate-800';
  const textSecondary = isDark ? 'text-slate-400' : 'text-slate-500';
  const textMuted = isDark ? 'text-slate-500' : 'text-slate-600';
  const inputBg = isDark ? 'bg-slate-800' : 'bg-slate-50';
  const inputFocusBg = isDark ? 'focus:bg-slate-800' : 'focus:bg-white';
  const inputBorder = isDark ? 'border-slate-700' : 'border-slate-200';
  const inputText = isDark ? 'text-slate-100' : 'text-slate-800';
  const cardBg = isDark ? 'bg-slate-800' : 'bg-slate-50';
  const cardBorder = isDark ? 'border-slate-700' : 'border-slate-200';
  const footerBg = isDark ? 'bg-slate-800/80' : 'bg-slate-50/80';
  const hoverBg = isDark ? 'hover:bg-slate-700' : 'hover:bg-slate-200';
  const hoverText = isDark ? 'hover:text-slate-100' : 'hover:text-slate-900';
  const accentBg = isDark ? 'bg-blue-900/30' : 'bg-blue-100';
  const accentText = isDark ? 'text-blue-400' : 'text-blue-600';
  const dangerBg = isDark ? 'bg-red-900/30' : 'bg-red-50';
  const dangerText = isDark ? 'text-red-400' : 'text-red-600';
  const dangerHoverBg = isDark ? 'hover:bg-red-900/50' : 'hover:bg-red-50';
  const dangerHoverText = isDark ? 'hover:text-red-300' : 'hover:text-red-700';

  return (
    <div className={`fixed inset-y-0 right-0 w-96 ${bg} backdrop-blur-md shadow-2xl ${border} z-30 flex flex-col transition-all duration-300`}>
      {/* Drawer Header */}
      <div className={`p-4 ${border} flex items-center justify-between ${headerBg}`}>
        <div className="flex items-center gap-2">
          <div className={`p-1.5 ${accentBg} ${accentText} rounded-md`}>
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className={`font-semibold text-sm ${textPrimary}`}>Node Configuration</h3>
            <p className={`text-[11px] font-mono ${textMuted}`}>ID: {selectedNode.id}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className={`p-1.5 ${textMuted} ${hoverText} ${hoverBg} rounded-md transition-colors`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Component Label & Tech */}
        <div className="space-y-3">
          <div>
            <label className={`block ${textMuted} font-medium mb-1`}>Component Name</label>
            <input
              type="text"
              value={formData.label}
              onChange={(e) => handleChange('label', e.target.value)}
              className={`w-full px-3 py-1.5 ${inputBg} ${inputBorder} rounded-md ${inputFocusBg} focus:ring-1 focus:ring-blue-500 focus:outline-none ${inputText}`}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block ${textMuted} font-medium mb-1`}>Category</label>
              <select
                value={formData.category}
                onChange={(e) => handleChange('category', e.target.value as ComponentCategory)}
                className={`w-full px-2 py-1.5 ${inputBg} ${inputBorder} rounded-md ${inputFocusBg} focus:ring-1 focus:ring-blue-500 focus:outline-none text-xs ${inputText}`}
              >
                <option value="api">API / Client</option>
                <option value="gateway">Gateway / LB</option>
                <option value="service">Microservice</option>
                <option value="database">Database</option>
                <option value="cache">Cache</option>
                <option value="queue">Message Queue</option>
                <option value="storage">Storage</option>
              </select>
            </div>

            <div>
              <label className={`block ${textMuted} font-medium mb-1`}>Tech Stack</label>
              <input
                type="text"
                value={formData.tech}
                placeholder="e.g. Redis, Kafka, Go"
                onChange={(e) => handleChange('tech', e.target.value)}
                className={`w-full px-3 py-1.5 ${inputBg} ${inputBorder} rounded-md ${inputFocusBg} focus:ring-1 focus:ring-blue-500 focus:outline-none ${inputText}`}
              />
            </div>
          </div>
        </div>

        {/* Simulation Parameter Controls */}
        <div className={`p-3 rounded-lg ${cardBorder} ${cardBg} space-y-3`}>
          <div className={`flex items-center gap-1.5 ${textPrimary} font-semibold ${border} pb-1.5 border-b`}>
            <Gauge className="w-3.5 h-3.5 text-blue-600" />
            <span>Simulation Parameters</span>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={`${textMuted}`}>Base Latency (ms)</label>
              <span className={`font-mono font-semibold ${textPrimary}`}>{formData.latency} ms</span>
            </div>
            <input
              type="range"
              min="1"
              max="500"
              value={formData.latency}
              onChange={(e) => handleChange('latency', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={`${textMuted}`}>Request Rate (RPS)</label>
              <span className={`font-mono font-semibold ${textPrimary}`}>{formData.rps.toLocaleString()}</span>
            </div>
            <input
              type="range"
              min="100"
              max="50000"
              step="100"
              value={formData.rps}
              onChange={(e) => handleChange('rps', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={`${textMuted}`}>Max Capacity (RPS)</label>
              <span className={`font-mono font-semibold ${textPrimary}`}>{formData.capacity.toLocaleString()}</span>
            </div>
            <input
              type="range"
              min="200"
              max="60000"
              step="200"
              value={formData.capacity}
              onChange={(e) => handleChange('capacity', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={`${textMuted}`}>Failure Rate (%)</label>
              <span className={`font-mono font-semibold ${textPrimary}`}>{formData.failureRate}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="15"
              step="0.1"
              value={formData.failureRate}
              onChange={(e) => handleChange('failureRate', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>
        </div>

        {/* High-Level Spec & Replication */}
        <div className="space-y-3">
          <div>
            <label className={`block ${textMuted} font-medium mb-1`}>Replication / High Availability</label>
            <input
              type="text"
              placeholder="e.g. Primary-Replica, Multi-AZ, Raft 3x"
              value={formData.replication}
              onChange={(e) => handleChange('replication', e.target.value)}
              className={`w-full px-3 py-1.5 ${inputBg} ${inputBorder} rounded-md ${inputFocusBg} focus:ring-1 focus:ring-blue-500 focus:outline-none ${inputText}`}
            />
          </div>

          <div>
            <label className={`block ${textMuted} font-medium mb-1`}>Component Description</label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="What this component does in the system..."
              className={`w-full px-3 py-1.5 ${inputBg} ${inputBorder} rounded-md ${inputFocusBg} focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none ${inputText}`}
            />
          </div>

          <div>
            <label className={`block ${textMuted} font-medium mb-1`}>
              Design Rationale (Learner Explanation)
            </label>
            <textarea
              rows={3}
              value={formData.explanation}
              onChange={(e) => handleChange('explanation', e.target.value)}
              placeholder="Why this technology was chosen over alternatives..."
              className={`w-full px-3 py-1.5 ${inputBg} ${inputBorder} rounded-md ${inputFocusBg} focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none ${inputText}`}
            />
          </div>
        </div>
      </div>

      {/* Drawer Footer Actions */}
      <div className={`p-3 ${border} ${footerBg} flex items-center justify-between gap-2`}>
        <button
          onClick={handleDelete}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md ${dangerText} ${dangerHoverText} ${dangerBg} ${dangerHoverBg} transition-colors text-xs font-medium`}
        >
          <Trash2 className="w-3.5 h-3.5" />
          Delete
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={onClose}
            className={`px-3 py-1.5 rounded-md ${textMuted} ${hoverBg} ${hoverText} transition-colors text-xs`}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-sm transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};
