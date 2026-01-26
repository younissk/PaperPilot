# Troubleshooting CodePipeline Deployment

If your Lambda functions aren't showing up in the AWS dashboard after setting up CodePipeline, follow these steps:

## Step 1: Check CodePipeline Status

1. Go to **AWS Console > CodePipeline > Pipelines**
2. Click on your pipeline (e.g., `paperpilot-deploy`)
3. Check the status of each stage:
   - **Source** (green = success, red = failed)
   - **Build** (green = success, red = failed)

### If Source Stage Failed

- Check GitHub connection is active
- Verify repository and branch names are correct
- Check that the buildspec.yml file is in the root of your repo

### If Build Stage Failed

- Click on the **Build** stage to see details
- Click on the **CodeBuild** link to view build logs
- Common issues:
  - Missing permissions for CodeBuild service role
  - SAM CLI installation failed
  - Build errors in the SAM template

## Step 2: Check CodeBuild Logs

1. Go to **AWS Console > CodeBuild > Build projects**
2. Click on `paperpilot-build`
3. Click on **Build history** tab
4. Click on the most recent build
5. Check the **Build logs** for errors

### Common Build Errors

#### "No module named 'mangum'"

**Solution:** The dependencies aren't being installed. Check that `requirements.txt` files exist in `services/api/` and `services/worker/`.

#### "Unable to locate credentials"

**Solution:** CodeBuild service role needs permissions. See Step 3.

#### "Template format error"

**Solution:** Check the SAM template syntax. Run `sam validate` locally.

#### "Access Denied" errors

**Solution:** CodeBuild role needs IAM permissions. See Step 3.

## Step 3: Verify CodeBuild Service Role Permissions

The CodeBuild service role needs these permissions:

1. Go to **IAM Console > Roles**
2. Find your CodeBuild service role (e.g., `codebuild-paperpilot-build-service-role`)
3. Click **Add permissions > Attach policies**
4. Attach these managed policies:
   - `CloudFormationFullAccess`
   - `AWSLambda_FullAccess`
   - `AmazonAPIGatewayAdministrator`
   - `AmazonDynamoDBFullAccess`
   - `AmazonSQSFullAccess`
   - `AmazonS3FullAccess`
   - `IAMFullAccess` (or create a custom policy with least privilege)

5. Or create a custom policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "dynamodb:*",
        "sqs:*",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "logs:*",
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 4: Manually Trigger the Pipeline

If the pipeline hasn't run:

1. Go to **CodePipeline > Pipelines**
2. Click on your pipeline
3. Click **Release change** button (top right)
4. This will trigger a new pipeline execution

## Step 5: Check CloudFormation Stack

Even if the build succeeds, the CloudFormation stack might have failed:

1. Go to **CloudFormation Console**
2. Look for a stack named `paperpilot` (or `paperpilot-prod`)
3. Check the stack status:
   - **CREATE_COMPLETE** = Success ✅
   - **CREATE_FAILED** = Failed ❌
   - **CREATE_IN_PROGRESS** = Still deploying ⏳
   - **ROLLBACK_COMPLETE** = Failed and rolled back ❌

4. If failed, click on the stack and check:
   - **Events** tab for error messages
   - **Resources** tab to see which resources failed to create

### Common CloudFormation Errors

#### "Resource handler returned message: 'Invalid request provided'"

**Solution:** Check that the SQS queue ARN in `samconfig.toml` is correct and exists.

#### "The role defined for the function cannot be assumed by Lambda"

**Solution:** IAM role creation failed. Check CodeBuild has `iam:CreateRole` permission.

#### "Resource of type 'AWS::Serverless::HttpApi' with identifier 'ServerlessHttpApi' already exists"

**Solution:** Stack already exists. Delete it or use a different stack name.

## Step 6: Verify Functions Were Created

After successful deployment:

1. Go to **Lambda Console**
2. You should see:
   - `paperpilot-api-prod` (or `paperpilot-api-{environment}`)
   - `paperpilot-worker-prod` (or `paperpilot-worker-{environment}`)

3. Go to **DynamoDB Console**
4. You should see:
   - `paperpilot-jobs-prod` (or `paperpilot-jobs-{environment}`)

5. Go to **API Gateway Console**
6. You should see an HTTP API created by SAM

## Step 7: Test the Deployment

Once functions are created:

1. Get the API URL from CloudFormation outputs:

   ```bash
   aws cloudformation describe-stacks \
     --stack-name paperpilot \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
     --output text
   ```

2. Test the health endpoint:

   ```bash
   curl https://YOUR_API_ID.execute-api.eu-central-1.amazonaws.com/api/health
   ```

## Quick Fixes

### Fix 1: Update buildspec.yml to use config file explicitly

The buildspec should explicitly reference the samconfig.toml:

```yaml
post_build:
  commands:
    - cd infra
    - sam deploy --config-file samconfig.toml --config-env default
```

### Fix 2: Ensure Python 3.13 is available in CodeBuild

If CodeBuild doesn't support Python 3.13 yet, you may need to:

- Use a custom build image
- Or downgrade to Python 3.12 in `template.yaml` and `buildspec.yml`

### Fix 3: Check SQS Queue Exists

Verify your SQS queue exists:

```bash
aws sqs get-queue-url --queue-name paperpilot-jobs-prod --region eu-central-1
```

### Fix 4: Manual Deployment Test

Test deployment locally first:

```bash
cd infra
cp -r ../paperpilot ../services/api/
cp -r ../paperpilot ../services/worker/
sam build --use-container
sam deploy --guided
```

## Still Having Issues?

1. **Check AWS Service Health**: <https://status.aws.amazon.com/>
2. **Review SAM CLI logs**: Enable verbose logging in buildspec
3. **Check region**: Ensure all resources are in the same region (eu-central-1)
4. **Contact AWS Support**: If permissions and configuration are correct but deployment still fails
