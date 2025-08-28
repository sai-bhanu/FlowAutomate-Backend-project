# FlowAutomate-Backend-project

How will I use AWS / cloud services you would use for deployment

AWS deployment (brief)

Compute:
ECS Fargate (API container) behind an ALB (or Lambda + API Gateway if you want serverless).

Search: Amazon OpenSearch Service (managed OpenSearch).

Cache / rate limiting: Amazon ElastiCache for Redis.

Storage: Parser outputs in S3; trigger ETL via S3 Event → SQS → ECS task/Lambda.

Config/Secrets: AWS Secrets Manager/SSM Parameter Store for credentials and API keys.

Networking: Private VPC subnets for API → OpenSearch/Redis; security groups limiting access.

Observability: CloudWatch Logs, CloudWatch Metrics, optional X-Ray tracing.

CI/CD: Push image to ECR, deploy with GitHub Actions or CodePipeline.
