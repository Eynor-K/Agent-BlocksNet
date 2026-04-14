$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host "Starting automatic backup to GitHub..."

# Добавляем все изменения, кроме тех, что в .gitignore
git add .

# Проверяем, есть ли изменения для коммита
$changes = git status --porcelain
if ($changes) {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "Auto backup: $date"
    git push origin master
    Write-Host "Backup completed successfully at $date."
} else {
    Write-Host "No new changes to backup."
}
