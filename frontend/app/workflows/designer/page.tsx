'use client'

import { useRouter } from 'next/navigation'
import WorkflowBuilder from '@/components/WorkflowBuilder'
import { Node, Edge } from 'reactflow'

export default function WorkflowDesignerPage() {
  const router = useRouter()

  const handleSave = async (nodes: Node[], edges: Edge[]) => {
    try {
      const response = await fetch('/api/workflows', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'New Workflow',
          description: 'Created with workflow builder',
          definition: {
            nodes,
            edges,
          },
        }),
      })

      if (response.ok) {
        const data = await response.json()
        router.push(`/workflows/${data.id}`)
      }
    } catch (error) {
      console.error('Failed to save workflow:', error)
    }
  }

  const handleDeploy = async (nodes: Node[], edges: Edge[]) => {
    // First save, then deploy
    await handleSave(nodes, edges)
    // Deployment logic would go here
  }

  return (
    <div className="h-screen">
      <WorkflowBuilder onSave={handleSave} onDeploy={handleDeploy} />
    </div>
  )
}