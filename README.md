# Cricket Intelligence System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Learning when to use SQL vs Vector DB through a practical cricket analytics system

## 🎯 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/cricket-intelligence-system.git
cd cricket-intelligence-system

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env  # Add your GNews API key

# Run the MCP server
python -m mcp_server.main
```

See [INSTALLATION.md](INSTALLATION.md) for detailed setup.

## What We're Building

A **multi-data-source intelligence system** that demonstrates when and why to use different data storage and retrieval methods. Instead of forcing everything into one paradigm (SQL or vector search), this project shows how they complement each other for different query types.

### The Core Question

**When should you use SQL vs Vector DB?**

This project answers by building a real system where:
- **SQL** is best for structured queries and aggregations ("Who scored the most runs in 2024?")
- **Vector DB** is best for semantic similarity search ("Find articles about Kohli's batting performance")

## Why Cricket?

Cricket provides the perfect use case:
- Rich **structured data** (ball-by-ball stats, player records) → SQL
- **News articles** requiring semantic search → Vector DB
- Real-world scenarios that aren't artificially contrived
- Complex enough to be interesting, focused enough to be manageable

## Architecture Philosophy

### MCP (Model Context Protocol) Design
- **Atomic tools**: Each tool does ONE thing well
- **LLM orchestration**: The LLM intelligently chooses which tool to use
- **Smart fallback**: System self-improves by auto-ingesting data when queries find nothing

### Data Layer Strategy
- **Bronze Layer**: Raw data, preserved exactly as received
- **Silver Layer**: Cleaned, standardized for analytics
- **Separation of concerns**: Data pipelines ≠ API tools

## What's Implemented

### Data Sources

**1. Cricket Statistics (SQL/DuckDB)**
- Test cricket data (1877-2024) from Kaggle
- Bronze/Silver transformation pipeline
- 6 tables: players, matches, batting, bowling, fall_of_wickets, partnerships
- DuckDB for OLAP-optimized analytics

**2. Cricket News (Vector DB/ChromaDB)**
- GNews API integration for live cricket news
- Sentence transformers for semantic embeddings (384-dim)
- Metadata-rich storage for filtering
- **ChromaDB for local experimentation** - can be swapped for more sophisticated vector databases (Pinecone, Weaviate, Qdrant) for production workloads

### MCP Tools Available

**Cricket News Tools:**
- `search_chromadb` - Semantic search in vector database
- `query_cricket_articles` - Fetch from GNews API + auto-ingest to ChromaDB

**Cricket Stats Tools:**
- `get_database_schema` - Understand available tables and columns
- `execute_sql` - Execute safe SQL queries (SELECT only, with injection protection)
- `get_sample_queries` - Get example queries for learning

### Smart Fallback Pattern

LLM orchestrates the flow:
1. Search ChromaDB for relevant articles
2. If no results → Query GNews API → Auto-ingest to ChromaDB
3. Search ChromaDB again → Return results

The system **learns and expands** based on what users ask for.

## Key Technical Decisions

### Focus on Learning and Understanding
- Code is **readable and educational**
- Pre-aggregated datasets for faster iteration
- Clear separation between data pipelines and API tools

### SQL Injection Protection
- Uses `sqlparse` to analyze queries
- Allows SELECT and WITH (CTEs)
- Blocks all DML/DDL operations (INSERT, UPDATE, DELETE, DROP, etc.)

### Reusable Components
- **Shared utilities**: `embedder.py`, `chromadb_manager.py`, `news_fetcher.py`
- **Topic-agnostic where possible**: Easy to adapt for AI news, finance, etc.
- **Domain-specific where needed**: Cricket-optimized for performance

### Vector DB Flexibility
- **Current**: ChromaDB for local development and experimentation
- **Scalable**: Architecture supports swapping to other vector databases for enhanced performance and features
- **Pluggable design**: Change vector DB without rewriting MCP tools

## Learning Outcomes

By building this system, you learn:

1. **When SQL is the right choice**: Structured queries, aggregations, reporting
2. **When Vector DB shines**: Semantic similarity, fuzzy matching, content discovery
3. **How to combine them**: LLM-orchestrated tool selection for intelligent querying
4. **Data engineering fundamentals**: Bronze/Silver layers, schema design, ETL patterns
5. **MCP architecture**: Building atomic tools that LLMs can orchestrate
6. **Smart fallback patterns**: Self-improving systems that expand based on usage

## Technology Stack

- **MCP Server**: Python MCP SDK
- **SQL Database**: DuckDB (OLAP-optimized, embedded)
- **Vector Database**: ChromaDB (local experimentation, swappable)
- **Embeddings**: all-MiniLM-L6-v2 (384-dim, fast)
- **News API**: GNews API (free tier)
- **SQL Parsing**: sqlparse for injection protection
- **Data Processing**: pandas, PyYAML

## Design Principles

1. **Learn by doing**: Real data, real queries, real problems
2. **Keep it simple**: Educational and clear architecture
3. **Optimize where it matters**: Domain-specific schemas for performance
4. **Generalize what's common**: Reusable utilities across topics
5. **Let the LLM orchestrate**: Tools are atomic, LLM is intelligent
6. **Build for flexibility**: Easy to swap components as needs evolve

## Why This Matters

Most tutorials force you into one paradigm. This project shows:
- **Not everything belongs in SQL** (semantic search is painful in SQL)
- **Not everything belongs in Vector DB** (aggregations are awkward)
- **Each has its strengths** - use the right tool for the right query

**The right tool for the right job**, orchestrated intelligently by LLMs.

## Project Structure

```
cricket-intelligence-system/
├── data/                    # Data layer
│   ├── bronze/             # Raw data
│   └── silver/             # Cleaned, standardized data
├── mcp_server/             # MCP server implementation
│   ├── tools/              # Tool implementations
│   │   ├── cricket_stats.py
│   │   └── cricket_news.py
│   ├── utils/              # Shared utilities
│   │   ├── embedder.py
│   │   ├── chromadb_manager.py
│   │   └── news_fetcher.py
│   └── main.py             # Server entry point
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
├── INSTALLATION.md        # Setup guide
├── CONTRIBUTING.md        # Contribution guidelines
└── README.md              # This file
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📖 **Documentation**: See [INSTALLATION.md](INSTALLATION.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/cricket-intelligence-system/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/cricket-intelligence-system/discussions)

---

Built to explore multi-modal data architectures through practical cricket analytics.
