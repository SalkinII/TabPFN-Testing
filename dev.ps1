# PowerShell Development Helper Script for TabPFN Data Quality Dashboard
# Usage: .\dev.ps1 [start|stop|restart|logs|clean|status|test|build]
#        .\dev.ps1 test [all|startup|web_app|csv_loading|data_quality|integration]
#        Examples:
#          .\dev.ps1 test                    # Run all test suites (default)
#          .\dev.ps1 test startup           # Run only startup tests
#          .\dev.ps1 test integration       # Run only integration tests

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'logs', 'clean', 'status', 'test', 'build')]
    [string]$Command = 'start',
    
    [Parameter(Position=1)]
    [ValidateSet('all', 'startup', 'web_app', 'csv_loading', 'data_quality', 'integration')]
    [string]$TestSuite = 'all'
)

$ContainerName = "tabpfn-data-quality-dev"
$ImageName = "tabpfn-data-quality"
$ComposeFile = "docker-compose.dev.yml"

function Load-EnvFile {
    # Load .env file if it exists
    if (Test-Path .env) {
        Write-Host "Loading environment variables from .env file..." -ForegroundColor Green
        Get-Content .env | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "  Loaded: $name" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host ".env file not found. TabPFN will use statistical fallback methods." -ForegroundColor Yellow
        Write-Host "To use TabPFN models, create .env file with: HF_TOKEN=your_token_here" -ForegroundColor Yellow
    }
}

function Start-DevContainer {
    Write-Host "Starting development container..." -ForegroundColor Green
    
    # Load .env file before starting
    Load-EnvFile
    
    # Check if container already exists and is running
    $existing = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}"
    if ($existing -eq $ContainerName) {
        $running = docker ps --filter "name=$ContainerName" --format "{{.Names}}"
        if ($running -eq $ContainerName) {
            Write-Host "Container is already running!" -ForegroundColor Yellow
            return
        } else {
            Write-Host "Starting existing container..." -ForegroundColor Yellow
            docker start $ContainerName
            return
        }
    }
    
    # Build and start with docker-compose
    Write-Host "Building and starting container with docker-compose..." -ForegroundColor Cyan
    docker-compose -f $ComposeFile up -d --build
    
    Write-Host "Development container started!" -ForegroundColor Green
    Write-Host "Application available at: http://localhost:5006" -ForegroundColor Cyan
    Write-Host "View logs with: .\dev.ps1 logs" -ForegroundColor Cyan
}

function Stop-DevContainer {
    Write-Host "Stopping development container..." -ForegroundColor Yellow
    docker-compose -f $ComposeFile down
    Write-Host "Container stopped." -ForegroundColor Green
}

function Restart-DevContainer {
    Write-Host "Restarting development container..." -ForegroundColor Yellow
    Stop-DevContainer
    Start-Sleep -Seconds 2
    Start-DevContainer
}

function Show-Logs {
    Write-Host "Showing container logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    docker-compose -f $ComposeFile logs -f
}

function Clean-Logs {
    Write-Host "Cleaning old log files in logs/dev/..." -ForegroundColor Yellow
    
    $devLogsPath = Join-Path $PSScriptRoot "logs\dev"
    if (Test-Path $devLogsPath) {
        $oldLogs = Get-ChildItem -Path $devLogsPath -Filter "*.json" | 
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
        
        if ($oldLogs.Count -gt 0) {
            $oldLogs | Remove-Item -Force
            Write-Host "Removed $($oldLogs.Count) old log files (older than 7 days)" -ForegroundColor Green
        } else {
            Write-Host "No old log files to clean." -ForegroundColor Green
        }
    } else {
        Write-Host "Logs directory does not exist yet." -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "Container Status:" -ForegroundColor Cyan
    docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host "`nRecent Logs:" -ForegroundColor Cyan
    docker-compose -f $ComposeFile logs --tail=20
}

function Build-Image {
    Write-Host "Building Docker image..." -ForegroundColor Cyan
    docker build -t $ImageName .
    Write-Host "Image built successfully!" -ForegroundColor Green
}

function Run-Tests {
    param(
        [string]$Suite = 'all'
    )
    
    # Test suite mapping
    $testSuites = @{
        'startup' = 'tests/test_container_startup.py'
        'web_app' = 'tests/test_web_app.py'
        'csv_loading' = 'tests/test_csv_loading.py'
        'data_quality' = 'tests/test_data_quality.py'
        'integration' = 'tests/test_integration.py'
    }
    
    # Check if container is running
    $running = docker ps --filter "name=$ContainerName" --format "{{.Names}}"
    
    if ($running -ne $ContainerName) {
        Write-Host "Container is not running. Starting container first..." -ForegroundColor Yellow
        Start-DevContainer
        Start-Sleep -Seconds 3  # Give container time to fully start
    }
    
    # Determine which tests to run
    $testsToRun = @()
    
    if ($Suite -eq 'all') {
        # Run all tests in logical order
        $testsToRun = @(
            @{ Name = 'Startup Tests'; File = 'tests/test_container_startup.py' }
            @{ Name = 'CSV Loading Tests'; File = 'tests/test_csv_loading.py' }
            @{ Name = 'Data Quality Tests'; File = 'tests/test_data_quality.py' }
            @{ Name = 'Web App Tests'; File = 'tests/test_web_app.py' }
            @{ Name = 'Integration Tests'; File = 'tests/test_integration.py' }
        )
    } else {
        # Run single test suite
        if ($testSuites.ContainsKey($Suite)) {
            # Format suite name: web_app -> Web App
            $suiteName = $Suite -replace '_', ' '
            $suiteName = (Get-Culture).TextInfo.ToTitleCase($suiteName)
            $testsToRun = @(
                @{ Name = "$suiteName Tests"; File = $testSuites[$Suite] }
            )
        } else {
            Write-Host "❌ Unknown test suite: $Suite" -ForegroundColor Red
            Write-Host "Available suites: all, startup, web_app, csv_loading, data_quality, integration" -ForegroundColor Yellow
            return 1
        }
    }
    
    Write-Host "Running test suite: $Suite" -ForegroundColor Cyan
    Write-Host ""
    
    $results = @()
    $totalPassed = 0
    $totalFailed = 0
    
    foreach ($test in $testsToRun) {
        $separator = "======================================================================"
        Write-Host $separator -ForegroundColor Cyan
        Write-Host "Running: $($test.Name)" -ForegroundColor Cyan
        Write-Host $separator -ForegroundColor Cyan
        Write-Host ""
        
        # Run test inside the container
        docker exec $ContainerName python $test.File
        
        $exitCode = $LASTEXITCODE
        $testResult = @{
            Name = $test.Name
            File = $test.File
            Passed = ($exitCode -eq 0)
            ExitCode = $exitCode
        }
        $results += $testResult
        
        if ($exitCode -eq 0) {
            $totalPassed++
            Write-Host ""
            Write-Host "✅ $($test.Name) passed" -ForegroundColor Green
        } else {
            $totalFailed++
            Write-Host ""
            Write-Host "❌ $($test.Name) failed (exit code: $exitCode)" -ForegroundColor Red
        }
        
        Write-Host ""
    }
    
    # Summary
    $summarySeparator = "======================================================================"
    Write-Host $summarySeparator -ForegroundColor Cyan
    Write-Host "Test Suite Summary" -ForegroundColor Cyan
    Write-Host $summarySeparator -ForegroundColor Cyan
    
    foreach ($result in $results) {
        $status = if ($result.Passed) { "✅ PASS" } else { "❌ FAIL" }
        Write-Host "$status : $($result.Name)" -ForegroundColor $(if ($result.Passed) { "Green" } else { "Red" })
    }
    
    Write-Host ""
    Write-Host "Total: $totalPassed passed, $totalFailed failed out of $($results.Count) test suite(s)" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Yellow" })
    
    if ($totalFailed -eq 0) {
        Write-Host "`n🎉 All test suites passed!" -ForegroundColor Green
        return 0
    } else {
        Write-Host "`n⚠️  Some test suites failed. Check output above for details." -ForegroundColor Red
        return 1
    }
}

# Main command dispatcher
switch ($Command) {
    'start' {
        Start-DevContainer
    }
    'stop' {
        Stop-DevContainer
    }
    'restart' {
        Restart-DevContainer
    }
    'logs' {
        Show-Logs
    }
    'clean' {
        Clean-Logs
    }
    'status' {
        Show-Status
    }
    'build' {
        Build-Image
    }
    'test' {
        Run-Tests -Suite $TestSuite
    }
}

