# Overview

MineSearch 2.0 is a comprehensive multi-agent mining research system that provides automated data collection and analysis for mining operations worldwide. The system features a FastAPI backend with SQLite database storage and a modern web frontend for interactive research and data visualization. It supports both single mine searches and batch CSV uploads, with intelligent AI-powered data extraction from 30+ specialized providers including Claude, GPT-4, Perplexity, and OpenRouter models.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Technology Stack**: Vanilla JavaScript, HTML5, CSS3 with modern responsive design
- **UI Framework**: Tab-based navigation system with radio button controls
- **Component System**: Modular JavaScript files for different functionalities (event-handlers.js, data-cards.js, display.js)
- **State Management**: Browser-based session management with localStorage for preferences
- **API Integration**: REST API client with fetch-based HTTP requests to FastAPI backend

## Backend Architecture  
- **Framework**: FastAPI (Python) with uvicorn server
- **Database**: SQLite with SQLAlchemy ORM for data persistence
- **Service Layer**: Modular service architecture with MineSearchService, DatabaseManager, and ProviderRegistry
- **API Design**: RESTful endpoints for search, batch processing, statistics, and data export
- **Data Processing**: Multi-stage pipeline with extraction processors, source managers, and consolidation logic

## Core Data Models
- **SearchResult**: Individual mine search results with structured data
- **Sources**: Reference data with reliability scoring and classification
- **Statistics**: Model performance tracking and field-level analytics
- **Session Management**: Progress tracking for batch operations

## Multi-Agent Provider System
- **Provider Registry**: 55+ AI models from OpenAI, Anthropic, Perplexity, OpenRouter
- **Smart Model Selection**: Automated provider selection based on query type and performance
- **Parallel Processing**: Concurrent requests to multiple providers for data validation
- **Result Consolidation**: Confidence-based scoring and intelligent data merging

# External Dependencies

## AI Providers & APIs
- **OpenAI**: GPT-4, GPT-3.5-turbo for structured data extraction
- **Anthropic**: Claude models for complex mining data analysis
- **Perplexity**: Real-time web search and source attribution
- **OpenRouter**: Access to 30+ additional AI models (Mistral, DeepSeek, etc.)
- **Tavily**: Specialized web search for mining industry sources

## Development Tools & MCP Servers
- **GitHub Integration**: Repository management and version control
- **Puppeteer**: Browser automation for testing and UI validation
- **Memory Server**: Persistent context storage for development
- **Filesystem Server**: Project file operations and management

## Data Sources & Integrations
- **Government Databases**: Mining registries from Canada, Australia, Chile
- **Industry Sources**: Mining technology websites, company reports
- **Academic Sources**: Geological surveys and research publications
- **Real-time Data**: Web scraping for current mining operations data

## Infrastructure
- **Port Standard**: Backend runs exclusively on port 8000
- **Static Assets**: Frontend served via FastAPI static file serving at /static/
- **Database**: SQLite file-based storage at /app/data/minesearch.db
- **Caching**: Request-response caching to minimize API costs and improve performance