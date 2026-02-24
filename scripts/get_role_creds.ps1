# PowerShell script to assume IAM role and update .env
$ROLE_ARN = "arn:aws:iam::413426654981:role/RoleSwitch-DevmetadataExternaluser"
$SESSION_NAME = "MaranSession"
$MFA_SERIAL = "arn:aws:iam::276824211313:mfa/samsung" # Update this if different

# 1. Load existing credentials from .env to sign the request
$envPath = ".env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^AWS_ACCESS_KEY_ID=(.+)") { $env:AWS_ACCESS_KEY_ID = $matches[1].Trim() }
        if ($_ -match "^AWS_SECRET_ACCESS_KEY=(.+)") { $env:AWS_SECRET_ACCESS_KEY = $matches[1].Trim() }
    }
}

Write-Host "Assuming role $ROLE_ARN..." -ForegroundColor Cyan

# 2. Get MFA token if needed
$mfaToken = Read-Host "Enter MFA Token (leave blank if not required)"

# 3. Run AWS command
try {
    if ($mfaToken) {
        $result = aws sts assume-role --role-arn $ROLE_ARN --role-session-name $SESSION_NAME --serial-number $MFA_SERIAL --token-code $mfaToken | ConvertFrom-Json
    }
    else {
        $result = aws sts assume-role --role-arn $ROLE_ARN --role-session-name $SESSION_NAME | ConvertFrom-Json
    }
}
catch {
    Write-Host "Error: Unable to assume role. Check your base credentials in .env or MFA token." -ForegroundColor Red
    exit
}

if ($result.Credentials) {
    $AccessKeyId = $result.Credentials.AccessKeyId
    $SecretAccessKey = $result.Credentials.SecretAccessKey
    $SessionToken = $result.Credentials.SessionToken

    Write-Host "Successfully obtained temporary credentials!" -ForegroundColor Green

    # Read .env file
    $envPath = ".env"
    if (Test-Path $envPath) {
        $content = Get-Content $envPath
        
        # Update or add credentials
        $newContent = @()
        $foundAccess = $false
        $foundSecret = $false
        $foundToken = $false

        foreach ($line in $content) {
            if ($line -match "^AWS_ACCESS_KEY_ID=") {
                $newContent += "AWS_ACCESS_KEY_ID=$AccessKeyId"
                $foundAccess = $true
            }
            elseif ($line -match "^AWS_SECRET_ACCESS_KEY=") {
                $newContent += "AWS_SECRET_ACCESS_KEY=$SecretAccessKey"
                $foundSecret = $true
            }
            elseif ($line -match "^AWS_SESSION_TOKEN=") {
                $newContent += "AWS_SESSION_TOKEN=$SessionToken"
                $foundToken = $true
            }
            else {
                $newContent += $line
            }
        }

        if (-not $foundAccess) { $newContent += "AWS_ACCESS_KEY_ID=$AccessKeyId" }
        if (-not $foundSecret) { $newContent += "AWS_SECRET_ACCESS_KEY=$SecretAccessKey" }
        if (-not $foundToken) { $newContent += "AWS_SESSION_TOKEN=$SessionToken" }

        $newContent | Set-Content $envPath
        Write-Host ".env file updated successfully." -ForegroundColor Yellow
    }
    else {
        Write-Host "Warning: .env file not found. Please create one." -ForegroundColor Red
    }
}
else {
    Write-Host "Error: Failed to get credentials from AWS." -ForegroundColor Red
}
