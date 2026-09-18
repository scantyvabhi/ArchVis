// ArchVis AI - System Design Real-Time Simulation Engine Web Worker

export interface WorkerNodeData {
  id: string;
  rps: number;
  capacity: number;
  latency: number;
  failureRate: number;
  category: string;
}

export interface WorkerEdgeData {
  id: string;
  source: string;
  target: string;
}

let isRunning = false;
let currentNodes: WorkerNodeData[] = [];
let currentEdges: WorkerEdgeData[] = [];
let timerId: any = null;
let tick = 0;

self.onmessage = (event: MessageEvent) => {
  const { type, payload } = event.data;

  if (type === 'INIT' || type === 'UPDATE_GRAPH') {
    if (payload?.nodes) {
      currentNodes = payload.nodes.map((n: any) => ({
        id: n.id,
        rps: Number(n.data?.rps || 1000),
        capacity: Number(n.data?.capacity || 5000),
        latency: Number(n.data?.latency || 20),
        failureRate: Number(n.data?.failureRate || 0.1),
        category: n.data?.category || 'service',
      }));
    }
    if (payload?.edges) {
      currentEdges = payload.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      }));
    }
  }

  if (type === 'START') {
    isRunning = true;
    if (!timerId) {
      timerId = setInterval(runSimulationTick, 150);
    }
  }

  if (type === 'STOP') {
    isRunning = false;
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }
};

function runSimulationTick() {
  if (!isRunning || currentNodes.length === 0) return;
  tick++;

  // Add subtle natural jitter (+- 3%)
  const jitterFactor = 1 + (Math.sin(tick * 0.4) * 0.03 + (Math.random() - 0.5) * 0.02);

  // Build adjacency list & compute in-degrees
  const inDegree: Record<string, number> = {};
  const outgoing: Record<string, string[]> = {};

  currentNodes.forEach((node) => {
    inDegree[node.id] = 0;
    outgoing[node.id] = [];
  });

  currentEdges.forEach((edge) => {
    if (outgoing[edge.source]) {
      outgoing[edge.source].push(edge.target);
    }
    if (inDegree[edge.target] !== undefined) {
      inDegree[edge.target]++;
    }
  });

  // Calculate incoming traffic for each node
  const incomingTraffic: Record<string, number> = {};
  const queue: string[] = [];

  // Identify source / root nodes (inDegree === 0 or api/gateway)
  currentNodes.forEach((node) => {
    if (inDegree[node.id] === 0 || node.category === 'api') {
      incomingTraffic[node.id] = Math.round(node.rps * jitterFactor);
      queue.push(node.id);
    } else {
      incomingTraffic[node.id] = 0;
    }
  });

  // If no root node found (e.g. isolated or cyclic graph), seed the first node
  if (queue.length === 0 && currentNodes.length > 0) {
    const first = currentNodes[0];
    incomingTraffic[first.id] = Math.round(first.rps * jitterFactor);
    queue.push(first.id);
  }

  // Traverse & propagate traffic
  const processedSet = new Set<string>();
  while (queue.length > 0) {
    const currId = queue.shift()!;
    if (processedSet.has(currId)) continue;
    processedSet.add(currId);

    const currNode = currentNodes.find((n) => n.id === currId);
    if (!currNode) continue;

    const inRps = incomingTraffic[currId] || currNode.rps;
    const capacity = Math.max(10, currNode.capacity);
    // Effective throughput this node can process
    const processedRps = Math.min(inRps, capacity);

    const downstream = outgoing[currId] || [];
    if (downstream.length > 0) {
      // Divide traffic equally across branches
      const branchTraffic = Math.round(processedRps / downstream.length);
      downstream.forEach((targetId) => {
        incomingTraffic[targetId] = (incomingTraffic[targetId] || 0) + branchTraffic;
        if (!processedSet.has(targetId)) {
          queue.push(targetId);
        }
      });
    }
  }

  // Calculate node-level metrics
  const nodeUpdates: Record<string, any> = {};
  const overloadedNodeIds: string[] = [];
  const warningNodeIds: string[] = [];
  let totalProcessed = 0;
  let totalLatency = 0;
  let maxLatency = 0;
  let totalErrorWeighted = 0;
  let activeNodesCount = 0;

  currentNodes.forEach((node) => {
    const inRps = incomingTraffic[node.id] || (inDegree[node.id] === 0 ? node.rps : 0);
    const capacity = Math.max(10, node.capacity);
    const utilization = Math.min(150, Math.round((inRps / capacity) * 100));
    const droppedRps = Math.max(0, inRps - capacity);

    let status: 'healthy' | 'warning' | 'overloaded' = 'healthy';
    if (utilization >= 100) {
      status = 'overloaded';
      overloadedNodeIds.push(node.id);
    } else if (utilization >= 75) {
      status = 'warning';
      warningNodeIds.push(node.id);
    }

    // Queuing theory non-linear delay
    let effLatency = node.latency;
    if (utilization >= 100) {
      const overloadRatio = (inRps - capacity) / capacity;
      effLatency = Math.round(node.latency * (2.2 + overloadRatio * 4.0));
    } else if (utilization >= 70) {
      effLatency = Math.round(node.latency * (1 + Math.pow(utilization / 100, 2) * 1.5));
    }

    // Error rate includes base failure rate plus dropped request percentage
    let effErrorRate = node.failureRate;
    if (inRps > 0 && droppedRps > 0) {
      effErrorRate = Math.min(100, Number((node.failureRate + (droppedRps / inRps) * 100).toFixed(1)));
    }

    nodeUpdates[node.id] = {
      rps: inRps,
      status,
      utilization,
      droppedRps,
      effectiveLatency: effLatency,
      effectiveErrorRate: effErrorRate,
    };

    if (inRps > 0) {
      activeNodesCount++;
      totalProcessed += Math.min(inRps, capacity);
      totalLatency += effLatency;
      if (effLatency > maxLatency) maxLatency = effLatency;
      totalErrorWeighted += effErrorRate;
    }
  });

  const avgLatency = activeNodesCount > 0 ? Math.round(totalLatency / activeNodesCount) : 0;
  const avgErrorRate = activeNodesCount > 0 ? Number((totalErrorWeighted / activeNodesCount).toFixed(2)) : 0;

  self.postMessage({
    type: 'TICK',
    payload: {
      nodeUpdates,
      metrics: {
        isRunning: true,
        totalThroughput: totalProcessed,
        averageLatency: avgLatency,
        p99Latency: Math.max(avgLatency, Math.round(maxLatency * 1.15)),
        systemErrorRate: avgErrorRate,
        bottlenecksCount: overloadedNodeIds.length,
        overloadedNodes: overloadedNodeIds,
        warningNodes: warningNodeIds,
        tickCount: tick,
      },
    },
  });
}
