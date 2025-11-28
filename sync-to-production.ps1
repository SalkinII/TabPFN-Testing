# PowerShell script to sync files from main branch to production branch
# Usage: .\sync-to-production.ps1 [--dry-run] [--push] [--no-backup]

param(
    [switch]$DryRun = $false,
    [switch]$Push = $false,
    [switch]$NoBackup = $false
)

$ErrorActionPreference = "Stop"
$ManifestFile = "production-manifest.txt"
$MainBranch = "main"
$ProductionBranch = "production"
$BackupBranch = "production-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Test-GitCommand {
    try {
        git --version | Out-Null
        return $true
    } catch {
        Write-Error "Git is not installed or not in PATH"
        return $false
    }
}

function Test-ManifestFile {
    if (-not (Test-Path $ManifestFile)) {
        Write-Error "Manifest file '$ManifestFile' not found!"
        Write-Info "Please create $ManifestFile with the list of files to sync."
        return $false
    }
    return $true
}

function Test-CleanWorkingDirectory {
    $status = git status --porcelain
    if ($status) {
        Write-Error "Working directory is not clean. Please commit or stash changes first."
        Write-Info "Uncommitted changes:"
        Write-Host $status
        return $false
    }
    return $true
}

function Test-CurrentBranch {
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne $MainBranch) {
        Write-Warning "Current branch is '$currentBranch', not '$MainBranch'"
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            return $false
        }
    }
    return $true
}

function Get-ManifestFiles {
    $files = @()
    Get-Content $ManifestFile | ForEach-Object {
        $line = $_.Trim()
        # Skip empty lines and comments
        if ($line -and -not $line.StartsWith("#")) {
            $files += $line
        }
    }
    return $files
}

function Test-FilesExist {
    param([string[]]$Files, [string]$Branch)
    
    $missingFiles = @()
    foreach ($file in $Files) {
        $exists = git cat-file -e "$Branch`:$file" 2>$null
        if (-not $exists) {
            $missingFiles += $file
        }
    }
    return $missingFiles
}

function Backup-ProductionBranch {
    if ($NoBackup) {
        Write-Info "Skipping backup (--no-backup flag set)"
        return $true
    }
    
    Write-Info "Creating backup branch: $BackupBranch"
    
    # Get current branch
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to determine current branch, skipping backup"
        return $false
    }
    
    # Checkout production branch if not already on it
    if ($currentBranch -ne $ProductionBranch) {
        $output = git checkout $ProductionBranch 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to checkout $ProductionBranch branch for backup: $output"
            return $false
        }
    }
    
    # Create backup branch
    $output = git checkout -b $BackupBranch 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to create backup branch: $output"
        # Try to return to original branch
        $null = git checkout $currentBranch 2>&1
        return $false
    }
    
    # Return to main branch
    $output = git checkout $MainBranch 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Backup created but failed to return to ${MainBranch}: $output"
        # Backup was created, so return true even if checkout failed
    }
    
    Write-Success "Backup branch created: $BackupBranch"
    return $true
}

function Sync-Files {
    param([string[]]$Files, [switch]$DryRun)
    
    Write-Info "Syncing files from $MainBranch to $ProductionBranch..."
    
    # Get current branch
    $currentBranch = git rev-parse --abbrev-ref HEAD
    
    # Checkout production branch if not already on it
    if ($currentBranch -ne $ProductionBranch) {
        $null = git checkout $ProductionBranch 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to checkout $ProductionBranch branch"
            return $false
        }
    }
    
    # Copy files from main branch
    $syncedFiles = @()
    $failedFiles = @()
    
    foreach ($file in $Files) {
        try {
            # Check if file exists in main branch
            git cat-file -e "$MainBranch`:$file" 2>$null
            if ($LASTEXITCODE -eq 0) {
                if (-not $DryRun) {
                    # Get file content from main branch and write to working directory
                    $content = git show "$MainBranch`:$file"
                    $filePath = Join-Path $PWD $file
                    $dir = Split-Path $filePath -Parent
                    if ($dir -and -not (Test-Path $dir)) {
                        New-Item -ItemType Directory -Path $dir -Force | Out-Null
                    }
                    [System.IO.File]::WriteAllText($filePath, $content)
                }
                $syncedFiles += $file
            } else {
                # File doesn't exist in main - check if it exists in production
                git cat-file -e "$ProductionBranch`:$file" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Info "File '$file' exists in production but not in main - preserving it"
                    $syncedFiles += $file
                } else {
                    Write-Warning "File '$file' does not exist in $MainBranch branch and will not be created"
                }
            }
        } catch {
            Write-Warning "Failed to sync '$file': $_"
            $failedFiles += $file
        }
    }
    
    # Remove files not in manifest
    if (-not $DryRun) {
        Write-Info "Removing files not in manifest..."
        $allFiles = git ls-tree -r --name-only $ProductionBranch
        $filesToRemove = $allFiles | Where-Object { 
            $_ -notin $Files -and 
            $_ -ne ".gitignore" -and
            $_ -ne $ManifestFile -and
            $_ -ne "sync-to-production.ps1" -and
            $_ -ne "DEPLOYMENT.md" -and
            $_ -notlike ".github/workflows/sync-production.yml"
        }
        
        foreach ($file in $filesToRemove) {
            if (Test-Path $file) {
                Remove-Item $file -Force -ErrorAction SilentlyContinue
                Write-Info "  Removed: $file"
            }
        }
    }
    
    Write-Success "Synced $($syncedFiles.Count) files"
    if ($failedFiles.Count -gt 0) {
        Write-Warning "Failed to sync $($failedFiles.Count) files"
    }
    
    return $true
}

function Commit-Changes {
    param([switch]$DryRun)
    
    if ($DryRun) {
        Write-Info "[DRY RUN] Would commit changes"
        return $true
    }
    
    $status = git status --porcelain
    if (-not $status) {
        Write-Info "No changes to commit"
        return $true
    }
    
    Write-Info "Staging changes..."
    git add -A 2>&1 | Out-Null
    
    $commitMessage = "Sync from main branch - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Info "Committing changes..."
    git commit -m $commitMessage 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Changes committed successfully"
        return $true
    } else {
        Write-Error "Failed to commit changes"
        return $false
    }
}

function Push-Changes {
    param([switch]$DryRun)
    
    if (-not $Push) {
        Write-Info "Skipping push (use --push to push to remote)"
        return $true
    }
    
    if ($DryRun) {
        Write-Info "[DRY RUN] Would push to remote"
        return $true
    }
    
    Write-Info "Pushing to remote..."
    git push origin $ProductionBranch 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Pushed to remote successfully"
        return $true
    } else {
        Write-Error "Failed to push to remote"
        return $false
    }
}

# Main execution
try {
    Write-Info "=========================================="
    Write-Info "Sync Main to Production Branch"
    Write-Info "=========================================="
    Write-Host ""
    
    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No changes will be made"
        Write-Host ""
    }
    
    # Validation checks
    if (-not (Test-GitCommand)) { exit 1 }
    if (-not (Test-ManifestFile)) { exit 1 }
    if (-not (Test-CleanWorkingDirectory)) { exit 1 }
    if (-not (Test-CurrentBranch)) { exit 1 }
    
    # Get files from manifest
    $manifestFiles = Get-ManifestFiles
    if ($manifestFiles.Count -eq 0) {
        Write-Error "No files found in manifest!"
        exit 1
    }
    
    Write-Info "Found $($manifestFiles.Count) files in manifest"
    Write-Host ""
    
    if ($DryRun) {
        Write-Info "Files that would be synced:"
        foreach ($file in $manifestFiles) {
            Write-Host "  - $file"
        }
        Write-Host ""
        Write-Info "[DRY RUN] No changes made"
        Write-Info "In actual run, a backup branch would be created before syncing"
        exit 0
    }
    
    # Create backup (skip in dry-run)
    Backup-ProductionBranch
    
    # Sync files
    if (-not (Sync-Files -Files $manifestFiles -DryRun:$DryRun)) {
        Write-Error "Failed to sync files"
        exit 1
    }
    
    # Commit changes
    if (-not (Commit-Changes -DryRun:$DryRun)) {
        Write-Error "Failed to commit changes"
        exit 1
    }
    
    # Push changes
    Push-Changes -DryRun:$DryRun
    
    # Return to main branch
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne $MainBranch) {
        Write-Info "Returning to $MainBranch branch..."
        $null = git checkout $MainBranch 2>&1
    }
    
    Write-Host ""
    Write-Success "=========================================="
    Write-Success "Sync completed successfully!"
    Write-Success "=========================================="
    
    if ($BackupBranch -and -not $NoBackup) {
        Write-Info "Backup branch created: $BackupBranch"
        Write-Info "To restore: git checkout $ProductionBranch && git reset --hard $BackupBranch"
    }
    
} catch {
    Write-Error "Error: $_"
    Write-Info "Returning to $MainBranch branch..."
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne $MainBranch) {
        $null = git checkout $MainBranch 2>&1
    }
    exit 1
}

