import AgentNode from './AgentNode'
import ConditionNode from './ConditionNode'
import WebhookNode from './WebhookNode'
import FunctionNode from './FunctionNode'
import KnowledgeNode from './KnowledgeNode'
import WorkflowNode from './WorkflowNode'
import LoopNode from './LoopNode'
import DelayNode from './DelayNode'

export const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
  webhook: WebhookNode,
  function: FunctionNode,
  knowledge: KnowledgeNode,
  workflow: WorkflowNode,
  loop: LoopNode,
  delay: DelayNode,
}