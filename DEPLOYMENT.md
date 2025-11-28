# Deployment Guide

This document describes how to deploy the TabPFN Data Quality Dashboard from the `main` branch to the `production` branch.

## Overview

The project uses a two-branch strategy:
- **`main` branch**: Contains full development setup including dev tools, test files, and data corruption features
- **`production` branch**: Contains only production-ready code, optimized for deployment via GitHub Actions

## Automated Sync Process

### GitHub Actions (Automatic)

When you push to the `main` branch, a GitHub Actions workflow automatically syncs production-ready files to the `production` branch. The workflow:

1. Reads `production-manifest.txt` to determine which files to sync
2. Copies only manifest-listed files from `main` to `production`
3. Removes files not in the manifest from `production`
4. Commits and pushes the changes
5. Triggers the Docker image build workflow

**Workflow file**: `.github/workflows/sync-production.yml`

### Manual Sync (Local)

For more control or testing, use the PowerShell sync script:

```powershell
# Preview what will be synced (dry run)
.\sync-to-production.ps1 --dry-run

# Sync files locally (no push to remote)
.\sync-to-production.ps1

# Sync and push to remote
.\sync-to-production.ps1 --push

# Skip backup branch creation
.\sync-to-production.ps1 --no-backup
```

**Script file**: `sync-to-production.ps1`

## Production Manifest

The `production-manifest.txt` file defines which files are included in production. Only files explicitly listed in this manifest will be synced.

### Included Files

- Core application files (`app.py`, `data_quality.py`, `utils.py`, etc.)
- Docker configuration (`Dockerfile`, `.dockerignore`, `.env.example`)
- Production compose file (`docker-compose.prod.yml`)
- GitHub Actions workflow (`.github/workflows/docker-publish.yml`)
- Production-relevant documentation (README files, user guides)
- Git configuration (`.gitignore`)

### Excluded Files

- Development scripts (`dev.ps1`, `dev.bat`)
- Development compose file (`docker-compose.dev.yml`)
- Data corruption features (`corrupt_data.py`, `corruption_framework.py`)
- Test files (`tests/` directory)
- Demo notebooks (`TabPFN_Demo_Local.ipynb`)
- Plan files (`.cursor/plans/`)
- Local setup documentation (`LOCAL_SETUP.md`)
- This deployment guide (`DEPLOYMENT.md`)

## Workflow

### Typical Deployment Process

1. **Develop on main branch**
   ```powershell
   git checkout main
   # Make your changes
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Automatic sync**
   - GitHub Actions automatically syncs to `production` branch
   - Production branch push triggers Docker image build
   - New image is published to GitHub Container Registry

3. **Verify deployment**
   ```powershell
   git checkout production
   git log --oneline -5
   ```

### Manual Sync Process

If you need to manually sync:

```powershell
# Ensure you're on main branch with clean working directory
git checkout main
git status  # Should be clean

# Run sync script
.\sync-to-production.ps1 --dry-run  # Preview first
.\sync-to-production.ps1 --push      # Actually sync and push
```

## Safety Features

### Validation Checks

The sync script performs several validation checks:

- ✅ Verifies Git is installed and accessible
- ✅ Checks that `production-manifest.txt` exists
- ✅ Ensures working directory is clean (no uncommitted changes)
- ✅ Warns if not on `main` branch (but allows override)

### Backup Mechanism

By default, the sync script creates a backup branch before syncing:

```
production-backup-YYYYMMDD-HHMMSS
```

To restore from backup:
```powershell
git checkout production
git reset --hard production-backup-YYYYMMDD-HHMMSS
```

To skip backup:
```powershell
.\sync-to-production.ps1 --no-backup
```

### Dry Run Mode

Always test with `--dry-run` first to preview changes:

```powershell
.\sync-to-production.ps1 --dry-run
```

This shows what files would be synced without making any changes.

## Troubleshooting

### Sync Script Fails

**Error: "Working directory is not clean"**
- Commit or stash your changes first
- Or use `git stash` to temporarily save changes

**Error: "Manifest file not found"**
- Ensure `production-manifest.txt` exists in the repository root
- Check that you're in the correct directory

**Error: "Failed to checkout production branch"**
- Ensure the `production` branch exists: `git branch -a`
- If it doesn't exist locally, fetch it: `git fetch origin production`

### GitHub Actions Fails

**Workflow doesn't trigger**
- Ensure you're pushing to `main` branch
- Check workflow file syntax in `.github/workflows/sync-production.yml`

**Permission denied**
- Verify the workflow has `contents: write` permission
- Check repository settings → Actions → General → Workflow permissions

**Files not syncing**
- Verify files exist in `main` branch
- Check `production-manifest.txt` includes the files
- Review workflow logs for specific errors

### Files Missing in Production

**File exists in main but not in production**
- Check if file is listed in `production-manifest.txt`
- Add file to manifest if it should be in production
- Re-run sync process

**File was accidentally removed**
- Restore from backup branch (see Backup Mechanism above)
- Or restore from git history: `git checkout production -- path/to/file`

## Best Practices

1. **Always test with dry-run first**
   ```powershell
   .\sync-to-production.ps1 --dry-run
   ```

2. **Keep manifest up to date**
   - When adding new production files, update `production-manifest.txt`
   - When removing files, ensure they're not in the manifest

3. **Review changes before pushing**
   ```powershell
   git checkout production
   git log --oneline -5
   git diff main..production
   ```

4. **Use meaningful commit messages on main**
   - These appear in production sync commits
   - Helps track what was deployed

5. **Monitor GitHub Actions**
   - Check workflow runs after pushing to main
   - Verify Docker image builds successfully

## File Structure

```
TabPFN-Testing/
├── production-manifest.txt          # File inclusion list for production
├── sync-to-production.ps1           # Local sync script
├── DEPLOYMENT.md                    # This file (excluded from production)
├── .github/
│   └── workflows/
│       ├── docker-publish.yml      # Production Docker build
│       └── sync-production.yml     # Auto-sync workflow
└── ...
```

## Related Documentation

- **README.md**: General project documentation
- **README_HF_TOKEN.md**: Hugging Face token setup
- **docs/User_Guide.md**: Application user guide
- **docs/Pipeline_Workflow.md**: Operational workflow

## Support

If you encounter issues with the deployment process:

1. Check this guide's Troubleshooting section
2. Review GitHub Actions workflow logs
3. Test sync script with `--dry-run` flag
4. Check git history for recent changes

