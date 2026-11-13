$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$WhisperDir = Join-Path $ProjectRoot "tools\whisper"
$WhisperModelDir = Join-Path $ProjectRoot "models\whisper"
$PiperModelDir = Join-Path $ProjectRoot "models\piper"
$DownloadDir = Join-Path $env:TEMP ("jarvis-voice-setup-" + [guid]::NewGuid())

New-Item -ItemType Directory -Force -Path $WhisperDir | Out-Null
New-Item -ItemType Directory -Force -Path $WhisperModelDir | Out-Null
New-Item -ItemType Directory -Force -Path $PiperModelDir | Out-Null
New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null

Write-Host "Installing Python voice packages..."
python -m pip install -r (Join-Path $ProjectRoot "requirements-voice.txt")

Write-Host "Downloading the latest official Whisper.cpp CPU build..."
$Releases = Invoke-RestMethod "https://api.github.com/repos/ggml-org/whisper.cpp/releases?per_page=20"
$Asset = $Releases |
    ForEach-Object { $_.assets } |
    Where-Object { $_.name -eq "whisper-bin-x64.zip" } |
    Select-Object -First 1
if (-not $Asset) {
    throw "No recent official Whisper.cpp release has a whisper-bin-x64.zip asset."
}
$WhisperZip = Join-Path $DownloadDir "whisper-bin-x64.zip"
Invoke-WebRequest -Uri $Asset.browser_download_url -OutFile $WhisperZip
$ExtractDir = Join-Path $DownloadDir "whisper"
Expand-Archive -Path $WhisperZip -DestinationPath $ExtractDir
Get-ChildItem -Path $ExtractDir -File -Recurse | Copy-Item -Destination $WhisperDir -Force

Write-Host "Downloading the Whisper base.en model..."
$WhisperModel = Join-Path $WhisperModelDir "ggml-base.en.bin"
Invoke-WebRequest `
    -Uri "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin" `
    -OutFile $WhisperModel

Write-Host "Downloading the Piper voice..."
python -m piper.download_voices --data-dir $PiperModelDir en_GB-alan-medium

Write-Host "Voice setup complete. Run: python main.py --voice"
