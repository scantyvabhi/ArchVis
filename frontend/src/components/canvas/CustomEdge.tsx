import React, { memo } from 'react';
import { EdgeProps, getSmoothStepPath, EdgeLabelRenderer } from '@xyflow/react';
import { ArchitectureEdge } from '../../types/architecture';

export const CustomEdge = memo((props: EdgeProps<ArchitectureEdge>) => {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data,
    label,
    animated,
  } = props;

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
  });

  const protocol = data?.protocol || (typeof label === 'string' ? label : '');

  return (
    <>
      <path
        id={id}
        style={{
          ...style,
          strokeWidth: 2,
          stroke: '#94A3B8',
        }}
        className={`react-flow__edge-path transition-colors hover:!stroke-blue-500 ${
          animated ? 'stroke-dash-animated' : ''
        }`}
        d={edgePath}
        markerEnd={markerEnd}
      />

      {protocol && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-white/95 backdrop-blur-sm border border-slate-200 text-slate-600 shadow-sm hover:border-blue-400 hover:text-blue-600 transition-colors cursor-pointer select-none">
              {protocol}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
