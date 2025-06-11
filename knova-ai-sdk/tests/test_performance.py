"""Performance tests for the Knova AI SDK database layer."""

import pytest
import asyncio
import time
import tempfile
from statistics import mean, median, stdev
from pathlib import Path

from knova_ai.db.connectors.sqlite import SQLiteConnector
from knova_ai.db.entities.agent import Agent
from knova_ai.db.utils.connection_pool import SQLiteConnectionPool


class TestConnectionPoolPerformance:
    """Test connection pool performance improvements."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_vs_direct(self):
        """Compare performance of pooled vs direct connections."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Test with direct connections (no pool)
            direct_times = []
            connector_direct = SQLiteConnector(db_path, use_pool=False)
            await connector_direct.connect()
            
            # Create table
            await connector_direct.execute("""
                CREATE TABLE agents (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    prompt TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Measure direct connection operations
            for i in range(50):
                start = time.time()
                agent = Agent(name=f"Agent {i}", prompt=f"Prompt {i}")
                await connector_direct.create(agent)
                direct_times.append(time.time() - start)
            
            await connector_direct.disconnect()
            
            # Test with connection pool
            pool_times = []
            connector_pool = SQLiteConnector(db_path, use_pool=True, pool_size=5)
            await connector_pool.connect()
            
            # Measure pooled operations
            for i in range(50):
                start = time.time()
                agent = Agent(name=f"Pool Agent {i}", prompt=f"Pool Prompt {i}")
                await connector_pool.create(agent)
                pool_times.append(time.time() - start)
            
            await connector_pool.disconnect()
            
            # Compare performance
            direct_avg = mean(direct_times)
            pool_avg = mean(pool_times)
            
            print(f"\nDirect connection avg: {direct_avg:.4f}s")
            print(f"Connection pool avg: {pool_avg:.4f}s")
            print(f"Improvement: {((direct_avg - pool_avg) / direct_avg * 100):.1f}%")
            
            # Pool should be faster on average
            assert pool_avg < direct_avg * 1.1  # Allow some variance
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_connection_pool_concurrent_access(self):
        """Test connection pool performance under concurrent load."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Setup pool
            pool = SQLiteConnectionPool(
                db_path=db_path,
                pool_size=5,
                max_overflow=5
            )
            await pool.initialize()
            
            # Create table
            async with pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE test_data (
                        id INTEGER PRIMARY KEY,
                        value TEXT
                    )
                """)
                await conn.commit()
            
            # Define concurrent task
            async def worker(worker_id: int, num_operations: int):
                times = []
                for i in range(num_operations):
                    start = time.time()
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO test_data (value) VALUES (?)",
                            (f"Worker {worker_id} - Op {i}",)
                        )
                        await conn.commit()
                    times.append(time.time() - start)
                return times
            
            # Run concurrent workers
            num_workers = 10
            ops_per_worker = 20
            
            start_time = time.time()
            tasks = [
                worker(i, ops_per_worker) 
                for i in range(num_workers)
            ]
            all_times = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # Analyze results
            all_operation_times = [t for times in all_times for t in times]
            avg_time = mean(all_operation_times)
            
            print(f"\nConcurrent test results:")
            print(f"Total operations: {num_workers * ops_per_worker}")
            print(f"Total time: {total_time:.2f}s")
            print(f"Avg operation time: {avg_time:.4f}s")
            print(f"Operations/second: {(num_workers * ops_per_worker) / total_time:.1f}")
            
            # Check pool statistics
            stats = pool.get_stats()
            print(f"\nPool statistics:")
            print(f"Pool hits: {stats['pool_hits']}")
            print(f"Pool misses: {stats['pool_misses']}")
            print(f"Connections reused: {stats['connections_reused']}")
            print(f"Overflow created: {stats['overflow_created']}")
            
            await pool.close()
            
            # Verify performance
            assert total_time < num_workers * ops_per_worker * 0.05  # Should be much faster than serial
            assert stats['connections_reused'] > 0  # Should reuse connections
            
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestBulkOperationsPerformance:
    """Test bulk operations performance."""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self):
        """Test bulk insert performance vs individual inserts."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create table
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Test individual inserts
        num_records = 100
        agents = [
            Agent(name=f"Agent {i}", prompt=f"Prompt {i}")
            for i in range(num_records)
        ]
        
        start = time.time()
        for agent in agents:
            await connector.create(agent)
        individual_time = time.time() - start
        
        # Clear table
        await connector.execute("DELETE FROM agents")
        
        # Test bulk insert
        start = time.time()
        await connector.bulk_create(agents)
        bulk_time = time.time() - start
        
        print(f"\nBulk insert performance:")
        print(f"Individual inserts: {individual_time:.3f}s")
        print(f"Bulk insert: {bulk_time:.3f}s")
        print(f"Speedup: {individual_time / bulk_time:.1f}x")
        
        # Bulk should be significantly faster
        assert bulk_time < individual_time * 0.5
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_bulk_update_performance(self):
        """Test bulk update performance."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create table and initial data
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Create initial agents
        num_records = 100
        agents = []
        for i in range(num_records):
            agent = Agent(name=f"Agent {i}", prompt=f"Prompt {i}")
            created = await connector.create(agent)
            agents.append(created)
        
        # Update all agents individually
        start = time.time()
        for agent in agents:
            agent.prompt = f"Updated {agent.prompt}"
            await connector.update(agent)
        individual_time = time.time() - start
        
        # Update all agents in bulk
        for agent in agents:
            agent.prompt = f"Bulk Updated {agent.prompt}"
        
        start = time.time()
        await connector.bulk_update(agents)
        bulk_time = time.time() - start
        
        print(f"\nBulk update performance:")
        print(f"Individual updates: {individual_time:.3f}s")
        print(f"Bulk update: {bulk_time:.3f}s")
        print(f"Speedup: {individual_time / bulk_time:.1f}x")
        
        # Bulk should be faster
        assert bulk_time < individual_time
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_bulk_delete_performance(self):
        """Test bulk delete performance."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create table and data
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Create agents
        num_records = 100
        agent_ids = []
        for i in range(num_records):
            agent = Agent(name=f"Agent {i}", prompt=f"Prompt {i}")
            created = await connector.create(agent)
            agent_ids.append(created.id)
        
        # Test bulk delete
        start = time.time()
        deleted_count = await connector.bulk_delete(Agent, agent_ids[:50])
        bulk_time = time.time() - start
        
        print(f"\nBulk delete performance:")
        print(f"Deleted {deleted_count} records in {bulk_time:.3f}s")
        print(f"Rate: {deleted_count / bulk_time:.1f} records/second")
        
        assert deleted_count == 50
        
        # Verify remaining records
        remaining = await connector.count(Agent)
        assert remaining == 50
        
        await connector.disconnect()


class TestQueryPerformance:
    """Test query performance optimizations."""
    
    @pytest.mark.asyncio
    async def test_indexed_query_performance(self):
        """Test performance with indexes."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            connector = SQLiteConnector(db_path)
            await connector.connect()
            
            # Create table without index
            await connector.execute("""
                CREATE TABLE test_data (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    value INTEGER,
                    created_at TEXT
                )
            """)
            
            # Insert test data
            for i in range(1000):
                await connector.execute(
                    "INSERT INTO test_data (id, name, value, created_at) VALUES (?, ?, ?, ?)",
                    {
                        'id': f"id_{i}",
                        'name': f"name_{i % 100}",
                        'value': i,
                        'created_at': f"2024-01-{(i % 30) + 1:02d}"
                    }
                )
            
            # Test query without index
            start = time.time()
            for _ in range(100):
                await connector.fetch_all(
                    "SELECT * FROM test_data WHERE name = :name",
                    {'name': 'name_50'}
                )
            no_index_time = time.time() - start
            
            # Create index
            await connector.execute("CREATE INDEX idx_name ON test_data(name)")
            
            # Test query with index
            start = time.time()
            for _ in range(100):
                await connector.fetch_all(
                    "SELECT * FROM test_data WHERE name = :name",
                    {'name': 'name_50'}
                )
            with_index_time = time.time() - start
            
            print(f"\nIndex performance:")
            print(f"Without index: {no_index_time:.3f}s")
            print(f"With index: {with_index_time:.3f}s")
            print(f"Speedup: {no_index_time / with_index_time:.1f}x")
            
            # Index should improve performance
            assert with_index_time < no_index_time
            
            await connector.disconnect()
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_pagination_performance(self):
        """Test pagination performance with LIMIT and OFFSET."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create table and data
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Insert many records
        agents = []
        for i in range(1000):
            agent = Agent(name=f"Agent {i:04d}", prompt=f"Prompt {i}")
            agents.append(agent)
        
        await connector.bulk_create(agents)
        
        # Test different page sizes
        page_sizes = [10, 50, 100, 500]
        times = {}
        
        for page_size in page_sizes:
            start = time.time()
            
            # Fetch all pages
            offset = 0
            total_fetched = 0
            while offset < 1000:
                results = await connector.list(Agent, limit=page_size, offset=offset)
                total_fetched += len(results)
                offset += page_size
                if not results:
                    break
            
            times[page_size] = time.time() - start
            assert total_fetched == 1000
        
        print(f"\nPagination performance:")
        for page_size, duration in times.items():
            print(f"Page size {page_size}: {duration:.3f}s")
        
        # Larger pages should generally be more efficient
        assert times[100] < times[10] * 1.5
        
        await connector.disconnect()


class TestMemoryPerformance:
    """Test memory usage and efficiency."""
    
    @pytest.mark.asyncio
    async def test_large_result_set_memory(self):
        """Test memory efficiency with large result sets."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create table
        await connector.execute("""
            CREATE TABLE large_data (
                id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        
        # Create large data entries
        large_text = "x" * 1000  # 1KB per record
        
        # Insert many records
        for i in range(1000):
            await connector.execute(
                "INSERT INTO large_data (id, data) VALUES (?, ?)",
                {'id': f"id_{i}", 'data': large_text}
            )
        
        # Test fetching all at once
        start = time.time()
        results = await connector.fetch_all("SELECT * FROM large_data")
        fetch_time = time.time() - start
        
        print(f"\nLarge result set performance:")
        print(f"Fetched {len(results)} records in {fetch_time:.3f}s")
        print(f"Rate: {len(results) / fetch_time:.1f} records/second")
        
        assert len(results) == 1000
        
        await connector.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])