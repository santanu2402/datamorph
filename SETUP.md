# DataMorph Setup Guide

This guide will walk you through setting up DataMorph in your AWS environment.

## Prerequisites

- AWS Account with administrator access
- AWS CLI installed and configured
- Python 3.11 or higher
- PostgreSQL database (RDS recommended)
- AWS Bedrock access (Claude Sonnet 4.5)

## Step 1: AWS Configuration

### 1.1 Enable AWS Bedrock

1. Go to AWS Bedrock console
2. Request access to Claude Sonnet 4.5 model
3. Wait for approval (usually instant)

### 1.2 Create S3 Bucket

```bash
aws s3 mb s3://your-datamorph-bucket --region us-east-1
```

### 1.3 Create DynamoDB Table

```bash
aws dynamodb create-table \
    --table-name datamorph_logs \
    --attribute-definitions AttributeName=run_id,AttributeType=S \
    --key-schema AttributeName=run_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### 1.4 Create RDS PostgreSQL Instance

```bash
aws rds create-db-instance \
    --db-instance-identifier datamorph-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --region us-east-1
```

## Step 2: Configuration

### 2.1 Copy Configuration Template

```bash
cp config.example.json config.json
```

### 2.2 Edit Configuration

Edit `config.json` with your AWS resource details:

```json
{
  "RDS_ENDPOINT": "your-rds-endpoint.region.rds.amazonaws.com",
  "RDS_USERNAME": "admin",
  "RDS_PASSWORD": "YourSecurePassword123!",
  "S3_BUCKET": "your-datamorph-bucket",
  ...
}
```

### 2.3 Store Configuration in Secrets Manager

```bash
aws secretsmanager create-secret \
    --name datamorph/config \
    --secret-string file://config.json \
    --region us-east-1
```

## Step 3: Deploy Lambda Functions

### 3.1 Create IAM Role for Lambda

```bash
aws iam create-role \
    --role-name DataMorphLambdaRole \
    --assume-role-policy-document file://iam/lambda-trust-policy.json

aws iam attach-role-policy \
    --role-name DataMorphLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name DataMorphLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

aws iam attach-role-policy \
    --role-name DataMorphLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
    --role-name DataMorphLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### 3.2 Package and Deploy Lambda Functions

```bash
# Install dependencies
pip install -r requirements.txt -t package/

# Package each Lambda
cd package
zip -r ../orchestrator.zip .
cd ..
cd src/lambdas/orchestrator
zip -g ../../../orchestrator.zip handler.py
cd ../../..

# Deploy
aws lambda create-function \
    --function-name datamorph-orchestrator \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/DataMorphLambdaRole \
    --handler handler.lambda_handler \
    --zip-file fileb://orchestrator.zip \
    --timeout 900 \
    --memory-size 512 \
    --region us-east-1
```

Repeat for all 6 Lambda functions:
- datamorph-orchestrator
- datamorph-specs-generator
- datamorph-glue-executor
- datamorph-validator
- datamorph-remediator
- datamorph-logger

## Step 4: Deploy Flask API

### 4.1 Launch EC2 Instance

```bash
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.small \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --user-data file://ec2-user-data.sh \
    --region us-east-1
```

### 4.2 Install Flask App

SSH into the EC2 instance and run:

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip postgresql-client

# Clone repository
git clone https://github.com/yourusername/datamorph.git
cd datamorph

# Install Python dependencies
pip3 install -r requirements.txt

# Install and configure Gunicorn
pip3 install gunicorn

# Create systemd service
sudo cp deployment/datamorph-flask.service /etc/systemd/system/
sudo systemctl enable datamorph-flask
sudo systemctl start datamorph-flask
```

## Step 5: Create Glue Connection

### 5.1 Create Glue Connection to RDS

```bash
aws glue create-connection \
    --connection-input '{
        "Name": "dmdb-connection",
        "ConnectionType": "JDBC",
        "ConnectionProperties": {
            "JDBC_CONNECTION_URL": "jdbc:postgresql://your-rds-endpoint:5432/your_database",
            "USERNAME": "admin",
            "PASSWORD": "YourSecurePassword123!"
        },
        "PhysicalConnectionRequirements": {
            "SubnetId": "subnet-xxxxxxxxx",
            "SecurityGroupIdList": ["sg-xxxxxxxxx"],
            "AvailabilityZone": "us-east-1a"
        }
    }' \
    --region us-east-1
```

## Step 6: Test the Setup

### 6.1 Run Health Check

```bash
curl http://your-ec2-ip:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "DataMorph Flask API"
}
```

### 6.2 Run Sample ETL

```bash
python examples/simple_etl.py
```

## Step 7: Monitoring Setup

### 7.1 Configure CloudWatch Logs

```bash
# Install CloudWatch agent on EC2
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file://cloudwatch-config.json
```

### 7.2 Create CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard \
    --dashboard-name DataMorph \
    --dashboard-body file://cloudwatch-dashboard.json \
    --region us-east-1
```

## Troubleshooting

### Lambda Timeout Issues

If Lambda functions timeout, increase the timeout:

```bash
aws lambda update-function-configuration \
    --function-name datamorph-orchestrator \
    --timeout 900 \
    --region us-east-1
```

### Bedrock Access Issues

Ensure you have requested access to Claude Sonnet 4.5 in the Bedrock console.

### RDS Connection Issues

Check security group rules allow connections from Lambda and EC2.

## Next Steps

- Read the [Documentation](docs/README.md)
- Try the [Examples](examples/)
- Join our [Community](https://discord.gg/datamorph)

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/datamorph/issues
- Email: support@datamorph.ai
- Discord: https://discord.gg/datamorph
