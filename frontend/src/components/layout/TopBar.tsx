import React, { useState } from 'react';
import {
  Play,
  Square,
  Trash2,
  Download,
  Upload,
  Sparkles,
  LayoutGrid,
  BookOpen,
  Briefcase,
  Layers,
  ChevronDown,
  Cpu,
  FileCode,
} from 'lucide-react';
import { AppMode } from '../../types/architecture';
import { PRESET_ARCHITECTURES } from '../../constants/presets';

interface TopBarProps {
  mode: AppMode;
  onToggleMode: (newMode: AppMode) => void;
  isSimulating: boolean;
  onToggleSimulation: () => void;
  onClearCanvas: () => void;
  onAutoLayout: () => void;
  onExportPng: () => void;
  onExportJson: () => void;
  onImportJson: (file: File) => void;
  onLoadPreset: (presetId: string) => void;
  backendHealthy: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  mode,
  onToggleMode,
  isSimulating,
  onToggleSimulation,
  onClearCanvas,
  onAutoLayout,
  onExportPng,
  onExportJson,
  onImportJson,
  onLoadPreset,
  backendHealthy,
}) => {
  const [showPresetsMenu, setShowPresetsMenu] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImportJson(file);
    }
  };

  return (
    <header className="h-14 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 flex items-center justify-between z-20 select-none relative">
      {/* Brand / Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-blue-200">
          <Cpu className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-slate-900 tracking-tight">ArchVis AI</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-500 hidden sm:block">AI System Design Visualizer & Simulator</p>
        </div>
      </div>

      {/* Center Controls: Simulation & Mode Switcher */}
      <div className="flex items-center gap-2">
        {/* Run / Stop Simulation Button */}
        <button
          onClick={onToggleSimulation}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium text-xs shadow-xs transition-all ${
            isSimulating
              ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-200'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-200'
          }`}
        >
          {isSimulating ? (
            <>
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop Simulation</span>
              <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Run Simulation</span>
            </>
          )}
        </button>

        {/* Mode Selector Pill */}
        <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200 flex items-center">
          <button
            onClick={() => onToggleMode('learner')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              mode === 'learner'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Learner</span>
          </button>
          <button
            onClick={() => onToggleMode('pro')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              mode === 'pro'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Professional</span>
          </button>
        </div>
      </div>

      {/* Right Controls: Presets, Layout, Export, Clear */}
      <div className="flex items-center gap-2">
        {/* Preset Architectures Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowPresetsMenu(!showPresetsMenu)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-200 transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            <span className="hidden md:inline">Presets</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {showPresetsMenu && (
            <div
              className="absolute right-0 mt-1.5 w-64 bg-white rounded-lg shadow-lg border border-slate-200 py-1.5 z-30 animate-in fade-in"
              onMouseLeave={() => setShowPresetsMenu(false)}
            >
              <div className="px-3 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Architecture Presets
              </div>
              {PRESET_ARCHITECTURES.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => {
                    onLoadPreset(preset.id);
                    setShowPresetsMenu(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-50 transition-colors flex flex-col"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-800">{preset.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600">
                      {preset.mode}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">
                    {preset.description}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Auto-Layout Graph */}
        <button
          onClick={onAutoLayout}
          title="Auto-arrange nodes cleanly with Dagre layout"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-200 transition-colors"
        >
          <LayoutGrid className="w-3.5 h-3.5 text-slate-500" />
          <span className="hidden lg:inline">Auto Layout</span>
        </button>

        {/* Export Menu Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-200 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span className="hidden md:inline">Export</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {showExportMenu && (
            <div
              className="absolute right-0 mt-1.5 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1.5 z-30"
              onMouseLeave={() => setShowExportMenu(false)}
            >
              <button
                onClick={() => {
                  onExportPng();
                  setShowExportMenu(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 text-xs text-slate-700 flex items-center gap-2"
              >
                <Download className="w-3.5 h-3.5 text-blue-600" />
                <span>Export High-Res PNG</span>
              </button>
              <button
                onClick={() => {
                  onExportJson();
                  setShowExportMenu(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 text-xs text-slate-700 flex items-center gap-2"
              >
                <FileCode className="w-3.5 h-3.5 text-indigo-600" />
                <span>Export Diagram JSON</span>
              </button>
              <label className="w-full text-left px-3 py-2 hover:bg-slate-50 text-xs text-slate-700 flex items-center gap-2 cursor-pointer">
                <Upload className="w-3.5 h-3.5 text-emerald-600" />
                <span>Import Diagram JSON</span>
                <input
                  type="file"
                  accept=".json"
                  className="hidden"
                  onChange={(e) => {
                    handleFileChange(e);
                    setShowExportMenu(false);
                  }}
                />
              </label>
            </div>
          )}
        </div>

        {/* Clear Canvas */}
        <button
          onClick={onClearCanvas}
          title="Clear all canvas nodes and edges"
          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>

        {/* Backend health status indicator */}
        <div
          title={backendHealthy ? 'FastAPI Backend Online' : 'FastAPI Backend Reconnecting'}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-slate-100 text-[10px] text-slate-500 font-mono"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              backendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
            }`}
          />
          <span className="hidden xl:inline">{backendHealthy ? 'API Active' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
};
