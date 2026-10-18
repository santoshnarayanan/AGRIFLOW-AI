# Logical backup of AGRIFLOW PostgreSQL (development / drill)
param(
    [string]$ContainerName = "agriflow-ai-db-1",
    [string]$DbUser = "agriflow",
    [string]$DbName = "agriflow",
    [string]$OutDir = "backups"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outFile = Join-Path $OutDir "agriflow-$stamp.dump"
$remotePath = "/tmp/agriflow-backup.dump"

Write-Host "Creating dump in container..."
podman exec $ContainerName pg_dump -U $DbUser -Fc -f $remotePath $DbName
Write-Host "Copying to $outFile ..."
podman cp "${ContainerName}:${remotePath}" $outFile
podman exec $ContainerName rm -f $remotePath
Write-Host "Done."
