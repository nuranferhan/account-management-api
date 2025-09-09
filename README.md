# Account Management API

![CI Build and Test](https://github.com/nuranferhan/account-management-api/workflows/CI%20Build%20and%20Test/badge.svg)

A RESTful API for managing user accounts built with Flask and SQLAlchemy.

## Features

- Create read update and delete user accounts
- RESTful API design
- SQLAlchemy ORM with SQLite database
- Comprehensive test coverage
- CI/CD pipeline with GitHub Actions
- Docker containerization
- Kubernetes deployment ready

## Tech Stack

- **Backend**: Flask SQLAlchemy
- **Database**: SQLite
- **Testing**: pytest pytest-cov
- **CI/CD**: GitHub Actions
- **Containerization**: Docker
- **Orchestration**: Kubernetes

## Project Structure

```

account-management-api/
├── app.py              # Main application file
├── tests/              # Test files
├── k8s/                # Kubernetes manifests
├── tekton/             # Tekton pipeline files
├── Dockerfile          # Docker configuration
└── requirements.txt    # Python dependencies

````

## Testing

Run tests with coverage:

```bash
pytest --cov=. --cov-report=term-missing tests/ -v
```

## Docker

Build and run with Docker:

```bash
docker build -t account-management-api .
docker run -p 5000:5000 account-management-api
```

## Kubernetes Deployment

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

### Health Check

* `GET /api/v1/health` Health check endpoint

### Accounts

* `POST /api/v1/accounts` Create new account
* `GET /api/v1/accounts` List all accounts
* `GET /api/v1/accounts/{id}` Get account by ID
* `PUT /api/v1/accounts/{id}` Update account
* `DELETE /api/v1/accounts/{id}` Delete account

### Example API Usage

Create an account:

```bash
curl -X POST http://localhost:5000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "phone": "123-456-7890"}'
```

Get all accounts:

```bash
curl http://localhost:5000/api/v1/accounts
```

## Security

* Input validation
* SQL injection protection via SQLAlchemy ORM
* CORS enabled for cross-origin requests
* Security scanning with Bandit

## CI/CD Pipeline

The project uses GitHub Actions for:

* ✅ Automated testing
* ✅ Code linting (flake8)
* ✅ Security scanning (bandit)
* ✅ Coverage reporting
* ✅ Docker image building
* ✅ Container testing

## License

This project is licensed under the MIT License.

