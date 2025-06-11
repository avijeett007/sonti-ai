"use client"

import React from 'react'
import { Button } from '@/components/ui/Button'

interface WorkflowToolbarProps {
  isAdvancedMode: boolean
  onToggleMode: () => void
  onSave: () => void
  onDeploy: () => void
  onClear: () => void
}

export default function WorkflowToolbar({
  isAdvancedMode,
  onToggleMode,
  onSave,
  onDeploy,
  onClear,
}: WorkflowToolbarProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-2 flex items-center gap-2">
      <Button onClick={onToggleMode} variant="secondary" size="sm">
        {isAdvancedMode ? '🎯 Simple Mode' : '⚡ Advanced Mode'}
      </Button>
      
      <div className="w-px h-6 bg-gray-300" />
      
      <Button onClick={onClear} variant="secondary" size="sm">
        🗑️ Clear
      </Button>
      
      <Button onClick={onSave} variant="secondary" size="sm">
        💾 Save
      </Button>
      
      <Button onClick={onDeploy} variant="primary" size="sm">
        🚀 Deploy
      </Button>
    </div>
  )
}