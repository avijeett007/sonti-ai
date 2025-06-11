"use client"

import React from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export default function FunctionNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 ${
        selected
          ? 'border-yellow-500 shadow-lg'
          : 'border-yellow-300 hover:border-yellow-400'
      } bg-yellow-50 transition-all`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">⚡</span>
        <div>
          <div className="font-medium text-sm">{data.label || 'Function'}</div>
          {data.functionName && (
            <div className="text-xs text-gray-600">{data.functionName}</div>
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