"""Database migration manager."""

import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import logging

from ..base import BaseConnector
from ..entities.base import BaseEntity
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Represents a database migration."""
    version: str
    name: str
    content: str
    checksum: str
    applied_at: Optional[datetime] = None
    
    @classmethod
    def from_file(cls, filepath: Path) -> 'Migration':
        """Create a migration from a file."""
        # Extract version and name from filename (e.g., "001_initial_schema.sql")
        match = re.match(r'^(\d+)_(.+)\.sql$', filepath.name)
        if not match:
            raise ValueError(f"Invalid migration filename: {filepath.name}")
        
        version = match.group(1)
        name = match.group(2)
        
        # Read content
        content = filepath.read_text()
        
        # Calculate checksum
        checksum = hashlib.md5(content.encode()).hexdigest()
        
        return cls(version=version, name=name, content=content, checksum=checksum)


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, connector: BaseConnector, migrations_dir: Optional[Path] = None):
        """Initialize migration manager.
        
        Args:
            connector: Database connector instance
            migrations_dir: Directory containing migration files
        """
        self.connector = connector
        self.migrations_dir = migrations_dir or Path(__file__).parent / "scripts"
        self._logger = logger
    
    async def initialize(self):
        """Initialize migration tracking table."""
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(10) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(32) NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        await self.connector.execute(create_table_sql)
        self._logger.info("Migration tracking table initialized")
    
    async def get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations."""
        query = """
            SELECT version, name, checksum, applied_at 
            FROM schema_migrations 
            ORDER BY version
        """
        
        rows = await self.connector.fetch_all(query)
        migrations = []
        
        for row in rows:
            migrations.append(Migration(
                version=row['version'],
                name=row['name'],
                checksum=row['checksum'],
                applied_at=row['applied_at']
            ))
        
        return migrations
    
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        # Get applied migrations
        applied = await self.get_applied_migrations()
        applied_versions = {m.version for m in applied}
        
        # Get all migration files
        pending = []
        if self.migrations_dir.exists():
            for filepath in sorted(self.migrations_dir.glob("*.sql")):
                try:
                    migration = Migration.from_file(filepath)
                    if migration.version not in applied_versions:
                        pending.append(migration)
                except ValueError as e:
                    self._logger.warning(f"Skipping invalid migration file: {e}")
        
        return pending
    
    async def apply_migration(self, migration: Migration):
        """Apply a single migration."""
        self._logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        try:
            # Begin transaction
            await self.connector.begin_transaction()
            
            # Execute migration SQL
            await self.connector.execute(migration.content)
            
            # Record migration
            record_sql = """
                INSERT INTO schema_migrations (version, name, checksum)
                VALUES (:version, :name, :checksum)
            """
            await self.connector.execute(record_sql, {
                'version': migration.version,
                'name': migration.name,
                'checksum': migration.checksum
            })
            
            # Commit transaction
            await self.connector.commit_transaction()
            
            self._logger.info(f"Migration {migration.version} applied successfully")
            
        except Exception as e:
            # Rollback on error
            await self.connector.rollback_transaction()
            self._logger.error(f"Migration {migration.version} failed: {e}")
            raise
    
    async def migrate(self, target_version: Optional[str] = None) -> int:
        """Run pending migrations up to target version.
        
        Args:
            target_version: Target version to migrate to (None for latest)
            
        Returns:
            Number of migrations applied
        """
        await self.initialize()
        
        pending = await self.get_pending_migrations()
        if not pending:
            self._logger.info("No pending migrations")
            return 0
        
        # Filter by target version if specified
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        # Apply migrations in order
        applied_count = 0
        for migration in pending:
            await self.apply_migration(migration)
            applied_count += 1
        
        self._logger.info(f"Applied {applied_count} migrations")
        return applied_count
    
    async def rollback(self, steps: int = 1) -> int:
        """Rollback migrations (if rollback scripts exist).
        
        Args:
            steps: Number of migrations to rollback
            
        Returns:
            Number of migrations rolled back
        """
        # Get applied migrations in reverse order
        applied = await self.get_applied_migrations()
        applied.reverse()
        
        if not applied:
            self._logger.info("No migrations to rollback")
            return 0
        
        rolled_back = 0
        for migration in applied[:steps]:
            # Look for rollback file
            rollback_file = self.migrations_dir / f"{migration.version}_{migration.name}_rollback.sql"
            
            if not rollback_file.exists():
                self._logger.warning(f"No rollback file for migration {migration.version}")
                break
            
            try:
                # Begin transaction
                await self.connector.begin_transaction()
                
                # Execute rollback
                rollback_sql = rollback_file.read_text()
                await self.connector.execute(rollback_sql)
                
                # Remove migration record
                delete_sql = "DELETE FROM schema_migrations WHERE version = :version"
                await self.connector.execute(delete_sql, {'version': migration.version})
                
                # Commit transaction
                await self.connector.commit_transaction()
                
                self._logger.info(f"Rolled back migration {migration.version}")
                rolled_back += 1
                
            except Exception as e:
                await self.connector.rollback_transaction()
                self._logger.error(f"Rollback of {migration.version} failed: {e}")
                raise
        
        return rolled_back
    
    async def status(self) -> Dict[str, Any]:
        """Get migration status."""
        await self.initialize()
        
        applied = await self.get_applied_migrations()
        pending = await self.get_pending_migrations()
        
        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'current_version': applied[-1].version if applied else None,
            'latest_version': pending[-1].version if pending else (applied[-1].version if applied else None),
            'applied': [{'version': m.version, 'name': m.name, 'applied_at': m.applied_at} for m in applied],
            'pending': [{'version': m.version, 'name': m.name} for m in pending]
        }
    
    async def create_migration(self, name: str, content: str) -> Path:
        """Create a new migration file.
        
        Args:
            name: Migration name (will be slugified)
            content: SQL content for the migration
            
        Returns:
            Path to created migration file
        """
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Get next version number
        existing = list(self.migrations_dir.glob("*.sql"))
        if existing:
            versions = []
            for f in existing:
                match = re.match(r'^(\d+)_', f.name)
                if match:
                    versions.append(int(match.group(1)))
            next_version = max(versions) + 1 if versions else 1
        else:
            next_version = 1
        
        # Format version with leading zeros
        version = f"{next_version:03d}"
        
        # Slugify name
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        
        # Create filename
        filename = f"{version}_{slug}.sql"
        filepath = self.migrations_dir / filename
        
        # Write content
        filepath.write_text(content)
        
        self._logger.info(f"Created migration: {filename}")
        return filepath