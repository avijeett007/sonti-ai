import { NextRequest, NextResponse } from 'next/server'

// Mock data for now
let workflows: any[] = []

export async function GET() {
  return NextResponse.json(workflows)
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  
  const workflow = {
    id: Math.random().toString(36).substr(2, 9),
    ...body,
    created_at: new Date().toISOString(),
    node_count: 0,
  }
  
  workflows.push(workflow)
  
  return NextResponse.json(workflow, { status: 201 })
}