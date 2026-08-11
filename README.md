# Multi-Hop Retrieval Agent

An agentic Retrieval-Augmented Generation (RAG) system that decomposes complex questions, retrieves evidence iteratively, evaluates whether the available evidence is sufficient, and generates grounded answers from uploaded documents.

## Overview

Traditional RAG typically follows a fixed pipeline:

`Query → Retrieval → Generation`

This project extends that workflow with an adaptive research loop:

`Query → Planning → Retrieval → Reflection → Additional Retrieval (if required) → Synthesis → Groundedness Verification`

The agent maintains a research state across retrieval hops and decides whether additional evidence is required before generating the final answer.

## Key Features

- LLM-based query planning and decomposition
- Complexity-based routing for simple and complex queries
- Multi-hop adaptive retrieval
- ChromaDB vector search with embedding-based retrieval
- Parallel retrieval of independent sub-questions using `asyncio`
- Pydantic validation for API requests and structured LLM outputs
- Retry and exponential backoff for LLM calls
- Bounded agent execution with maximum hop limits
- Query tracking and duplicate prevention
- Research-trail and execution-metric tracking
- LLM-based answer synthesis
- Groundedness verification against retrieved evidence
- FastAPI backend
- React and TypeScript frontend
- PDF ingestion with overlapping text chunks

## Architecture

```text
                         User Query
                              |
                              v
                     +----------------+
                     | Query Planner  |
                     |                |
                     | Complexity     |
                     | Decomposition  |
                     +-------+--------+
                             |
                             v
                     +----------------+
                     | Research State |
                     +-------+--------+
                             |
                             v
                  +------------------------+
                  | Parallel Retrieval     |
                  |        ChromaDB        |
                  +-----------+------------+
                              |
                              v
                     +----------------+
                     |   Reflection   |
                     |                |
                     | Enough evidence|
                     |      ?         |
                     +-------+--------+
                             |
                   +---------+---------+
                   |                   |
                  Yes                  No
                   |                   |
                   v                   v
              Synthesis          Generate Query
                   |                   |
                   |                   v
                   |              Retrieve Again
                   |                   |
                   |              Reflection
                   |                   |
                   +---------+---------+
                             |
                             v
                  Groundedness Check
                             |
                             v
                       Final Answer
```

## How It Works

### 1. Document Ingestion

Uploaded PDFs are processed by extracting their text, splitting it into overlapping chunks, generating embeddings, and storing the resulting vectors in ChromaDB.

### 2. Query Planning

The planner analyzes the user's question and produces a structured research plan containing the query complexity, research goal, and sub-questions.

Simple questions can bypass decomposition and use direct retrieval. Complex questions are divided into independent research tasks.

### 3. Initial Retrieval

For complex queries, independent sub-questions are retrieved concurrently. Retrieved chunks are accumulated in the research state and deduplicated.

### 4. Reflection

The reflection model evaluates the evidence collected so far and returns a structured decision containing:

- Whether the evidence is sufficient
- Reasoning for the decision
- Missing information
- Confidence
- A next query when additional evidence is required

### 5. Multi-Hop Retrieval

If the evidence is insufficient, the agent generates a new query based on the identified information gap and performs another retrieval hop.

Execution is bounded by a maximum hop count and previously visited queries are tracked to prevent unnecessary repetition.

### 6. Synthesis

Once sufficient evidence has been collected, the synthesis model generates the final answer using the research goal, original question, and accumulated evidence.

### 7. Groundedness Verification

The generated answer is evaluated against the retrieved evidence to identify unsupported claims and estimate how well the answer is grounded in the available context.

## Why Multi-Hop Retrieval

A single retrieval step can fail when the information required to answer a question is distributed across multiple documents or concepts.

Instead of increasing the retrieval size indiscriminately, this system uses an adaptive loop:

```text
Retrieve
   |
Reflect
   |
   +-- Sufficient --> Synthesize
   |
   +-- Insufficient --> Identify gap
                              |
                              v
                         New query
                              |
                              v
                           Retrieve
```

This allows retrieval depth to depend on the information actually required by the question.

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- ChromaDB
- Sentence Transformers
- PyPDF
- asyncio
- Tenacity

### LLM

- Groq API
- Llama 3.3 70B Versatile

### Frontend

- React
- TypeScript
- Vite
- React Markdown

## Project Structure

```text
Multi-Hop-Retrieval-Agent/
├── app_data/
│   ├── main.py
│   ├── agentic_loop.py
│   ├── decomposition.py
│   ├── reflection.py
│   ├── retrieval.py
│   ├── ingestion.py
│   ├── synthesis.py
│   ├── models.py
│   ├── prompts.py
│   └── ...
├── frontend/
│   └── src/
├── data/
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Local Setup

### Backend

```bash
git clone https://github.com/AdarshBobade/Multi-Hop-Retrieval-Agent.git
cd Multi-Hop-Retrieval-Agent

python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

Start the backend:

```bash
uvicorn app_data.main:app --reload --port 8000
```

API documentation:

`http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Example

A complex question can be processed as:

```text
User Question
      |
      v
Query Decomposition
      |
      +---- Sub-question 1
      +---- Sub-question 2
      +---- Sub-question 3
                    |
                    v
             Parallel Retrieval
                    |
                    v
                Reflection
                    |
          +---------+---------+
          |                   |
       Sufficient        Insufficient
          |                   |
          v                   v
      Synthesis          New Query
                              |
                              v
                         Next Hop
                              |
                              v
                         Reflection
                              |
                              v
                         Synthesis
```

The API response also exposes the research trail and execution metadata, allowing the retrieval process to be inspected rather than treated as a black box.

## Engineering Considerations

The system uses several controls around probabilistic LLM behavior:

- Pydantic validation for structured outputs
- Retry with exponential backoff
- Maximum hop limits
- Visited-query tracking
- Explicit research state
- Retrieval and LLM call counters
- Exception handling and logging
- Groundedness verification

These controls separate model-generated decisions from deterministic application logic and keep the agent's execution bounded and observable.

## Roadmap

- Hybrid semantic and keyword retrieval
- Similarity-based chunk deduplication
- Cross-encoder reranking
- Improved query similarity detection
- No-new-evidence termination
- Page-level citations
- Retrieval and LLM latency metrics
- Token and cost tracking
- Stage 1 versus multi-hop retrieval benchmarking
- Web search integration
- Streaming research-trail visualization

## License

MIT License.
