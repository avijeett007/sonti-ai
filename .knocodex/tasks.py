import os
import sys
import time
from redis import Redis
from rq import Queue

# Redis connection
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
queue_name = os.environ.get('REDIS_QUEUE', 'knocodex')
redis_conn = Redis.from_url(redis_url)
queue = Queue(queue_name, connection=redis_conn)

# Safely import from worker - add appropriate path first
worker_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(worker_path)

# Define placeholder functions in case imports fail
def process_github_issue(issue_number):
    '''Process a GitHub issue'''
    raise NotImplementedError("Worker module not properly loaded")

def update_project_documentation():
    '''Update project documentation'''
    raise NotImplementedError("Worker module not properly loaded")

def review_pull_request(pr_number):
    '''Review a pull request'''
    raise NotImplementedError("Worker module not properly loaded")

# Try to import the actual implementations
try:
    from worker import process_github_issue, update_project_documentation, review_pull_request
    print("Successfully imported worker functions")
except ImportError as e:
    print(f"Warning: Could not import from worker: {e}")
    # Continue with placeholder functions

def enqueue_process_github_issue(issue_number):
    '''Add a GitHub issue processing task to the queue'''
    job = queue.enqueue(
        process_github_issue,
        issue_number,
        job_timeout='2h',  # Long timeout for complex issues
        result_ttl=86400,  # Keep results for 24 hours
        ttl=86400          # Job can wait in queue for up to 24 hours
    )
    return job.id

def enqueue_update_documentation():
    '''Add a documentation update task to the queue'''
    job = queue.enqueue(
        update_project_documentation,
        job_timeout='1h',
        result_ttl=86400,
        ttl=86400
    )
    return job.id

def enqueue_review_pull_request(pr_number):
    '''Add a PR review task to the queue'''
    job = queue.enqueue(
        review_pull_request,
        pr_number,
        job_timeout='1h',
        result_ttl=86400,
        ttl=86400
    )
    return job.id
