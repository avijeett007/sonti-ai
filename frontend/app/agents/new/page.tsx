'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Textarea } from '@/components/ui/Textarea'

export default function NewAgentPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    llm_provider: 'openai',
    llm_model: 'gpt-4',
    stt_provider: 'deepgram',
    tts_provider: 'elevenlabs',
    prompt: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch('/api/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        const agent = await response.json()
        router.push(`/agents/${agent.id}`)
      }
    } catch (error) {
      console.error('Failed to create agent:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Create New Agent</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            Agent Name
          </label>
          <Input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Customer Support Agent"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              LLM Provider
            </label>
            <Select
              value={formData.llm_provider}
              onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
            >
              <option value="openai">OpenAI</option>
              <option value="google">Google</option>
              <option value="anthropic">Anthropic</option>
              <option value="azure">Azure</option>
              <option value="aws">AWS Bedrock</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              LLM Model
            </label>
            <Select
              value={formData.llm_model}
              onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gemini-pro">Gemini Pro</option>
              <option value="claude-3">Claude 3</option>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              STT Provider
            </label>
            <Select
              value={formData.stt_provider}
              onChange={(e) => setFormData({ ...formData, stt_provider: e.target.value })}
            >
              <option value="deepgram">Deepgram</option>
              <option value="openai">OpenAI Whisper</option>
              <option value="google">Google Cloud STT</option>
              <option value="azure">Azure Speech</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              TTS Provider
            </label>
            <Select
              value={formData.tts_provider}
              onChange={(e) => setFormData({ ...formData, tts_provider: e.target.value })}
            >
              <option value="elevenlabs">ElevenLabs</option>
              <option value="openai">OpenAI TTS</option>
              <option value="google">Google Cloud TTS</option>
              <option value="azure">Azure Speech</option>
              <option value="aws">AWS Polly</option>
            </Select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            System Prompt
          </label>
          <Textarea
            value={formData.prompt}
            onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
            placeholder="You are a helpful AI assistant..."
            rows={6}
          />
        </div>

        <div className="flex gap-4">
          <Button type="submit" disabled={loading}>
            {loading ? 'Creating...' : 'Create Agent'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/agents')}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}