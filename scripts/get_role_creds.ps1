# PowerShell script to assume IAM role and update .env
$ROLE_ARN = "arn:aws:iam::413426654981:role/RoleSwitch-DevmetadataExternaluser"
$SESSION_NAME = "MaranSession"
$MFA_SERIAL = "arn:aws:iam::276824211313:mfa/samsung"

$envPath = ".env"
$baseAccessKey = ""
$baseSecretKey = ""

# 1. Load PERMANENT credentials from .env
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^BASE_AWS_ACCESS_KEY_ID=(.+)") { $baseAccessKey = $matches[1].Trim() }
        if ($_ -match "^BASE_AWS_SECRET_ACCESS_KEY=(.+)") { $baseSecretKey = $matches[1].Trim() }
    }
}

if (-not $baseAccessKey -or -not $baseSecretKey) {
    Write-Host "[WARNING] BASE_AWS_ACCESS_KEY_ID or BASE_AWS_SECRET_ACCESS_KEY not found in .env" -ForegroundColor Red
    Write-Host "Please ensure your Permanent keys (AKIA...) are saved with 'BASE_' prefix in .env" -ForegroundColor Yellow
    exit
}

Write-Host "[KEY] Using Permanent Keys for authentication: $baseAccessKey" -ForegroundColor Gray

# 2. Get MFA token
$mfaToken = Read-Host "Enter MFA Token (leave blank if not required)"

# 3. Run AWS command
try {
    # Set temporary environment variables for the AWS CLI call
    $env:AWS_ACCESS_KEY_ID = $baseAccessKey
    $env:AWS_SECRET_ACCESS_KEY = $baseSecretKey
    $env:AWS_SESSION_TOKEN = ""

    if ($mfaToken) {
        $result = aws sts assume-role --role-arn $ROLE_ARN --role-session-name $SESSION_NAME --serial-number $MFA_SERIAL --token-code $mfaToken | ConvertFrom-Json
    }
    else {
        $result = aws sts assume-role --role-arn $ROLE_ARN --role-session-name $SESSION_NAME | ConvertFrom-Json
    }
    
    # CLEAR THEM IMMEDIATELY
    $env:AWS_ACCESS_KEY_ID = ""
    $env:AWS_SECRET_ACCESS_KEY = ""
}
catch {
    Write-Host "[ERROR] Unable to assume role. Check your MFA token or if BASE keys are still valid." -ForegroundColor Red
    exit
}

if ($result.Credentials) {
    $tempAccessKey = $result.Credentials.AccessKeyId
    $tempSecretKey = $result.Credentials.SecretAccessKey
    $tempSessionToken = $result.Credentials.SessionToken

    Write-Host "[SUCCESS] Successfully obtained temporary credentials!" -ForegroundColor Green

    # 4. Update .env file (Only update the ones the app uses, leave BASE_ keys alone)
    $content = Get-Content $envPath
    $newContent = @()
    
    foreach ($line in $content) {
        if ($line -match "^AWS_ACCESS_KEY_ID=") { $newContent += "AWS_ACCESS_KEY_ID=$tempAccessKey" }
        elseif ($line -match "^AWS_SECRET_ACCESS_KEY=") { $newContent += "AWS_SECRET_ACCESS_KEY=$tempSecretKey" }
        elseif ($line -match "^AWS_SESSION_TOKEN=") { $newContent += "AWS_SESSION_TOKEN=$tempSessionToken" }
        else { $newContent += $line }
    }

    $newContent | Set-Content $envPath
    Write-Host "Success: .env file updated with Temporary Session! You can now run the app/tests." -ForegroundColor Yellow
}
