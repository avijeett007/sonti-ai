"use client"

import React from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export default function WebhookNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 ${
        selected
          ? 'border-purple-500 shadow-lg'
          : 'border-purple-300 hover:border-purple-400'
      } bg-purple-50 transition-all`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">🔗</span>
        <div>
          <div className="font-medium text-sm">{data.label || 'Webhook'}</div>
          {data.method && (
            <div className="text-xs text-gray-600">{data.method}</div>
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