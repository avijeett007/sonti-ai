'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Plus, GitBranch } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Workflow {
  id: string
  name: string
  description: string
  created_at: string
  node_count: number
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const fetchWorkflows = async () => {
    try {
      const response = await fetch('/api/workflows')
      if (response.ok) {
        const data = await response.json()
        setWorkflows(data)
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Workflows</h1>
        <Link href="/workflows/designer">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Create Workflow
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading workflows...</p>
        </div>
      ) : workflows.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed rounded-lg">
          <GitBranch className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No workflows yet</h3>
          <p className="text-muted-foreground mb-4">
            Create your first multi-agent workflow
          </p>
          <Link href="/workflows/designer">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Workflow
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <Link key={workflow.id} href={`/workflows/${workflow.id}`}>
              <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="flex items-start justify-between mb-4">
                  <GitBranch className="w-8 h-8 text-primary" />
                  <span className="text-sm text-muted-foreground">
                    {workflow.node_count} nodes
                  </span>
                </div>
                <h3 className="font-semibold text-lg mb-2">{workflow.name}</h3>
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {workflow.description || 'No description'}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}