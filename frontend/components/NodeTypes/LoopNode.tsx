"use client"

import React from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export default function LoopNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 ${
        selected
          ? 'border-cyan-500 shadow-lg'
          : 'border-cyan-300 hover:border-cyan-400'
      } bg-cyan-50 transition-all`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">🔁</span>
        <div>
          <div className="font-medium text-sm">{data.label || 'Loop'}</div>
          {data.iterations && (
            <div className="text-xs text-gray-600">{data.iterations} times</div>
          )}
        </div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        id="continue"
        style={{ left: '30%' }}
        className="w-3 h-3 bg-blue-500 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="break"
        style={{ left: '70%' }}
        className="w-3 h-3 bg-red-500 border-2 border-white"
      />
    </div>
  )
}