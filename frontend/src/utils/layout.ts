import dagre from 'dagre';
import { ArchitectureNode, ArchitectureEdge } from '../types/architecture';

const NODE_WIDTH = 280;
const NODE_HEIGHT = 160;

export function getLayoutedElements(
  nodes: ArchitectureNode[],
  edges: ArchitectureEdge[],
  direction: 'LR' | 'TB' = 'LR'
): { nodes: ArchitectureNode[]; edges: ArchitectureEdge[] } {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: isHorizontal ? 60 : 70,
    ranksep: isHorizontal ? 120 : 100,
    align: 'DL',
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const x = nodeWithPosition.x - NODE_WIDTH / 2;
    const y = nodeWithPosition.y - NODE_HEIGHT / 2;

    return {
      ...node,
      position: { x, y },
    };
  });

  return { nodes: layoutedNodes, edges };
}
