""" Deployment Guide for EtherScope

This guide covers deployment strategies for EtherScope in different environments.
"""

# # Deployment Guide for EtherScope

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/etherscope.git
cd etherscope

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### Running

```bash
python run.py
```

### Testing

```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t etherscope:latest .
```

### Run Container

```bash
docker run -d \
  --env-file .env \
  --name etherscope \
  --restart unless-stopped \
  etherscope:latest
```

### Using Docker Compose

```bash
docker-compose up -d
```

### View Logs

```bash
docker logs -f etherscope
```

### Stop and Remove

```bash
docker-compose down
```

## Production Deployment

### One-click Deployment Options

#### Railway.app

1. Connect your GitHub repository
2. Add environment variables via Railway dashboard
3. Deploy!

#### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create etherscope

# Add environment variables
heroku config:set \
  TELEGRAM_BOT_TOKEN=your_token \
  ETHERSCAN_API_KEY=your_key \
  ENVIRONMENT=production

# Deploy via Git
git push heroku main
```

#### DigitalOcean App Platform

1. Connect GitHub repository
2. Specify `run.py` as start command
3. Set environment variables
4. Deploy

#### AWS (with Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 etherscope

# Create environment
eb create etherscope-prod -e --instance-role-arn arn:aws:iam::YOUR_ACCOUNT:role/ROLE_NAME

# Set environment variables
eb setenv \
  TELEGRAM_BOT_TOKEN=your_token \
  ETHERSCAN_API_KEY=your_key

# Deploy
eb deploy
```

### Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etherscope
spec:
  replicas: 2
  selector:
    matchLabels:
      app: etherscope
  template:
    metadata:
      labels:
        app: etherscope
    spec:
      containers:
      - name: etherscope
        image: etherscope:latest
        env:
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: etherscope-secrets
              key: token
        - name: ETHERSCAN_API_KEY
          valueFrom:
            secretKeyRef:
              name: etherscope-secrets
              key: api-key
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

Deploy:

```bash
kubectl create secret generic etherscope-secrets \
  --from-literal=token=YOUR_TOKEN \
  --from-literal=api-key=YOUR_KEY

kubectl apply -f k8s-deployment.yaml
```

## Monitoring

### Log Aggregation

With ELK Stack:

```bash
docker run -d --name elasticsearch docker.elastic.co/elasticsearch/elasticsearch:8.0.0
docker run -d --name kibana docker.elastic.co/kibana/kibana:8.0.0
```

Configure bot to send logs to Elasticsearch.

### Alerts

Set up monitoring for:
- Bot uptime
- API error rates
- Cache hit ratios
- Response times

Example Prometheus metrics could be added:

```python
from prometheus_client import Counter, Histogram

requests_total = Counter('etherscope_requests_total', 'Total requests')
request_duration = Histogram('etherscope_request_duration_seconds', 'Request duration')
```

### Health Checks

Bot exposes `/health` endpoint:

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Bot Not Starting

Check logs:
```bash
docker logs etherscope
```

Verify environment variables:
```bash
docker exec etherscope env
```

### High Memory Usage

Reduce cache size in `.env`:
```env
# Reduce from 1000 to 100
CACHE_MAX_SIZE=100
```

Or clear cache periodically:

```python
cache_service.cleanup_expired()
```

### API Rate Limiting

Increase retry delays or:
- Upgrade to Alchemy API with higher limits
- Implement request batching
- Cache results longer (increase `CACHE_TTL_SECONDS`)

### Bot Timeouts

Increase API timeout:
```env
API_TIMEOUT=60  # seconds
```

## Performance Optimization

### Caching Strategy

- Enable caching in production
- Set appropriate TTL (300-600 seconds)
- Monitor cache hit rates

### Database (Optional Future Enhancement)

For persistent storage:

```python
# Add SQLAlchemy models
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/etherscope')
```

### Load Balancing

For multiple bot instances:

```docker-compose
version: '3'
services:
  bot1:
    image: etherscope
    container_name: etherscope-1
  bot2:
    image: etherscope
    container_name: etherscope-2
  nginx:
    image: nginx
    ports:
      - "8000:8000"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## Cost Optimization

- Use Etherscan free tier for development
- Upgrade to Alchemy only if limits exceeded
- Cache aggressively to reduce API calls
- Monitor API usage in provider dashboards

---

**For questions or issues, check the main README.md**
