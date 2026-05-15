Param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [string]$User = $env:USER
)

$py = "python"
$script = Join-Path $PSScriptRoot "log_prompt.py"
Start-Process -FilePath $py -ArgumentList ("$script --prompt " + [System.Text.RegularExpressions.Regex]::Escape($Prompt) + " --user " + $User) -NoNewWindow -Wait
