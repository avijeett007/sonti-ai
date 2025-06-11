import Link from 'next/link'
import { Phone, Brain, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AgentCardProps {
  agent: {
    id: string
    name: string
    type: string
    llm_provider: string
    llm_model: string
    created_at: string
    status: string
  }
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <Link href={`/agents/${agent.id}`}>
      <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
        <div className="flex items-start justify-between mb-4">
          <Brain className="w-8 h-8 text-primary" />
          <span
            className={cn(
              "text-xs px-2 py-1 rounded",
              agent.status === 'active'
                ? "bg-green-100 text-green-800"
                : "bg-gray-100 text-gray-800"
            )}
          >
            {agent.status}
          </span>
        </div>
        
        <h3 className="font-semibold text-lg mb-2">{agent.name}</h3>
        
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            <span>{agent.llm_provider} / {agent.llm_model}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>{new Date(agent.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </Link>
  )
}