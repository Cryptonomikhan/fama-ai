# Fama AI Deployment Guide

This guide provides instructions for deploying the Fama AI financial modeling API in a production environment using Docker and Docker Compose.

## System Requirements

- **Docker**: Version 20.10.0 or higher
- **Docker Compose**: Version 2.0.0 or higher
- **Storage**: At least 10GB of free disk space
- **Memory**: Minimum 4GB RAM recommended
- **CPU**: 2+ cores recommended

## Deployment Options

### 1. Docker Compose Deployment (Recommended)

This approach deploys the API in a container. The PostgreSQL database is optional and only starts when specifically requested.

#### Prerequisites

1. Install Docker and Docker Compose
2. Clone the repository

#### Setup

1. Start the API service only (recommended for production):

```bash
docker compose up -d
```

This starts only the API service. The PostgreSQL database is not started since all database configuration comes from API callers in their requests.

2. To start both the API and PostgreSQL (useful for development/testing):

```bash
docker compose --profile dev up -d
```

The `--profile dev` flag tells Docker Compose to also start services marked with the `dev` profile, which includes the PostgreSQL container.

3. Verify the deployment:

```bash
docker compose ps
curl http://localhost:8000/health
```

### 2. API-Only Deployment

If you prefer to use an existing PostgreSQL database, you can deploy just the API container.

#### Setup

1. Create the API container:

```bash
docker build -t fama-api .
docker run -d --name fama-api \
  -p 8000:8000 \
  --env-file .env.production \
  -v ./logs:/app/logs \
  -v ./uploads:/app/uploads \
  fama-api
```

Note: You'll need to provide all necessary environment variables in `.env.production`, including the external database connection details.

## Configuration

### Environment Variables

Key environment variables to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `FAMA_API_KEY` | API authentication key | (required) |
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (optional) |
| `FAMA_DEFAULT_PROVIDER` | Default model provider | openai |
| `FAMA_DEFAULT_MODEL_ID` | Default model ID | gpt-4o |
| `POSTGRES_*` | Database configuration | (required) |
| `FAMA_LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | INFO |
| `FAMA_RATE_LIMIT_PER_MINUTE` | API rate limit | 60 |

See `.env.production` for a complete list of configuration options.

### Volumes

The Docker Compose setup uses the following volumes:

- `postgres-data`: Persistent storage for the PostgreSQL database
- `./logs:/app/logs`: API log files
- `./uploads:/app/uploads`: Temporary file uploads

## Scaling

### Horizontal Scaling

For higher throughput, you can run multiple API instances:

```bash
docker compose --env-file .env.production up -d --scale api=3
```

Note: You'll need a load balancer in front of the API instances.

### Vertical Scaling

Adjust the resource limits in `docker-compose.yml`:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'  # Increase CPU limit
        memory: 4G   # Increase memory limit
```

## Security Considerations

1. **API Authentication**: Always set a strong `FAMA_API_KEY`
2. **Database Security**: Use strong passwords for PostgreSQL
3. **Network Security**: Consider running behind a reverse proxy with SSL
4. **Resource Limits**: Set appropriate container resource limits
5. **Updates**: Regularly update the Docker images for security patches

## Monitoring

1. **Container Health**: Use Docker's health checks
2. **API Logs**: Check `/app/logs` for application logs
3. **Metrics**: Consider setting up Prometheus/Grafana for monitoring

## Backup & Recovery

### Database Backup

```bash
docker exec fama-postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql
```

### Database Restore

```bash
cat backup.sql | docker exec -i fama-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
```

## Troubleshooting

### Common Issues

1. **Connection Issues**:
   - Check if the containers are running: `docker compose ps`
   - Verify network connectivity: `docker network inspect fama-network`

2. **Database Issues**:
   - Check PostgreSQL logs: `docker logs fama-postgres`
   - Verify connection parameters in `.env.production`

3. **API Issues**:
   - Check API logs: `docker logs fama-api`
   - Verify API is healthy: `curl http://localhost:8000/health`

## Maintenance

### Updates

To update to a new version:

```bash
git pull
docker compose --env-file .env.production down
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d
```

## Advanced Configuration

### Custom Model Providers

To add custom model providers, mount a configuration file:

```yaml
volumes:
  - ./custom_providers.json:/app/config/custom_providers.json
```

### SSL Termination

For production, we recommend using a reverse proxy like Nginx or Traefik for SSL termination.

Example Nginx configuration:

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Understanding Containerization

### Container Structure

The containerized API follows these principles:

1. **API-Only Focus**: The container runs only the FastAPI server that processes requests
2. **Stateless Design**: No state is maintained in the container between requests
3. **Caller-Provided Configuration**: API callers provide all configuration in their requests:
   - Model provider API keys
   - Storage connection strings
   - Knowledge base settings
   - MCP server configurations
   - Memory preferences

### PostgreSQL Container (Optional)

The included PostgreSQL container with pgvector extension:

1. **Not required**: The API does not depend on this database
2. **Only starts with explicit flag**: Using `--profile dev` 
3. **Development use case**: Useful for testing storage connections locally
4. **Independent operation**: Each caller still provides their own database configuration in requests
5. **Not connected by default**: The API has no hardcoded connection to this database

For example, even with the PostgreSQL container running, clients still need to provide complete storage connection information in their API requests:

```json
{
  "task": "Analyze this financial data...",
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "provider_api_key": "sk-...",
  "storage_type": "postgres",
  "storage_connection": "postgresql://username:password@hostname:port/database"
}
``` 