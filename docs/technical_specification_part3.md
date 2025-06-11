# Knova AI: Technical Specification (Part 3)

## 4. Knowledge Base Integration

### 4.1 Knowledge Base Architecture

#### 4.1.1 Technology Stack
- **Vector Database**: Qdrant or Pinecone
- **Embedding Models**: OpenAI, Google, or other provider embeddings
- **Document Processing**: LangChain or LlamaIndex for document ingestion
- **Storage**: S3-compatible object storage for raw documents

#### 4.1.2 Knowledge Base Components
- **Document Processor**: Handles document parsing, chunking, and embedding
- **Vector Store**: Stores and retrieves document embeddings
- **Query Engine**: Processes natural language queries against the vector store
- **Metadata Store**: Manages document metadata and access controls

#### 4.1.3 Integration with Agent Runtime
Knowledge base integration will be implemented using LiveKit's tool calling capabilities:

```python
class KnowledgeBaseConnector:
    def __init__(self, knowledge_base_id: str, user_id: str):
        self.knowledge_base_id = knowledge_base_id
        self.user_id = user_id
        self.vector_store = self._init_vector_store()
    
    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        # Generate embeddings for the query
        embedding = await generate_embedding(query)
        
        # Search the vector store
        results = await self.vector_store.search(
            embedding=embedding,
            top_k=top_k,
            filter={"knowledge_base_id": self.knowledge_base_id}
        )
        
        # Format results for the agent
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.payload["content"],
                "metadata": result.payload["metadata"],
                "score": result.score
            })
        
        return formatted_results
```

### 4.2 Document Processing Pipeline

#### 4.2.1 Document Ingestion Flow
1. User uploads document(s) through the frontend
2. Backend validates and stores raw documents in object storage
3. Document processor parses documents into chunks
4. Chunks are embedded and stored in the vector database
5. Metadata is stored in the relational database

#### 4.2.2 Document Types Support
- Text documents (PDF, DOCX, TXT)
- Web pages (HTML)
- Structured data (JSON, CSV)
- Future: Audio and video transcripts

## 5. Function Calling & Tool Integration

### 5.1 Function Registry

#### 5.1.1 Function Definition Schema
```typescript
interface FunctionDefinition {
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, {
      type: string;
      description: string;
      enum?: string[];
      required?: boolean;
    }>;
    required: string[];
  };
  response_schema: {
    type: string;
    properties: Record<string, {
      type: string;
      description: string;
    }>;
  };
}
```

#### 5.1.2 Function Categories
- **System Functions**: Core platform capabilities (e.g., knowledge base search)
- **Integration Functions**: Pre-built integrations with external services
- **Custom Functions**: User-defined functions via Composio or custom webhooks

### 5.2 Composio Integration

#### 5.2.1 Composio Connector
```python
class ComposioConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.composio.dev/v1"
        
    async def execute_function(self, function_name: str, parameters: dict) -> dict:
        """Execute a function via Composio."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "function": function_name,
            "parameters": parameters
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/execute",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Composio API error: {error_text}")
                
                return await response.json()
```

#### 5.2.2 Function Registration
Functions from Composio will be dynamically registered with the agent:

```python
def _register_composio_tools(self, composio_functions: list[dict]):
    """Register Composio functions as tools."""
    for func in composio_functions:
        # Create a dynamic function tool
        @function_tool(
            name=func["name"],
            description=func["description"]
        )
        async def execute_composio_function(
            self,
            context: RunContext,
            **kwargs
        ) -> dict:
            """Execute a Composio function."""
            return await self.composio_connector.execute_function(
                function_name=func["name"],
                parameters=kwargs
            )
        
        # Add the function to the agent
        setattr(self, f"composio_{func['name']}", execute_composio_function)
```
