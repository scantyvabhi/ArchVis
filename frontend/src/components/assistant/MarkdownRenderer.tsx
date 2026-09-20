import React from 'react';

/**
 * Simple Markdown renderer for chat messages
 * Handles: **bold**, *italic*, `code`, ```code blocks```, bullet points, numbered lists, headers
 */
export const MarkdownRenderer: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  // Normalize line endings and handle escape sequences
  const normalizedText = text
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '');

  // Split by code blocks first to preserve them
  const parts = normalizedText.split(/(\n?```[\s\S]*?```\n?)/g);
  
  return (
    <div className="whitespace-pre-wrap text-xs leading-relaxed">
      {parts.map((part, idx) => {
        // Code blocks
        if (part.startsWith('```') && part.endsWith('```')) {
          const lines = part.split('\n');
          const langMatch = lines[0].match(/^```(\w*)/);
          const code = lines.slice(1, -1).join('\n');
          return (
            <pre key={idx} className="bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto mt-2 mb-2 text-[10px] font-mono">
              <code className={langMatch ? `language-${langMatch[1]}` : ''}>{code}</code>
            </pre>
          );
        }
        
        // Inline code and regular text
        const inlineParts = part.split(/(`[^`\n]+`)/g);
        
        return (
          <React.Fragment key={idx}>
            {inlineParts.map((inlinePart, iIdx) => {
              // Inline code
              if (inlinePart.startsWith('`') && inlinePart.endsWith('`')) {
                return (
                  <code key={iIdx} className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 px-1 rounded font-mono text-[10px]">
                    {inlinePart.slice(1, -1)}
                  </code>
                );
              }
              
              // Process markdown in text parts
              return (
                <MarkdownText key={iIdx} text={inlinePart} />
              );
            })}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const MarkdownText: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;
  
  // Split by newlines to handle lists and structure
  const lines = text.split('\n');
  
  return (
    <React.Fragment>
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();
        
        // Empty line - add spacing
        if (!trimmed) {
          return <div key={lineIdx} className="h-1" />;
        }
        
        // Bullet points
        if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
          return (
            <div key={lineIdx} className="flex gap-2 ml-4 my-0.5">
              <span className="text-slate-500 dark:text-slate-400 flex-shrink-0">•</span>
              <span className="flex-1">{parseInlineMarkdown(trimmed.slice(2).trimStart())}</span>
            </div>
          );
        }
        
        // Numbered lists
        const numMatch = trimmed.match(/^(\d+)[\.\)]\s+(.+)$/);
        if (numMatch) {
          return (
            <div key={lineIdx} className="flex gap-2 ml-4 my-0.5">
              <span className="text-slate-600 dark:text-slate-300 font-mono text-[10px] flex-shrink-0 font-medium">{numMatch[1]}.</span>
              <span className="flex-1 text-slate-700 dark:text-slate-200">{parseInlineMarkdown(numMatch[2].trimStart())}</span>
            </div>
          );
        }
        
        // Headers
        if (trimmed.startsWith('### ')) {
          return <h4 key={lineIdx} className="font-semibold text-xs text-slate-700 dark:text-slate-300 mt-2 mb-1">{parseInlineMarkdown(trimmed.slice(4))}</h4>;
        }
        if (trimmed.startsWith('## ')) {
          return <h3 key={lineIdx} className="font-semibold text-sm text-slate-700 dark:text-slate-300 mt-2 mb-1">{parseInlineMarkdown(trimmed.slice(3))}</h3>;
        }
        if (trimmed.startsWith('# ')) {
          return <h2 key={lineIdx} className="font-semibold text-base text-slate-700 dark:text-slate-300 mt-2 mb-1">{parseInlineMarkdown(trimmed.slice(2))}</h2>;
        }
        
        // Horizontal rule
        if (trimmed === '---' || trimmed === '***') {
          return <hr key={lineIdx} className="border-t border-slate-200 dark:border-slate-700 my-2" />;
        }
        
        // Blockquotes
        if (trimmed.startsWith('> ')) {
          return (
            <blockquote key={lineIdx} className="border-l-4 border-blue-500 pl-3 italic text-slate-600 dark:text-slate-400 my-1 ml-4">
              {parseInlineMarkdown(trimmed.slice(2).trimStart())}
            </blockquote>
          );
        }
        
        // Regular text with inline markdown
        return (
          <div key={lineIdx} className="my-0.5">
            {parseInlineMarkdown(line)}
          </div>
        );
      })}
    </React.Fragment>
  );
};

function parseInlineMarkdown(text: string): React.ReactNode {
  if (!text || text.trim() === '') return text;
  
  // Handle bold first: **text** or __text__
  const boldParts = text.split(/(\*\*[^*]+\*\*|__[^_]+__)/g);
  
  return (
    <React.Fragment>
      {boldParts.map((part, idx) => {
        if ((part.startsWith('**') && part.endsWith('**')) || (part.startsWith('__') && part.endsWith('__'))) {
          return <strong key={idx} className="font-semibold text-slate-700 dark:text-slate-200">{part.slice(2, -2)}</strong>;
        }
        
        // Handle italic: *text* or _text_ (but not bold markers)
        const italicParts = part.split(/(\*[^*]+\*|_[^_]+_)/g);
        
        return (
          <React.Fragment key={idx}>
            {italicParts.map((iPart, iIdx) => {
              if ((iPart.startsWith('*') && iPart.endsWith('*') && iPart.length > 2) ||
                  (iPart.startsWith('_') && iPart.endsWith('_') && iPart.length > 2)) {
                return <em key={iIdx} className="italic text-slate-700 dark:text-slate-200">{iPart.slice(1, -1)}</em>;
              }
              
              // Handle strikethrough: ~~text~~
              const strikeParts = iPart.split(/~~([^~]+)~~/g);
              
              return (
                <React.Fragment key={iIdx}>
                  {strikeParts.map((sPart, sIdx) => {
                    if (sIdx % 2 === 1) {
                      return <del key={sIdx} className="line-through text-slate-500 dark:text-slate-400">{sPart}</del>;
                    }
                    return <span key={sIdx} className="text-slate-700 dark:text-slate-200">{sPart}</span>;
                  })}
                </React.Fragment>
              );
            })}
          </React.Fragment>
        );
      })}
    </React.Fragment>
  );
}