# DataMorph GitHub Repository Structure

This document describes the complete file structure of the DataMorph repository.

## 📁 Repository Structure

```
datamorph/
├── 📄 README.md                    # Main README with animated diagrams
├── 📄 LICENSE                      # MIT License
├── 📄 CONTRIBUTING.md              # Contribution guidelines
├── 📄 SETUP.md                     # Detailed setup instructions
├── 📄 ARCHITECTURE.md              # System architecture documentation
├── 📄 FILE_STRUCTURE.md            # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 .gitignore                   # Git ignore rules
├── 📄 config.example.json          # Configuration template
│
├── 📁 src/                         # Source code
│   ├── 📁 flask_app/               # Flask API Gateway
│   │   └── 📄 app.py               # Main Flask application
│   │
│   ├── 📁 lambdas/                 # Lambda functions
│   │   ├── 📁 orchestrator/        # Orchestrator Lambda
│   │   │   └── 📄 handler.py
│   │   ├── 📁 specs_generator/     # Specs Generator Lambda
│   │   │   └── 📄 handler.py
│   │   ├── 📁 glue_executor/       # Glue Executor Lambda
│   │   │   └── 📄 handler.py
│   │   ├── 📁 validator/           # Validator Lambda
│   │   │   └── 📄 handler.py
│   │   ├── 📁 remediator/          # Remediator Lambda
│   │   │   └── 📄 handler.py
│   │   └── 📁 logger/              # Logger Lambda
│   │       └── 📄 handler.py
│   │
│   └── 📁 shared/                  # Shared utilities
│       ├── 📄 __init__.py
│       ├── 📄 config.py            # Configuration management
│       ├── 📄 utils.py             # Utility functions
│       ├── 📄 logger.py            # Logging utilities
│       └── 📄 aws_clients.py       # AWS client wrappers
│
├── 📁 docs/                        # Documentation
│   ├── 📄 README.md                # Documentation index
│   ├── 📄 AGENT_01_FLASK_API.md    # Flask API documentation
│   ├── 📄 AGENT_02_ORCHESTRATOR.md # Orchestrator documentation
│   ├── 📄 AGENT_03_SPECS_GENERATOR.md # Specs Generator docs
│   ├── 📄 AGENT_04_GLUE_EXECUTOR.md   # Glue Executor docs
│   ├── 📄 AGENT_05_VALIDATOR.md       # Validator documentation
│   ├── 📄 AGENT_06_REMEDIATOR.md      # Remediator documentation
│   └── 📄 AGENT_07_LOGGER.md          # Logger documentation
│
├── 📁 examples/                    # Example scripts
│   ├── 📄 simple_etl.py            # Simple ETL example
│   ├── 📄 complex_etl.py           # Complex ETL example
│   └── 📄 README.md                # Examples documentation
│
└── 📁 .github/                     # GitHub specific files
    ├── 📁 workflows/               # GitHub Actions
    │   └── 📄 ci.yml               # CI/CD pipeline
    └── 📄 ISSUE_TEMPLATE.md        # Issue template
```

## 📝 File Descriptions

### Root Files

| File | Description |
|------|-------------|
| `README.md` | Main project README with animated diagrams, features, and quick start |
| `LICENSE` | MIT License for the project |
| `CONTRIBUTING.md` | Guidelines for contributing to the project |
| `SETUP.md` | Step-by-step setup instructions for AWS deployment |
| `ARCHITECTURE.md` | Detailed system architecture documentation |
| `requirements.txt` | Python package dependencies |
| `.gitignore` | Files and directories to ignore in git |
| `config.example.json` | Template configuration file (sanitized) |

### Source Code (`src/`)

#### Flask App
- `src/flask_app/app.py` - Flask REST API providing HTTP interface and database proxy

#### Lambda Functions
- `src/lambdas/orchestrator/handler.py` - Central workflow coordinator
- `src/lambdas/specs_generator/handler.py` - Natural language to ETL specs converter
- `src/lambdas/glue_executor/handler.py` - PySpark code generator and executor
- `src/lambdas/validator/handler.py` - Hybrid validation system (5 phases)
- `src/lambdas/remediator/handler.py` - Autonomous error correction system
- `src/lambdas/logger/handler.py` - Centralized logging service

#### Shared Utilities
- `src/shared/config.py` - Configuration management (loads from Secrets Manager)
- `src/shared/utils.py` - Utility functions (run_id generation, retry logic, etc.)
- `src/shared/logger.py` - Logging utilities and formatters
- `src/shared/aws_clients.py` - AWS service client wrappers

### Documentation (`docs/`)

Comprehensive documentation for each agent:

| Document | Description |
|----------|-------------|
| `AGENT_01_FLASK_API.md` | Flask API Gateway - HTTP interface and database operations |
| `AGENT_02_ORCHESTRATOR.md` | Orchestrator Lambda - Workflow coordination |
| `AGENT_03_SPECS_GENERATOR.md` | Specs Generator - Natural language processing |
| `AGENT_04_GLUE_EXECUTOR.md` | Glue Executor - Code generation and execution |
| `AGENT_05_VALIDATOR.md` | Validator - Hybrid validation system |
| `AGENT_06_REMEDIATOR.md` | Remediator - Autonomous error correction |
| `AGENT_07_LOGGER.md` | Logger - Centralized logging |

Each agent document includes:
- Name and role
- Services used
- Input/output formats
- Objectives
- Architecture diagrams
- Detailed working
- Merits
- Design patterns
- Performance metrics
- Configuration
- Future enhancements

### Examples (`examples/`)

- `simple_etl.py` - Example of simple join and aggregation
- `complex_etl.py` - Example of multi-table join with filters
- `README.md` - Examples documentation

## 🔒 Security Notes

### Sanitized Information

All sensitive information has been removed or replaced with placeholders:

- ✅ Database credentials → `your_username`, `your_password`
- ✅ RDS endpoints → `your-rds-endpoint.region.rds.amazonaws.com`
- ✅ S3 bucket names → `your-bucket-name`
- ✅ API URLs → `http://your-flask-api-url`
- ✅ AWS account IDs → `YOUR_ACCOUNT_ID`

### Configuration Template

The `config.example.json` file provides a template with all required fields but no actual credentials.

## 📦 Dependencies

### Core Dependencies
- `boto3` - AWS SDK for Python
- `flask` - Web framework
- `psycopg2-binary` - PostgreSQL adapter
- `requests` - HTTP library

### AWS Services Required
- AWS Lambda
- AWS Bedrock (Claude Sonnet 4.5)
- AWS Glue
- AWS RDS (PostgreSQL)
- AWS S3
- AWS DynamoDB
- AWS Secrets Manager
- AWS CloudWatch

## 🚀 Quick Start

1. Clone the repository
2. Copy `config.example.json` to `config.json` and fill in your AWS details
3. Follow `SETUP.md` for detailed deployment instructions
4. Run examples from `examples/` directory

## 📚 Additional Resources

- [Full Documentation](docs/README.md)
- [Architecture Details](ARCHITECTURE.md)
- [Setup Guide](SETUP.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 📞 Support

- GitHub Issues: https://github.com/yourusername/datamorph/issues
- Email: support@datamorph.ai
- Discord: https://discord.gg/datamorph

---

**Note**: This repository contains sanitized code suitable for public GitHub hosting. All confidential information has been removed or replaced with placeholders.
