Param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [string]$User = $env:USER
)

$script = Join-Path $PSScriptRoot "log_prompt.py"

function Resolve-Python {
    param([string[]]$candidates)
    foreach ($c in $candidates) {
        try {
            if (Test-Path $c) { return $c }
            $cmd = Get-Command $c -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
        } catch { }
    }
    return $null
}

$py = Resolve-Python @(
    (Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"),
    (Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"),
    'python3',
    'python'
)

if (-not $py) { $py = 'python' }

Start-Process -FilePath $py -ArgumentList @($script, '--prompt', $Prompt, '--user', $User) -NoNewWindow -Wait
