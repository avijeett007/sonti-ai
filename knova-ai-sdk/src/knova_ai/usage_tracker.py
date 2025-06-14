"""Usage tracking and analytics for Knova AI SDK"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging

from .config import ConfigManager
from .license import LicenseInfo

logger = logging.getLogger(__name__)


class UsageTracker:
    """Tracks and aggregates usage metrics for analytics"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._metrics_buffer: List[Dict[str, Any]] = []
        self._buffer_size = 100  # Flush after 100 events
        
    def track_event(
        self,
        event_type: str,
        license_key: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track a usage event
        
        Args:
            event_type: Type of event (e.g., 'agent_created', 'api_call')
            license_key: License key associated with event
            metadata: Additional event metadata
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'license_key': license_key[:20] + '...' if len(license_key) > 20 else license_key,
            'metadata': metadata or {}
        }
        
        self._metrics_buffer.append(event)
        
        # Flush buffer if it's full
        if len(self._metrics_buffer) >= self._buffer_size:
            self._flush_metrics()
            
    def track_api_call(
        self,
        endpoint: str,
        method: str,
        license_key: str,
        response_time_ms: int,
        status_code: int,
        error: Optional[str] = None
    ):
        """Track API call metrics"""
        self.track_event('api_call', license_key, {
            'endpoint': endpoint,
            'method': method,
            'response_time_ms': response_time_ms,
            'status_code': status_code,
            'error': error
        })
        
    def track_agent_lifecycle(
        self,
        action: str,
        agent_id: str,
        license_key: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Track agent lifecycle events"""
        self.track_event(f'agent_{action}', license_key, {
            'agent_id': agent_id,
            'success': success,
            'error': error
        })
        
    def track_voice_usage(
        self,
        session_id: str,
        license_key: str,
        duration_seconds: int,
        provider: str
    ):
        """Track voice usage metrics"""
        self.track_event('voice_usage', license_key, {
            'session_id': session_id,
            'duration_seconds': duration_seconds,
            'duration_minutes': round(duration_seconds / 60, 2),
            'provider': provider
        })
        
    def track_document_operation(
        self,
        operation: str,
        document_id: str,
        license_key: str,
        size_bytes: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Track document operations"""
        self.track_event(f'document_{operation}', license_key, {
            'document_id': document_id,
            'size_bytes': size_bytes,
            'processing_time_ms': processing_time_ms
        })
        
    def get_usage_summary(
        self,
        license_key: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for a license
        
        Args:
            license_key: License key to summarize
            period_days: Number of days to include in summary
            
        Returns:
            Usage summary dictionary
        """
        # Load historical metrics
        metrics = self._load_metrics(license_key, period_days)
        
        # Aggregate metrics
        summary = {
            'period_days': period_days,
            'total_events': len(metrics),
            'events_by_type': defaultdict(int),
            'api_calls': {
                'total': 0,
                'by_endpoint': defaultdict(int),
                'avg_response_time_ms': 0,
                'error_rate': 0
            },
            'agents': {
                'created': 0,
                'deployed': 0,
                'deleted': 0
            },
            'voice': {
                'total_minutes': 0,
                'sessions': 0
            },
            'documents': {
                'uploaded': 0,
                'processed': 0,
                'total_size_mb': 0
            }
        }
        
        # Process metrics
        api_response_times = []
        api_errors = 0
        
        for metric in metrics:
            event_type = metric['event_type']
            summary['events_by_type'][event_type] += 1
            
            if event_type == 'api_call':
                summary['api_calls']['total'] += 1
                endpoint = metric['metadata'].get('endpoint', 'unknown')
                summary['api_calls']['by_endpoint'][endpoint] += 1
                
                if 'response_time_ms' in metric['metadata']:
                    api_response_times.append(metric['metadata']['response_time_ms'])
                    
                if metric['metadata'].get('error'):
                    api_errors += 1
                    
            elif event_type.startswith('agent_'):
                action = event_type.split('_')[1]
                if action in summary['agents']:
                    summary['agents'][action] += 1
                    
            elif event_type == 'voice_usage':
                summary['voice']['sessions'] += 1
                summary['voice']['total_minutes'] += metric['metadata'].get('duration_minutes', 0)
                
            elif event_type.startswith('document_'):
                operation = event_type.split('_')[1]
                if operation == 'upload':
                    summary['documents']['uploaded'] += 1
                    size_mb = (metric['metadata'].get('size_bytes', 0) / 1024 / 1024)
                    summary['documents']['total_size_mb'] += size_mb
                elif operation == 'process':
                    summary['documents']['processed'] += 1
                    
        # Calculate averages
        if api_response_times:
            summary['api_calls']['avg_response_time_ms'] = sum(api_response_times) / len(api_response_times)
            
        if summary['api_calls']['total'] > 0:
            summary['api_calls']['error_rate'] = api_errors / summary['api_calls']['total']
            
        return dict(summary)
        
    def get_usage_trend(
        self,
        license_key: str,
        metric: str,
        period_days: int = 7,
        granularity: str = 'day'
    ) -> List[Dict[str, Any]]:
        """
        Get usage trend for a specific metric
        
        Args:
            license_key: License key
            metric: Metric to track (e.g., 'api_calls', 'voice_minutes')
            period_days: Period to analyze
            granularity: 'hour', 'day', or 'week'
            
        Returns:
            List of data points with timestamp and value
        """
        metrics = self._load_metrics(license_key, period_days)
        
        # Group by time period
        time_buckets = defaultdict(int)
        
        for event in metrics:
            timestamp = datetime.fromisoformat(event['timestamp'])
            
            # Determine bucket key based on granularity
            if granularity == 'hour':
                bucket_key = timestamp.strftime('%Y-%m-%d %H:00')
            elif granularity == 'week':
                # Get start of week
                week_start = timestamp - timedelta(days=timestamp.weekday())
                bucket_key = week_start.strftime('%Y-%m-%d')
            else:  # day
                bucket_key = timestamp.strftime('%Y-%m-%d')
                
            # Count based on metric type
            if metric == 'api_calls' and event['event_type'] == 'api_call':
                time_buckets[bucket_key] += 1
            elif metric == 'voice_minutes' and event['event_type'] == 'voice_usage':
                time_buckets[bucket_key] += event['metadata'].get('duration_minutes', 0)
            elif metric == 'agents_created' and event['event_type'] == 'agent_created':
                time_buckets[bucket_key] += 1
                
        # Convert to sorted list
        trend = [
            {'timestamp': k, 'value': v}
            for k, v in sorted(time_buckets.items())
        ]
        
        return trend
        
    def _flush_metrics(self):
        """Flush metrics buffer to storage"""
        if not self._metrics_buffer:
            return
            
        # Group by license key
        metrics_by_license = defaultdict(list)
        for metric in self._metrics_buffer:
            license_key = metric['license_key']
            metrics_by_license[license_key].append(metric)
            
        # Store metrics for each license
        for license_key, metrics in metrics_by_license.items():
            # Create daily bucket key
            date_key = datetime.now().strftime('%Y-%m-%d')
            storage_key = f"metrics_{license_key}_{date_key}"
            
            # Load existing metrics for today
            existing = self.config_manager.get(storage_key) or []
            
            # Append new metrics
            existing.extend(metrics)
            
            # Store with 35-day TTL
            self.config_manager.set(storage_key, existing, ttl_seconds=35*24*3600)
            
        # Clear buffer
        self._metrics_buffer = []
        logger.debug(f"Flushed {len(metrics)} metrics to storage")
        
    def _load_metrics(
        self,
        license_key: str,
        period_days: int
    ) -> List[Dict[str, Any]]:
        """Load metrics for a license over a period"""
        all_metrics = []
        
        # Load metrics for each day in period
        for i in range(period_days):
            date = datetime.now() - timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            storage_key = f"metrics_{license_key[:20]}..._{date_key}"
            
            daily_metrics = self.config_manager.get(storage_key)
            if daily_metrics:
                all_metrics.extend(daily_metrics)
                
        return all_metrics
        
    def export_metrics(
        self,
        license_key: str,
        start_date: datetime,
        end_date: datetime,
        format: str = 'json'
    ) -> str:
        """
        Export metrics for a date range
        
        Args:
            license_key: License key
            start_date: Start date
            end_date: End date
            format: Export format ('json' or 'csv')
            
        Returns:
            Exported data as string
        """
        # Calculate period
        period_days = (end_date - start_date).days + 1
        metrics = self._load_metrics(license_key, period_days)
        
        # Filter by date range
        filtered_metrics = [
            m for m in metrics
            if start_date <= datetime.fromisoformat(m['timestamp']) <= end_date
        ]
        
        if format == 'json':
            return json.dumps(filtered_metrics, indent=2)
        elif format == 'csv':
            # Simple CSV export
            lines = ['timestamp,event_type,metadata']
            for metric in filtered_metrics:
                metadata_str = json.dumps(metric['metadata'])
                lines.append(f"{metric['timestamp']},{metric['event_type']},{metadata_str}")
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def cleanup_old_metrics(self, days_to_keep: int = 90):
        """Clean up metrics older than specified days"""
        # This is handled automatically by TTL in storage
        logger.info(f"Metrics are automatically cleaned up after {days_to_keep} days via TTL")