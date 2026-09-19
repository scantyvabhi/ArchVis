import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Github,
  BookOpen,
  Briefcase,
  ChevronUp,
  ChevronDown,
  Bot,
  User,
  HelpCircle,
  Zap,
  RotateCcw,
  Loader2,
  Paperclip,
  Brain,
  GitBranch,
  Layers,
} from 'lucide-react';
import { AppMode, ChatMessage, ArchitectureNode, ArchitectureEdge, AgentThinkingStep } from '../../types/architecture';
import { AgentThinkingDisplay } from './AgentThinkingDisplay';
import { MarkdownRenderer } from './MarkdownRenderer';

interface FloatingAssistantProps {
  mode: AppMode;
  onToggleMode: (newMode: AppMode) => void;
  onGenerateArchitecture: (prompt: string) => Promise<void>;
  onSendMessage: (message: string) => Promise<void>;
  onOrchestrateAgents: (prompt: string, repoUrl?: string) => Promise<void>;
  onOpenRepoIngestion: () => void;
  messages: ChatMessage[];
  isLoading: boolean;
  nodesCount: number;
  currentAgentThinking?: AgentThinkingStep;
}

export const FloatingAssistant: React.FC<FloatingAssistantProps> = ({
  mode,
  onToggleMode,
  onGenerateArchitecture,
  onSendMessage,
  onOrchestrateAgents,
  onOpenRepoIngestion,
  messages,
  isLoading,
  nodesCount,
  currentAgentThinking,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const query = inputText.trim();
    setInputText('');

    // Check for GitHub repo URL
    const repoUrlMatch = query.match(/https?:\/\/github\.com\/[\w-]+\/[\w-]+/);
    const repoUrl = repoUrlMatch ? repoUrlMatch[0] : undefined;

    // Check if this is an architecture design request (design, generate, build, create, or specific system names)
    const isDesignRequest =
      nodesCount === 0 ||
      query.toLowerCase().startsWith('design') ||
      query.toLowerCase().startsWith('generate') ||
      query.toLowerCase().startsWith('build') ||
      query.toLowerCase().startsWith('create') ||
      // Common system names that imply architecture design
      /\b(flipkart|amazon|uber|netflix|youtube|whatsapp|slack|twitter|instagram|stripe|doordash|swiggy|zomato|spotify|airbnb|booking|expedia)\b/i.test(query);

    // Check for multi-agent trigger keywords (repo analysis, full orchestration)
    const isMultiAgentRequest =
      query.toLowerCase().startsWith('analyze') ||
      query.toLowerCase().startsWith('orchestrate') ||
      query.toLowerCase().startsWith('multi-agent') ||
      query.toLowerCase().startsWith('full analysis') ||
      repoUrl ||
      query.toLowerCase().includes('repo') && (query.toLowerCase().includes('analyze') || query.toLowerCase().includes('understand'));

    if (repoUrl) {
      // GitHub repo - use full orchestration with repo
      if (!isOpen) setIsOpen(true);
      await onOrchestrateAgents(query, repoUrl);
    } else if (isDesignRequest) {
      // Architecture design request - use multi-agent orchestration for better results
      if (!isOpen) setIsOpen(true);
      await onOrchestrateAgents(query);
    } else if (isMultiAgentRequest) {
      // Other multi-agent requests
      if (!isOpen) setIsOpen(true);
      await onOrchestrateAgents(query);
    } else {
      // Normal chat question - use multi-agent chat
      if (!isOpen) setIsOpen(true);
      await onSendMessage(query);
    }
  };

  const quickPrompts = [
    'Analyze bottlenecks & SPOFs in my current diagram',
    'How can I optimize this for 50,000 RPS?',
    'Explain the data flow step-by-step',
    'Design Netflix video streaming with multi-region CDN',
    'Design Uber ride-matching with Redis Geospatial',
  ];

  const designPrompts = [
    'Design Flipkart e-commerce architecture',
    'Design Uber ride-hailing system',
    'Design Netflix video streaming platform',
    'Design WhatsApp real-time messaging',
    'Design Twitter social media feed',
    'Design Stripe payment platform',
  ];

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-2xl px-4 select-none">
      {/* Expanded Chat Drawer */}
      {isOpen && (
        <div className="mb-3 bg-white/98 backdrop-blur-xl border border-slate-200/90 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[400px] animate-in fade-in slide-in-from-bottom-6">
          {/* Assistant Header */}
          <div className="px-4 py-3 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 bg-gradient-to-tr from-blue-600 to-indigo-600 text-white rounded-lg shadow-xs">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-xs text-slate-800 flex items-center gap-1.5">
                  ArchVis AI Copilot
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-normal">
                    {mode === 'learner' ? 'Learner Mode' : 'Pro Mode'}
                  </span>
                </h3>
                <p className="text-[10px] text-slate-500">
                  Aware of {nodesCount} canvas components & active telemetry
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 rounded-md transition-colors"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
            {messages.length === 0 ? (
              <div className="text-center py-6 text-slate-400 space-y-2">
                <Sparkles className="w-6 h-6 mx-auto text-blue-500 opacity-60" />
                <p className="font-medium text-slate-600">Ask anything about your architecture</p>
                <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
                  I can analyze bottlenecks, suggest caching layers, verify fault tolerance, or generate an entire design.
                </p>
                <div className="flex flex-wrap gap-1.5 justify-center pt-2">
                  {quickPrompts.slice(0, 3).map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setInputText(prompt);
                      }}
                      className="text-[10px] bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 px-2.5 py-1 rounded-full border border-slate-200/80 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap gap-1.5 justify-center pt-1 border-t border-slate-100 mt-2">
                  <span className="text-[9px] text-slate-400 px-1 self-center">Design System:</span>
                  {designPrompts.slice(0, 3).map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setInputText(prompt);
                      }}
                      className="text-[10px] bg-green-50 hover:bg-green-100 hover:text-green-700 text-green-600 px-2.5 py-1 rounded-full border border-green-200/80 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap gap-1.5 justify-center pt-1 border-t border-slate-100 mt-2">
                  <span className="text-[9px] text-slate-400 px-1 self-center">Multi-Agent:</span>
                  {[
                    'Analyze GitHub repo: https://github.com/fastapi/fastapi',
                    'Full multi-agent analysis of my diagram',
                  ].map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setInputText(prompt);
                      }}
                      className="text-[10px] bg-purple-50 hover:bg-purple-100 hover:text-purple-700 text-purple-600 px-2.5 py-1 rounded-full border border-purple-200/80 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'assistant' && (
                    <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-3.5 h-3.5" />
                    </div>
                  )}

                  <div className="flex flex-col max-w-[82%]">
                    <div
                      className={`rounded-xl px-3.5 py-2.5 leading-relaxed text-xs ${
                        msg.sender === 'user'
                          ? 'bg-blue-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-800 border border-slate-200/60 shadow-xs'
                      }`}
                    >
                      {msg.sender === 'assistant' ? (
                        <MarkdownRenderer text={msg.text} />
                      ) : (
                        <div className="whitespace-pre-wrap">{msg.text}</div>
                      )}
                      <span
                        className={`block text-[9px] mt-1 font-mono ${
                          msg.sender === 'user' ? 'text-blue-200 text-right' : 'text-slate-400'
                        }`}
                      >
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    {/* Agent Thinking Display */}
                    {msg.thinking && msg.thinking.length > 0 && (
                      <AgentThinkingDisplay
                        thinkingSteps={msg.thinking}
                        messageId={msg.id}
                      />
                    )}
                  </div>

                  {msg.sender === 'user' && (
                    <div className="w-6 h-6 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5">
                      <User className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              ))
            )}
            {isLoading && (
              <>
                <div className="flex gap-2.5 items-center text-slate-400 text-xs">
                  <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  </div>
                  <span>Analyzing architecture with Gemini 1.5 Flash...</span>
                </div>
                {currentAgentThinking && (
                  <div className="mt-2">
                    <div className="flex gap-2.5 items-center text-slate-400 text-xs">
                      <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                        <Brain className="w-3.5 h-3.5 animate-spin" />
                      </div>
                      <span>Agent pipeline running...</span>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Floating Bottom Input Bar */}
      <form
        onSubmit={handleSubmit}
        className="bg-white/95 backdrop-blur-xl border border-slate-200/90 rounded-2xl shadow-xl p-1.5 flex items-center gap-1.5 transition-all focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-500/10"
      >
        {/* Toggle Mode Button */}
        <button
          type="button"
          onClick={() => onToggleMode(mode === 'learner' ? 'pro' : 'learner')}
          title={mode === 'learner' ? 'Learner Mode Active (Click to switch to Pro)' : 'Pro Mode Active (Click to switch to Learner)'}
          className={`flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition-colors ${
            mode === 'learner'
              ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          {mode === 'learner' ? <BookOpen className="w-3.5 h-3.5" /> : <Briefcase className="w-3.5 h-3.5" />}
          <span className="hidden sm:inline capitalize">{mode}</span>
        </button>

        {/* Multi-Agent Orchestration Button */}
        <button
          type="button"
          onClick={() => {
            setInputText('Full multi-agent analysis of my diagram');
            if (!isOpen) setIsOpen(true);
          }}
          title="Run full multi-agent orchestration (Repo Fetcher → Architecture Analyst → Diagram Builder)"
          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors shrink-0"
        >
          <Brain className="w-4 h-4" />
        </button>

        {/* Ingestion Button (GitHub / Doc) */}
        <button
          type="button"
          onClick={onOpenRepoIngestion}
          title="Ingest GitHub Repository or Documentation"
          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors shrink-0"
        >
          <Github className="w-4 h-4" />
        </button>

        {/* Input Text Field */}
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            nodesCount === 0
              ? 'Enter system design prompt (e.g. "Design Uber ride hailing")...'
              : 'Ask a question about current diagram or enter "Design [system]"...'
          }
          className="flex-1 bg-transparent px-2.5 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
        />

        {/* Quick Expand Chat Drawer Button */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          title="Toggle Assistant Conversation"
          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors shrink-0"
        >
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>

        {/* Submit Send Button */}
        <button
          type="submit"
          disabled={isLoading || !inputText.trim()}
          className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl shadow-xs transition-all shrink-0 flex items-center justify-center"
        >
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
        </button>
      </form>
    </div>
  );
};
