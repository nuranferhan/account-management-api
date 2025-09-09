# Account Management API

A REST API for managing user accounts built with Flask, featuring CI/CD pipelines and Kubernetes deployment.

## Features

- **REST API Endpoints**: CRUD operations for account management
- **Database Integration**: SQLAlchemy with SQLite
- **Testing**: Comprehensive test suite with pytest
- **CI/CD**: GitHub Actions for automated testing and building
- **Security**: Code scanning with bandit and flake8 linting
- **Containerization**: Docker support with health checks
- **Orchestration**: Kubernetes deployment manifests
- **Pipeline**: Tekton CI/CD pipeline configuration

## API Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/accounts/{id}` - Get account by ID
- `GET /api/v1/accounts` - List all accounts
- `PUT /api/v1/accounts/{id}` - Update account
- `DELETE /api/v1/accounts/{id}` - Delete account

## Quick Start

### Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. API will be available at `http://localhost:5000`

### Testing

```bash
pytest --cov=app tests/