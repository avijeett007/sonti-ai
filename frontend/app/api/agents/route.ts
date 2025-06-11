import { NextRequest, NextResponse } from 'next/server'

// Mock data for now - will be replaced with database
let agents: any[] = []

export async function GET() {
  return NextResponse.json(agents)
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  
  const agent = {
    id: Math.random().toString(36).substr(2, 9),
    ...body,
    created_at: new Date().toISOString(),
    status: 'active',
  }
  
  agents.push(agent)
  
  return NextResponse.json(agent, { status: 201 })
}