$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$executable = Join-Path $projectRoot '.tools\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw 'Ollama is missing. See docs/LOCAL_SETUP.md.'
}
$listener = [Net.Sockets.TcpClient]::new()
try {
    $listener.Connect('127.0.0.1', 11435)
    throw 'Port 11435 is already in use. Check the existing service before starting another.'
} catch [Net.Sockets.SocketException] {
    # Connection refused means the dedicated local port is available.
} finally {
    $listener.Dispose()
}
$runtimePath = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
$modelPath = Join-Path $projectRoot '.models\ollama'
New-Item -ItemType Directory -Path $modelPath -Force | Out-Null
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = $modelPath
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
$process = Start-Process -FilePath $executable -ArgumentList 'serve' `
    -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $runtimePath 'ollama.stdout.log') `
    -RedirectStandardError (Join-Path $runtimePath 'ollama.stderr.log')
@{ pid = $process.Id; executable = $executable; started_at = $process.StartTime.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimePath 'ollama-process.json')
Write-Output "Local Ollama started: PID $($process.Id), http://127.0.0.1:11435"
