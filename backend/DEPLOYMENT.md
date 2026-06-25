# Deployment Guide - Crop Disease Detection Backend

## 🚀 Quick Start (Development)

### Local Development Setup

1. **Install Python 3.10+**
   ```bash
   python --version  # Should be 3.10 or higher
   ```

2. **Install MongoDB**
   - Windows: https://www.mongodb.com/try/download/community
   - Mac: `brew install mongodb-community`
   - Linux: Follow official MongoDB documentation

3. **Setup Project**
   ```bash
   cd backend
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Update .env file with your settings
   # IMPORTANT: Change SECRET_KEY
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. **Start MongoDB**
   ```bash
   mongod --dbpath ./data/db
   ```

6. **Run Application**
   ```bash
   # Development with auto-reload
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or
   python app/main.py
   ```

7. **Access API**
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Manual Docker Build

```bash
# Build image
docker build -t crop-disease-backend:latest .

# Run container
docker run -d \
  --name crop-disease-backend \
  -p 8000:8000 \
  -e MONGODB_URL="mongodb://localhost:27017" \
  -e SECRET_KEY="your-secret-key" \
  crop-disease-backend:latest
```

---

## ☁️ Cloud Deployment

### AWS EC2

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t3.medium or larger
   - Open ports: 22 (SSH), 8000 (API)

2. **Connect and Setup**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd crop_disease_detection/backend
   
   # Create production .env
   cp .env .env.production
   # Edit .env.production with production values
   
   # Start services
   docker-compose up -d
   ```

4. **Setup Nginx Reverse Proxy**
   ```bash
   sudo apt install nginx -y
   
   # Create Nginx config
   sudo nano /etc/nginx/sites-available/crop-disease-api
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/crop-disease-api /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d api.yourdomain.com
   ```

### Google Cloud Platform (GCP)

1. **Create Compute Engine Instance**
   ```bash
   gcloud compute instances create crop-disease-backend \
     --machine-type=e2-medium \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --boot-disk-size=50GB
   ```

2. **Connect and Deploy**
   ```bash
   gcloud compute ssh crop-disease-backend
   # Follow same steps as EC2
   ```

### Azure

1. **Create Virtual Machine**
   ```bash
   az vm create \
     --resource-group crop-disease-rg \
     --name crop-disease-backend \
     --image UbuntuLTS \
     --size Standard_B2s \
     --admin-username azureuser
   ```

2. **Deploy Application**
   ```bash
   ssh azureuser@your-azure-vm-ip
   # Follow same steps as EC2
   ```

---

## 🗄️ Database Setup

### MongoDB Atlas (Cloud)

1. **Create Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Create free cluster

2. **Configure Cluster**
   - Create database: `crop_disease_db`
   - Add database user
   - Whitelist IP: `0.0.0.0/0` (or specific IPs)

3. **Get Connection String**
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/crop_disease_db?retryWrites=true&w=majority
   ```

4. **Update .env**
   ```bash
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/crop_disease_db
   ```

### Local MongoDB with Authentication

```bash
# Start MongoDB with auth
mongod --auth --dbpath ./data/db

# Create admin user
mongo
> use admin
> db.createUser({
    user: "admin",
    pwd: "securepassword",
    roles: ["root"]
})

# Create app database and user
> use crop_disease_db
> db.createUser({
    user: "crop_app",
    pwd: "apppassword",
    roles: ["readWrite"]
})

# Update connection string
MONGODB_URL=mongodb://crop_app:apppassword@localhost:27017/crop_disease_db?authSource=crop_disease_db
```

---

## 🔒 Security Checklist

### Production Security

- [ ] Change SECRET_KEY to strong random value
- [ ] Set DEBUG=False
- [ ] Use HTTPS/SSL (Let's Encrypt)
- [ ] Configure CORS properly (specific origins)
- [ ] Enable MongoDB authentication
- [ ] Use environment-specific .env files
- [ ] Never commit .env to git
- [ ] Setup firewall rules
- [ ] Regular security updates
- [ ] Use secrets manager (AWS Secrets Manager, etc.)
- [ ] Enable rate limiting
- [ ] Setup monitoring and alerts

### Environment Variables Security

```bash
# Use secrets manager in production
# AWS
aws secretsmanager create-secret --name crop-disease-env --secret-string file://.env.production

# Retrieve in production
aws secretsmanager get-secret-value --secret-id crop-disease-env --query SecretString --output text > .env
```

---

## 📊 Monitoring & Logging

### Application Logs

```bash
# Docker logs
docker-compose logs -f backend

# Local logs
tail -f logs/app.log
```

### Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "app_name": "Crop Disease Detection API",
  "version": "1.0.0",
  "database": "connected"
}
```

### Setup Monitoring (Optional)

**Prometheus + Grafana**
```bash
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  
grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Backend

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest
    
    - name: Deploy to server
      env:
        SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        SERVER_IP: ${{ secrets.SERVER_IP }}
      run: |
        # SSH and deploy
        ssh-keyscan -H $SERVER_IP >> ~/.ssh/known_hosts
        ssh user@$SERVER_IP 'cd /app && git pull && docker-compose up -d --build'
```

---

## 📈 Performance Optimization

### Production Settings

```python
# Increase workers based on CPU cores
# Formula: (2 x CPU cores) + 1
workers = 4

# Adjust timeouts
timeout = 120

# Enable keepalive
keepalive = 5
```

### Database Optimization

```python
# Increase connection pool
MONGODB_MIN_POOL_SIZE=20
MONGODB_MAX_POOL_SIZE=200

# Enable caching
REDIS_URL=redis://localhost:6379/0
```

### Image Optimization

```python
# Compress images before saving
MAX_UPLOAD_SIZE=5242880  # 5MB
```

---

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check MongoDB is running
sudo systemctl status mongod

# Check connection string
mongo "mongodb://localhost:27017"
```

**Port Already in Use**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
kill -9 <PID>
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Docker Issues**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📞 Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Health endpoint: `/health`
- Documentation: `/docs`

---

**Happy Deploying! 🚀**
