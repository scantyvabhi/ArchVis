import React, { useState } from 'react';
import { X, Github, FileText, Upload, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { AppMode } from '../../types/architecture';

interface RepoIngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitRepo: (repoUrl: string) => Promise<void>;
  onSubmitDoc: (docContent: string) => Promise<void>;
  mode: AppMode;
  isLoading: boolean;
}

export const RepoIngestionModal: React.FC<RepoIngestionModalProps> = ({
  isOpen,
  onClose,
  onSubmitRepo,
  onSubmitDoc,
  mode,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<'github' | 'doc'>('github');
  const [repoUrl, setRepoUrl] = useState('');
  const [docContent, setDocContent] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleRepoSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setErrorMessage('');
    try {
      await onSubmitRepo(repoUrl.trim());
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to ingest repository');
    }
  };

  const handleDocSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docContent.trim()) return;
    setErrorMessage('');
    try {
      await onSubmitDoc(docContent.trim());
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to parse documentation');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setDocContent(content);
      setActiveTab('doc');
    };
    reader.readAsText(file);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Reverse-Engineer Architecture</h3>
              <p className="text-xs text-slate-500">Ingest GitHub Repo or System Documentation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Toggle */}
        <div className="flex border-b border-slate-100 px-6 pt-3 gap-4">
          <button
            type="button"
            onClick={() => setActiveTab('github')}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'github'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Github className="w-4 h-4" />
            GitHub Repository
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('doc')}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'doc'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileText className="w-4 h-4" />
            Paste Doc / File Upload
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {errorMessage && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {activeTab === 'github' ? (
            <form onSubmit={handleRepoSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  GitHub Public Repository URL
                </label>
                <div className="relative">
                  <Github className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="url"
                    required
                    placeholder="https://github.com/tiangolo/fastapi"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
                  Gemini will inspect repo structure, manifests (package.json, Dockerfile, requirements.txt, go.mod), and README to construct an interactive architecture.
                </p>
              </div>

              {/* Sample Quick Links */}
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                  Try Sample Repositories:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    'https://github.com/fastapi/fastapi',
                    'https://github.com/redis/redis',
                    'https://github.com/supabase/supabase',
                  ].map((sample) => (
                    <button
                      key={sample}
                      type="button"
                      onClick={() => setRepoUrl(sample)}
                      className="px-2 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-600 font-mono text-[10px] transition-colors"
                    >
                      {sample.replace('https://github.com/', '')}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !repoUrl.trim()}
                  className="px-5 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl shadow-sm transition-all flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Analyzing Repository...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Generate Architecture</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleDocSubmit} className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Paste Architecture Specification or README
                  </label>
                  <label className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
                    <Upload className="w-3 h-3" />
                    <span>Upload File</span>
                    <input
                      type="file"
                      accept=".md,.txt,.json,.yaml,.yml"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </label>
                </div>
                <textarea
                  rows={6}
                  required
                  placeholder="Paste Markdown design doc, system requirements, or Docker compose file here..."
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                  className="w-full p-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 resize-none font-mono"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !docContent.trim()}
                  className="px-5 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl shadow-sm transition-all flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Parsing Documentation...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Synthesize Diagram</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
