import Link from 'next/link'
import { Button } from '@/components/ui/Button'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold">Knova AI</h1>
        <p className="text-xl text-muted-foreground max-w-2xl">
          Open-source Voice AI Agent platform. Build intelligent voice agents 
          with multi-provider support, visual workflows, and enterprise-ready features.
        </p>
        
        <div className="flex gap-4 justify-center pt-6">
          <Link href="/agents">
            <Button size="lg">Get Started</Button>
          </Link>
          <Link href="https://docs.knova.ai" target="_blank">
            <Button size="lg" variant="outline">Documentation</Button>
          </Link>
        </div>
        
        <div className="pt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
          <div className="border rounded-lg p-6">
            <h3 className="font-semibold text-lg mb-2">🎯 Simple API</h3>
            <p className="text-sm text-muted-foreground">
              Create voice agents with just a few lines of Python code
            </p>
          </div>
          
          <div className="border rounded-lg p-6">
            <h3 className="font-semibold text-lg mb-2">🔧 Multi-Provider</h3>
            <p className="text-sm text-muted-foreground">
              Support for OpenAI, Google, Azure, AWS, and more
            </p>
          </div>
          
          <div className="border rounded-lg p-6">
            <h3 className="font-semibold text-lg mb-2">📱 SIP Ready</h3>
            <p className="text-sm text-muted-foreground">
              Built-in telephony support with Twilio, Telnyx, and Plivo
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}