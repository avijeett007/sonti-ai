"use client"

import React from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export default function ConditionNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 ${
        selected
          ? 'border-orange-500 shadow-lg'
          : 'border-orange-300 hover:border-orange-400'
      } bg-orange-50 transition-all`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">🔀</span>
        <div>
          <div className="font-medium text-sm">{data.label || 'Condition'}</div>
          {data.conditionType && (
            <div className="text-xs text-gray-600">{data.conditionType}</div>
          )}
        </div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        style={{ left: '30%' }}
        className="w-3 h-3 bg-green-500 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        style={{ left: '70%' }}
        className="w-3 h-3 bg-red-500 border-2 border-white"
      />
    </div>
  )
}