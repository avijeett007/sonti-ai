"use client"

import React, { useCallback, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  Panel,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { Button } from '@/components/ui/Button'
import { nodeTypes } from '../NodeTypes'
import WorkflowSidebar from './WorkflowSidebar'
import WorkflowToolbar from './WorkflowToolbar'

const initialNodes: Node[] = []
const initialEdges: Edge[] = []

export interface WorkflowBuilderProps {
  workflowId?: string
  onSave?: (nodes: Node[], edges: Edge[]) => void
  onDeploy?: (nodes: Node[], edges: Edge[]) => void
}

function WorkflowBuilder({ workflowId, onSave, onDeploy }: WorkflowBuilderProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [isAdvancedMode, setIsAdvancedMode] = useState(false)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()

      const type = event.dataTransfer.getData('application/reactflow')
      if (!type) return

      const position = {
        x: event.clientX - event.currentTarget.getBoundingClientRect().left,
        y: event.clientY - event.currentTarget.getBoundingClientRect().top,
      }

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: { label: `${type} node` },
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [setNodes]
  )

  const handleSave = () => {
    if (onSave) {
      onSave(nodes, edges)
    }
  }

  const handleDeploy = () => {
    if (onDeploy) {
      onDeploy(nodes, edges)
    }
  }

  const handleClearCanvas = () => {
    setNodes([])
    setEdges([])
    setSelectedNode(null)
  }

  return (
    <div className="flex h-screen">
      <WorkflowSidebar 
        isAdvancedMode={isAdvancedMode}
        selectedNode={selectedNode}
        onNodeUpdate={(nodeId, data) => {
          setNodes((nds) =>
            nds.map((node) =>
              node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
            )
          )
        }}
      />
      
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
          
          <Panel position="top-center">
            <WorkflowToolbar
              isAdvancedMode={isAdvancedMode}
              onToggleMode={() => setIsAdvancedMode(!isAdvancedMode)}
              onSave={handleSave}
              onDeploy={handleDeploy}
              onClear={handleClearCanvas}
            />
          </Panel>
        </ReactFlow>
      </div>
    </div>
  )
}

export default function WorkflowBuilderWithProvider(props: WorkflowBuilderProps) {
  return (
    <ReactFlowProvider>
      <WorkflowBuilder {...props} />
    </ReactFlowProvider>
  )
}