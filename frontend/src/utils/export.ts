import { toPng, toSvg } from 'html-to-image';
import { ArchitectureNode, ArchitectureEdge } from '../types/architecture';

function getThemeBackground(): string {
  // Check if dark mode is active
  if (typeof document !== 'undefined' && document.documentElement.classList.contains('dark')) {
    return '#0f172a'; // dark mode background
  }
  return '#F8FAFC'; // light mode background
}

export async function exportCanvasToPng(element: HTMLElement, filename = 'archvis-system-design.png'): Promise<void> {
  try {
    // Clone the element to avoid modifying the original
    const clone = element.cloneNode(true) as HTMLElement;
    
    // Apply theme-aware styles to the clone
    const isDark = document.documentElement.classList.contains('dark');
    
    // Temporarily add the clone to body for rendering
    document.body.appendChild(clone);
    clone.style.position = 'absolute';
    clone.style.left = '-9999px';
    clone.style.top = '0';
    clone.style.backgroundColor = getThemeBackground();
    
    // Apply dark/light mode classes to the clone
    if (isDark) {
      clone.classList.add('dark');
    } else {
      clone.classList.remove('dark');
    }
    
    try {
      const dataUrl = await toPng(clone, {
        backgroundColor: getThemeBackground(),
        quality: 0.98,
        pixelRatio: 3, // High DPI (300 DPI equivalent)
        filter: (node) => {
          const exclusionClasses = ['react-flow__panel', 'no-export'];
          if (node instanceof HTMLElement) {
            return !exclusionClasses.some((cls) => node.classList.contains(cls));
          }
          return true;
        },
      });
  
      const link = document.createElement('a');
      link.download = filename;
      link.href = dataUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } finally {
      // Clean up
      document.body.removeChild(clone);
    }
  } catch (error) {
    console.error('Error exporting canvas as PNG:', error);
    throw error;
  }
}

export async function exportCanvasToSvg(element: HTMLElement, filename = 'archvis-system-design.svg'): Promise<void> {
  try {
    // Clone the element to avoid modifying the original
    const clone = element.cloneNode(true) as HTMLElement;
    
    const isDark = document.documentElement.classList.contains('dark');
    
    // Temporarily add the clone to body for rendering
    document.body.appendChild(clone);
    clone.style.position = 'absolute';
    clone.style.left = '-9999px';
    clone.style.top = '0';
    clone.style.backgroundColor = getThemeBackground();
    
    if (isDark) {
      clone.classList.add('dark');
    } else {
      clone.classList.remove('dark');
    }
    
    try {
      const dataUrl = await toSvg(clone, {
        backgroundColor: getThemeBackground(),
        filter: (node) => {
          const exclusionClasses = ['react-flow__panel', 'no-export'];
          if (node instanceof HTMLElement) {
            return !exclusionClasses.some((cls) => node.classList.contains(cls));
          }
          return true;
        },
      });
  
      const link = document.createElement('a');
      link.download = filename;
      link.href = dataUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } finally {
      document.body.removeChild(clone);
    }
  } catch (error) {
    console.error('Error exporting canvas as SVG:', error);
    throw error;
  }
}

export function exportArchitectureJson(nodes: ArchitectureNode[], edges: ArchitectureEdge[], title = 'architecture'): void {
  const exportData = {
    app: 'ArchVis AI',
    version: '1.0.0',
    exportedAt: new Date().toISOString(),
    nodes,
    edges,
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.download = `${title}-${new Date().toISOString().slice(0, 10)}.json`;
  link.href = url;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function parseImportedJson(jsonString: string): { nodes: ArchitectureNode[]; edges: ArchitectureEdge[] } {
  try {
    const parsed = JSON.parse(jsonString);
    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
      throw new Error('Invalid JSON format: missing "nodes" or "edges" arrays.');
    }
    return {
      nodes: parsed.nodes,
      edges: parsed.edges,
    };
  } catch (e: any) {
    throw new Error(`Failed to parse architecture JSON: ${e.message}`);
  }
}
