"use client"

import React from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export default function WorkflowNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 ${
        selected
          ? 'border-indigo-500 shadow-lg'
          : 'border-indigo-300 hover:border-indigo-400'
      } bg-indigo-50 transition-all`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">🔄</span>
        <div>
          <div className="font-medium text-sm">{data.label || 'Sub-Workflow'}</div>
          {data.workflowName && (
            <div className="text-xs text-gray-600">{data.workflowName}</div>
          )}
        </div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
    </div>
  )
}