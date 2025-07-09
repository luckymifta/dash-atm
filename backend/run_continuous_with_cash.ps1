# ATM Data Retrieval Script - Continuous Operation with 15-minute interval
# Includes cash information and saves to database
#
# This PowerShell script runs the combined_atm_retrieval_script.py in continuous mode
# with a 15-minute interval, saving data to the database.

$host.UI.RawUI.WindowTitle = "ATM Data Retrieval - Continuous Operation (15m)"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "ATM Data Retrieval - Continuous Operation (15-minute interval)" -ForegroundColor Cyan
Write-Host "Includes Cash Information and Database Storage" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting continuous operation at $(Get-Date)" -ForegroundColor Green
Write-Host "Press CTRL+C to stop the script" -ForegroundColor Yellow
Write-Host ""

# Set Python executable - adjust path if needed
$pythonCmd = "python"

# Set log file path
$logFile = "continuous_retrieval_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Run the script with appropriate parameters
try {
    & $pythonCmd combined_atm_retrieval_script.py --continuous --interval 900 --include-cash --save-to-db --log-file $logFile
} catch {
    Write-Host "Error running script: $_" -ForegroundColor Red
    Write-Host "Check that Python is installed and in your PATH" -ForegroundColor Red
}

Write-Host ""
Write-Host "Script terminated at $(Get-Date)" -ForegroundColor Green
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
