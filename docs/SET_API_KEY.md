# Setting OpenAI API Key After Deployment

After your Lambda functions are deployed, you need to set the `OPENAI_API_KEY` environment variable.

## Option 1: Set via AWS Console (Easiest)

1. Go to **AWS Console > Lambda > Functions**
2. Click on `paperpilot-api-prod`
3. Go to **Configuration > Environment variables**
4. Click **Edit**
5. Click **Add environment variable**
6. Set:
   - **Key:** `OPENAI_API_KEY`
   - **Value:** Your OpenAI API key (starts with `sk-`)
7. Click **Save**
8. Repeat for `paperpilot-worker-prod`

## Option 2: Set via AWS CLI

```bash
# Set for API function
aws lambda update-function-configuration \
  --function-name paperpilot-api-prod \
  --environment "Variables={OPENAI_API_KEY=sk-your-key-here,LOG_LEVEL=INFO,JOBS_TABLE_NAME=paperpilot-jobs-prod,SQS_QUEUE_URL=https://sqs.eu-central-1.amazonaws.com/120569648365/paperpilot-jobs-prod,ENVIRONMENT=prod}" \
  --region eu-central-1

# Set for Worker function
aws lambda update-function-configuration \
  --function-name paperpilot-worker-prod \
  --environment "Variables={OPENAI_API_KEY=sk-your-key-here,LOG_LEVEL=INFO,JOBS_TABLE_NAME=paperpilot-jobs-prod,SQS_QUEUE_URL=https://sqs.eu-central-1.amazonaws.com/120569648365/paperpilot-jobs-prod,ENVIRONMENT=prod}" \
  --region eu-central-1
```

## Option 3: Use AWS Secrets Manager (Recommended for Production)

1. **Create the secret:**
   ```bash
   aws secretsmanager create-secret \
     --name paperpilot/openai-api-key \
     --secret-string "sk-your-key-here" \
     --region eu-central-1
   ```

2. **Update the SAM template** to reference the secret:
   ```yaml
   Environment:
     Variables:
       LOG_LEVEL: INFO
   Secrets:
     OPENAI_API_KEY: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:paperpilot/openai-api-key"
   ```

3. **Add IAM permission** to the Lambda functions to read the secret:
   ```yaml
   Policies:
     - SecretsManagerReadWrite:
         SecretArn: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:paperpilot/openai-api-key"
   ```

4. **Redeploy** the stack

## Option 4: Use SSM Parameter Store (Already Set Up)

If you already created the SSM parameter:

1. **Add IAM permission** to Lambda functions to read SSM:
   ```yaml
   Policies:
     - Statement:
         - Effect: Allow
           Action:
             - ssm:GetParameter
             - ssm:GetParameters
           Resource: !Sub "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/paperpilot/*"
   ```

2. **Update your Lambda code** to fetch from SSM at runtime:
   ```python
   import boto3
   ssm = boto3.client('ssm')
   openai_key = ssm.get_parameter(
       Name='/paperpilot/openai-api-key',
       WithDecryption=True
   )['Parameter']['Value']
   ```

## Verify It's Set

After setting the key, test the API:

```bash
# Get API URL from CloudFormation outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name paperpilot \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text \
  --region eu-central-1)

# Test health endpoint
curl $API_URL/api/health
```

## Security Best Practices

1. **Never commit API keys** to git
2. **Use Secrets Manager** for production (encrypted at rest)
3. **Rotate keys regularly**
4. **Use least-privilege IAM policies** (only allow reading the specific secret)
5. **Enable CloudTrail** to audit secret access
