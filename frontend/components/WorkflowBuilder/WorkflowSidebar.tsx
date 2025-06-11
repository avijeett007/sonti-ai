"use client"

import React from 'react'
import { Node } from 'reactflow'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Textarea } from '@/components/ui/Textarea'

interface WorkflowSidebarProps {
  isAdvancedMode: boolean
  selectedNode: Node | null
  onNodeUpdate: (nodeId: string, data: any) => void
}

const nodeCategories = [
  {
    name: 'Agents',
    items: [
      { type: 'agent', label: 'Voice Agent', icon: '🎤' },
      { type: 'workflow', label: 'Sub-Workflow', icon: '🔄' },
    ],
  },
  {
    name: 'Tools',
    items: [
      { type: 'function', label: 'Function Call', icon: '⚡' },
      { type: 'webhook', label: 'Webhook', icon: '🔗' },
      { type: 'knowledge', label: 'Knowledge Base', icon: '📚' },
    ],
  },
  {
    name: 'Logic',
    items: [
      { type: 'condition', label: 'Condition', icon: '🔀' },
      { type: 'loop', label: 'Loop', icon: '🔁' },
      { type: 'delay', label: 'Delay', icon: '⏰' },
    ],
  },
]

export default function WorkflowSidebar({
  isAdvancedMode,
  selectedNode,
  onNodeUpdate,
}: WorkflowSidebarProps) {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold">Workflow Builder</h2>
        <p className="text-sm text-gray-600 mt-1">
          {isAdvancedMode ? 'Advanced Mode' : 'Simple Mode'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {!selectedNode ? (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Drag nodes to canvas
            </h3>
            {nodeCategories.map((category) => (
              <div key={category.name} className="mb-6">
                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                  {category.name}
                </h4>
                <div className="space-y-2">
                  {category.items
                    .filter((item) => isAdvancedMode || !['loop', 'delay'].includes(item.type))
                    .map((item) => (
                      <div
                        key={item.type}
                        className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg cursor-move hover:border-blue-400 hover:shadow-sm transition-all"
                        draggable
                        onDragStart={(e) => onDragStart(e, item.type)}
                      >
                        <span className="text-2xl">{item.icon}</span>
                        <span className="text-sm font-medium">{item.label}</span>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-4">
              Node Properties
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <Input
                  value={selectedNode.data.label || ''}
                  onChange={(e) =>
                    onNodeUpdate(selectedNode.id, { label: e.target.value })
                  }
                  placeholder="Enter node name"
                />
              </div>

              {selectedNode.type === 'agent' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      LLM Provider
                    </label>
                    <Select
                      value={selectedNode.data.provider || 'openai'}
                      onChange={(e) =>
                        onNodeUpdate(selectedNode.id, { provider: e.target.value })
                      }
                    >
                      <option value="openai">OpenAI</option>
                      <option value="google">Google</option>
                      <option value="anthropic">Anthropic</option>
                      <option value="azure">Azure</option>
                      <option value="aws">AWS Bedrock</option>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      System Prompt
                    </label>
                    <Textarea
                      value={selectedNode.data.prompt || ''}
                      onChange={(e) =>
                        onNodeUpdate(selectedNode.id, { prompt: e.target.value })
                      }
                      placeholder="Enter system prompt"
                      rows={4}
                    />
                  </div>
                </>
              )}

              {selectedNode.type === 'condition' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Condition Type
                    </label>
                    <Select
                      value={selectedNode.data.conditionType || 'keyword'}
                      onChange={(e) =>
                        onNodeUpdate(selectedNode.id, { conditionType: e.target.value })
                      }
                    >
                      <option value="keyword">Keyword Match</option>
                      <option value="intent">Intent Detection</option>
                      <option value="sentiment">Sentiment Analysis</option>
                      <option value="custom">Custom Function</option>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Condition Value
                    </label>
                    <Input
                      value={selectedNode.data.conditionValue || ''}
                      onChange={(e) =>
                        onNodeUpdate(selectedNode.id, { conditionValue: e.target.value })
                      }
                      placeholder="Enter condition value"
                    />
                  </div>
                </>
              )}

              {selectedNode.type === 'webhook' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Webhook URL
                    </label>
                    <Input
                      value={selectedNode.data.webhookUrl || ''}
                      onChange={(e) =>
                        onNodeUpdate(selectedNode.id, { webhookUrl: e.target.value })
                      }
                      placeholder="https://example.com/webhook"
                      type="url"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      HTTP Method
                    </label>
                    <Select
                      value={selectedNode.data.method || 'POST'}
                      onChange={(e) =>
                        onNodeUpdate(selectedNode.id, { method: e.target.value })
                      }
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="PATCH">PATCH</option>
                    </Select>
                  </div>
                </>
              )}

              <Button
                onClick={() => onNodeUpdate(selectedNode.id, {})}
                className="w-full"
                variant="primary"
              >
                Update Node
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}