# Quick Diagnostic Checklist

Follow these steps in order to diagnose why your functions aren't showing up:

## ✅ Step 1: Did the Pipeline Run?

**Check:** AWS Console > CodePipeline > Your Pipeline

- [ ] Pipeline exists and shows stages (Source, Build)
- [ ] Pipeline status is **In Progress** or **Succeeded**
- [ ] If **Failed**, note which stage failed (Source or Build)

**If pipeline hasn't run:**

- Click **Release change** button to trigger it manually

---

## ✅ Step 2: Check Build Logs

**Check:** AWS Console > CodeBuild > Build Projects > paperpilot-build > Build History

- [ ] Latest build shows **Succeeded** (green)
- [ ] If **Failed** (red), click on it and check **Build logs**

**Common errors in logs:**

- `No module named 'mangum'` → Dependencies not installed
- `Access Denied` → CodeBuild role missing permissions
- `Unable to locate credentials` → IAM role issue
- `Template format error` → SAM template syntax error

---

## ✅ Step 3: Check CloudFormation Stack

**Check:** AWS Console > CloudFormation > Stacks

- [ ] Stack named `paperpilot` exists
- [ ] Stack status:
  - ✅ **CREATE_COMPLETE** = Success! Functions should exist
  - ❌ **CREATE_FAILED** = Check Events tab for errors
  - ⏳ **CREATE_IN_PROGRESS** = Wait a few minutes
  - ❌ **ROLLBACK_COMPLETE** = Deployment failed, check Events

**If stack doesn't exist:**

- Build succeeded but deploy didn't run
- Check CodeBuild logs for `sam deploy` errors

---

## ✅ Step 4: Verify CodeBuild Permissions

**Check:** IAM Console > Roles > [Your CodeBuild Service Role]

The role needs these permissions:

- [ ] `CloudFormationFullAccess` (or equivalent)
- [ ] `AWSLambda_FullAccess` (or equivalent)
- [ ] `IAMFullAccess` (or ability to create roles)
- [ ] `AmazonS3FullAccess` (for SAM artifacts)
- [ ] `AmazonDynamoDBFullAccess`
- [ ] `AmazonSQSFullAccess`
- [ ] `AmazonAPIGatewayAdministrator`

**Quick fix:** Attach `AdministratorAccess` temporarily to test, then create a least-privilege policy.

---

## ✅ Step 5: Check Lambda Functions

**Check:** AWS Console > Lambda > Functions

- [ ] `paperpilot-api-prod` exists
- [ ] `paperpilot-worker-prod` exists

**If functions don't exist:**

- CloudFormation stack likely failed
- Go back to Step 3 and check stack Events

---

## ✅ Step 6: Check DynamoDB Table

**Check:** AWS Console > DynamoDB > Tables

- [ ] `paperpilot-jobs-prod` table exists

**If table doesn't exist:**

- CloudFormation stack likely failed
- Go back to Step 3

---

## 🚨 Most Common Issues

### Issue 1: CodeBuild Role Missing Permissions

**Symptom:** Build fails with "Access Denied" errors  
**Fix:** Add IAM permissions to CodeBuild service role (Step 4)

### Issue 2: SQS Queue Doesn't Exist

**Symptom:** CloudFormation fails with "Queue not found"  
**Fix:** Verify queue ARN in `infra/samconfig.toml` matches your actual queue

### Issue 3: Python 3.13 Not Available

**Symptom:** Build fails with "Runtime python3.13 not found"  
**Fix:** Change runtime to `python3.12` in `infra/template.yaml` and `buildspec.yml`

### Issue 4: SAM Deploy Not Running

**Symptom:** Build succeeds but no CloudFormation stack  
**Fix:** Check that `sam deploy` command in buildspec.yml is correct

---

## 📞 Next Steps

1. **If pipeline hasn't run:** Click "Release change" in CodePipeline
2. **If build failed:** Check CodeBuild logs and fix the error
3. **If stack failed:** Check CloudFormation Events tab for specific error
4. **If everything succeeded but no functions:** Check the region (should be eu-central-1)

For detailed troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
