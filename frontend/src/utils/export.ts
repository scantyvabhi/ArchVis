import { toPng, toSvg } from 'html-to-image';
import { ArchitectureNode, ArchitectureEdge } from '../types/architecture';

function getThemeBackground(): string {
  if (typeof document !== 'undefined' && document.documentElement.classList.contains('dark')) {
    return '#0f172a';
  }
  return '#F8FAFC';
}

function getNodeColor(category: string): string {
  const colors: Record<string, string> = {
    api: '#3B82F6',
    gateway: '#8B5CF6',
    service: '#10B981',
    cache: '#F59E0B',
    database: '#EF4444',
    queue: '#EC4899',
    storage: '#6B7280',
  };
  return colors[category] || '#6B7280';
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    api: '🌐',
    gateway: '🛡️',
    service: '⚙️',
    cache: '⚡',
    database: '🗄️',
    queue: '📬',
    storage: '💾',
  };
  return icons[category] || '⚙️';
}

function drawNode(ctx: CanvasRenderingContext2D, node: any, scale: number, panX: number, panY: number) {
  const x = (node.position.x * scale) + panX;
  const y = (node.position.y * scale) + panY;
  const width = Math.max(180, Math.min(220, (node.width || 180) * scale));
  const height = Math.max(80, Math.min(120, (node.height || 80) * scale));
  const radius = 12 * scale;
  const color = getNodeColor(node.data?.category || 'service');
  
  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = color;
  ctx.lineWidth = 2 * scale;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fill();
  ctx.stroke();
  
  const badgeHeight = 24 * scale;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(x, y, width, badgeHeight, radius);
  ctx.fill();
  
  const icon = getCategoryIcon(node.data?.category || 'service');
  ctx.font = `${14 * scale}px Arial`;
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText(icon, x + width / 2, y + badgeHeight / 2 + 5 * scale);
  
  ctx.font = `bold ${12 * scale}px Inter, system-ui`;
  ctx.fillStyle = '#1e293b';
  ctx.textAlign = 'center';
  const label = node.data?.label || 'Node';
  ctx.fillText(label, x + width / 2, y + badgeHeight + 20 * scale);
  
  if (node.data?.tech) {
    ctx.font = `${10 * scale}px Inter, system-ui`;
    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'center';
    ctx.fillText(node.data.tech, x + width / 2, y + badgeHeight + 36 * scale);
  }
  
  const status = node.data?.status || 'healthy';
  const statusColor = status === 'healthy' ? '#10B981' : status === 'warning' ? '#F59E0B' : '#EF4444';
  ctx.beginPath();
  ctx.arc(x + width - 10 * scale, y + 10 * scale, 6 * scale, 0, Math.PI * 2);
  ctx.fillStyle = statusColor;
  ctx.fill();
}

function drawEdge(ctx: CanvasRenderingContext2D, edge: any, nodes: any[], scale: number, panX: number, panY: number) {
  const sourceNode = nodes.find(n => n.id === edge.source);
  const targetNode = nodes.find(n => n.id === edge.target);
  if (!sourceNode || !targetNode) return;
  
  const sx = (sourceNode.position.x * scale) + panX + (sourceNode.width || 180) * scale / 2;
  const sy = (sourceNode.position.y * scale) + panY + (sourceNode.height || 80) * scale / 2;
  const tx = (targetNode.position.x * scale) + panX + (targetNode.width || 180) * scale / 2;
  const ty = (targetNode.position.y * scale) + panY + (targetNode.height || 80) * scale / 2;
  
  ctx.beginPath();
  ctx.moveTo(sx, sy);
  const cx = (sx + tx) / 2;
  const cy = (sy + ty) / 2;
  ctx.quadraticCurveTo(cx, cy - 50, tx, ty);
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 2;
  ctx.stroke();
  
  const angle = Math.atan2(ty - cy, tx - cx);
  const arrowSize = 10;
  ctx.beginPath();
  ctx.moveTo(tx, ty);
  ctx.lineTo(tx - arrowSize * Math.cos(angle - Math.PI / 6), ty - arrowSize * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(tx - arrowSize * Math.cos(angle + Math.PI / 6), ty - arrowSize * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fillStyle = '#94a3b8';
  ctx.fill();
  
  if (edge.data?.protocol) {
    ctx.font = '10px Inter, system-ui';
    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'center';
    ctx.fillText(edge.data.protocol, cx, cy - 60);
  }
}

export async function exportCanvasToPng(
  nodes: any[], 
  edges: any[], 
  viewport: { x: number; y: number; zoom: number },
  filename = 'archvis-system-design.png'
): Promise<void> {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d')!;
    
    const scale = 2;
    const padding = 100;
    
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(node => {
      const x = node.position?.x ?? 0;
      const y = node.position?.y ?? 0;
      const w = node.width || 180;
      const h = node.height || 80;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + w);
      maxY = Math.max(maxY, y + h);
    });
    
    // Handle case where no nodes or all at same position
    if (maxX === -Infinity) {
      maxX = 100;
      maxY = 100;
      minX = 0;
      minY = 0;
    }
    
    const width = (maxX - minX + padding * 2);
    const height = (maxY - minY + padding * 2);
    
    canvas.width = width * 2;
    canvas.height = height * 2;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    
    const ctxScale = 2;
    const panX = (-minX + padding) * ctxScale;
    const panY = (-minY + padding) * ctxScale;
    
    const isDark = document.documentElement.classList.contains('dark');
    const bgColor = document.documentElement.classList.contains('dark') ? '#0f172a' : '#F8FAFC';
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 0.5;
    const gridSize = 50 * 2;
    for (let x = 0; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
    
    edges.forEach(edge => drawEdge(ctx as any, edge, nodes, 2, 0, 0));
    nodes.forEach(node => drawNode(ctx as any, node, 2, 0, 0));
    
    const dataUrl = canvas.toDataURL('image/png', 0.98);
    
    // Use a single reliable download approach
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataUrl;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    // Small delay to ensure the click is processed
    setTimeout(() => {
      document.body.removeChild(link);
    }, 100);
  } catch (error) {
    console.error('Error exporting canvas as PNG:', error);
    throw error;
  }
}

export async function exportCanvasToSvg(
  nodes: any[], 
  edges: any[], 
  viewport: { x: number; y: number; zoom: number },
  filename = 'archvis-system-design.svg'
): Promise<void> {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d')!;
    
    const scale = 2;
    const padding = 100;
    
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(node => {
      const x = node.position.x;
      const y = node.position.y;
      const w = node.width || 180;
      const h = node.height || 80;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + w);
      maxY = Math.max(maxY, y + h);
    });
    
    const width = (maxX - minX + padding * 2);
    const height = (maxY - minY + padding * 2);
    
    canvas.width = width * 2;
    canvas.height = height * 2;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    
    const ctxScale = 2;
    const panX = (-minX + padding) * 2;
    const panY = (-minY + padding) * 2;
    
    const isDark = document.documentElement.classList.contains('dark');
    const bgColor = document.documentElement.classList.contains('dark') ? '#0f172a' : '#F8FAFC';
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 0.5;
    const gridSize = 50 * 2;
    for (let x = 0; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
    
    edges.forEach(edge => drawEdge(ctx as any, edge, nodes, 2, 0, 0));
    nodes.forEach(node => drawNode(ctx as any, node, 2, 0, 0));
    
    const dataUrl = canvas.toDataURL('image/svg+xml', 0.98);
    
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataUrl;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
    }, 100);
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