#Requires -Version 5.1
<#
.SYNOPSIS
  Interactive installer for the Claude Agentic Orchestrator pack (Windows).
.DESCRIPTION
  Clients: Claude Code, OpenAI Codex CLI, GitHub Copilot (pick any combination).
  Two modes, chosen automatically:
    PACK MODE   - user-claude\ and repo-root\ found near this script: copies them.
    VERIFY MODE - payloads not found: assumes you copied files manually, verifies
                  each destination instead, and still merges hooks + runs tooling.
  Hook settings are embedded, so the merge works in both modes.
  Prerequisite: domain agent packs in place before running, so the generated
  registry includes them (discovery scans .claude/.github/.copilot/.codex agents).
.PARAMETER RepoPath
  Target repository root. Prompted for when omitted.
#>
[CmdletBinding()]
param([string]$RepoPath)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$Text)  { Write-Host "`n==> $Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text)    { Write-Host "    [OK] $Text" -ForegroundColor Green }
function Write-Warn2([string]$Text) { Write-Host "    [!] $Text" -ForegroundColor Yellow }
function Write-Fail([string]$Text)  { Write-Host "    [X] $Text" -ForegroundColor Red }

function Confirm-YesNo([string]$Question, [bool]$DefaultYes = $true) {
    $suffix = if ($DefaultYes) { '[Y/n]' } else { '[y/N]' }
    $answer = Read-Host "$Question $suffix"
    if ([string]::IsNullOrWhiteSpace($answer)) { return $DefaultYes }
    return $answer.Trim().ToLower().StartsWith('y')
}

function Copy-Tree([string]$Source, [string]$Destination) {
    $copied = 0; $skipped = 0
    Get-ChildItem -Path $Source -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($Source.Length).TrimStart('\', '/')
        $target = Join-Path $Destination $relative
        $targetDir = Split-Path $target -Parent
        if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        if (Test-Path $target) {
            $same = (Get-FileHash $_.FullName).Hash -eq (Get-FileHash $target).Hash
            if ($same) { $skipped++; return }
            if (-not (Confirm-YesNo "    Overwrite existing (differs): $relative" $false)) { $skipped++; return }
        }
        Copy-Item $_.FullName $target -Force
        $copied++
    }
    Write-Ok "$copied file(s) copied, $skipped skipped (identical or kept)"
}

function Get-AgentRoster([string]$Python, [string]$Repo) {
    try {
        $raw = & cmd /c "$Python tooling\workflow.py discover 2>nul"
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
        $data = ($raw -join "`n") | ConvertFrom-Json
        return @($data.agents)
    } catch { return $null }
}

function Select-AgentsFromRoster([object[]]$Roster, [bool]$Single = $false) {
    Write-Host ''
    Write-Host '      #   Agent id                                Installed' -ForegroundColor Gray
    Write-Host '      --- --------------------------------------- ---------' -ForegroundColor Gray
    for ($i = 0; $i -lt $Roster.Count; $i++) {
        $mark = if ($Roster[$i].available) { 'yes' } else { 'NO ' }
        $line = '      {0,-3} {1,-39} {2}' -f ($i + 1), $Roster[$i].id, $mark
        if ($Roster[$i].available) { Write-Host $line } else { Write-Host $line -ForegroundColor DarkYellow }
    }
    Write-Host ''
    $hint = if ($Single) { 'one number' } else { "numbers, e.g. 1,4,6 or 2-5 (or 'a' for all installed)" }
    while ($true) {
        $answer = (Read-Host "      Pick $hint").Trim().ToLower()
        if (-not $Single -and $answer -eq 'a') {
            return @($Roster | Where-Object { $_.available } | ForEach-Object { $_.id })
        }
        $picked = New-Object System.Collections.Generic.List[string]
        $valid = $true
        foreach ($token in ($answer -split '[,\s]+' | Where-Object { $_ })) {
            if ($token -match '^(\d+)-(\d+)$') {
                $lo = [int]$Matches[1]; $hi = [int]$Matches[2]
                if ($lo -lt 1 -or $hi -gt $Roster.Count -or $lo -gt $hi) { $valid = $false; break }
                $lo..$hi | ForEach-Object { $picked.Add($Roster[$_ - 1].id) }
            } elseif ($token -match '^\d+$') {
                $n = [int]$token
                if ($n -lt 1 -or $n -gt $Roster.Count) { $valid = $false; break }
                $picked.Add($Roster[$n - 1].id)
            } else { $valid = $false; break }
        }
        if (-not $valid -or $picked.Count -eq 0) { Write-Warn2 "Invalid selection: $answer"; continue }
        if ($Single -and $picked.Count -gt 1) { Write-Warn2 'Pick exactly one number for this mode.'; continue }
        return @($picked | Select-Object -Unique)
    }
}

# Hook settings embedded so VERIFY MODE never needs the pack files.
$HookSettingsJson = @'
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/hooks/claude_event.py\" --event SessionStart" } ] }
    ],
    "SubagentStart": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/hooks/claude_event.py\" --event SubagentStart" } ] }
    ],
    "SubagentStop": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/hooks/claude_event.py\" --event SubagentStop" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/hooks/claude_event.py\" --event Stop", "timeout": 30 } ] }
    ]
  }
}
'@

$ExpectedSkills = @(
    'agentic-workflow-dispatch',
    'agent-registry-and-capability-discovery',
    'handoff-contract-and-state',
    'claude-subagent-delegation',
    'claude-hooks-and-guardrails',
    'workflow-evidence-and-recovery'
)

Write-Host ''
Write-Host '=============================================================' -ForegroundColor Cyan
Write-Host '  Claude Agentic Orchestrator - interactive installer'        -ForegroundColor Cyan
Write-Host '=============================================================' -ForegroundColor Cyan
Write-Host '  Read PLACEMENT.md for the full map of what goes where.'

# ---------------------------------------------------------------- step 1: payloads
Write-Step 'Step 1/8  Locating the pack payloads'
function Find-PackRoot([string]$Start) {
    $candidates = @($Start)
    $candidates += Get-ChildItem $Start -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    $candidates += Get-ChildItem $Start -Directory -ErrorAction SilentlyContinue |
        Get-ChildItem -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    $parent = Split-Path $Start -Parent
    if ($parent) {
        $candidates += $parent
        $candidates += Get-ChildItem $parent -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    }
    foreach ($c in $candidates) {
        if ((Test-Path (Join-Path $c 'user-claude')) -and (Test-Path (Join-Path $c 'repo-root'))) { return $c }
    }
    return $null
}
$PackRoot = Find-PackRoot $PSScriptRoot
$VerifyMode = $false
if ($PackRoot) {
    Write-Ok "Pack payloads found at: $PackRoot"
    $userPayload = Join-Path $PackRoot 'user-claude'
    $repoPayload = Join-Path $PackRoot 'repo-root'
    $agentFiles = @(Get-ChildItem (Join-Path $userPayload 'agents') -Filter *.md -Recurse -ErrorAction SilentlyContinue)
    $skillFiles = @(Get-ChildItem (Join-Path $userPayload 'skills') -Filter SKILL.md -Recurse -ErrorAction SilentlyContinue)
    Write-Ok "user-claude\agents : $($agentFiles.Count) agent file(s)"
    Write-Ok "user-claude\skills : $($skillFiles.Count) skill(s)"
    if ($agentFiles.Count -le 1) {
        Write-Warn2 'Only the orchestrator itself is present. Domain agent packs should be in'
        Write-Warn2 'user-claude\ before installing so the generated registry includes them'
        Write-Warn2 '(or add them to the agent folders later and re-run: python tooling\workflow.py registry).'
        if (-not (Confirm-YesNo '    Continue anyway?' $true)) { exit 0 }
    }
} else {
    $VerifyMode = $true
    Write-Warn2 'Payload folders (user-claude\ + repo-root\) not found near this script.'
    Write-Ok  'Switching to VERIFY MODE: assuming you already copied the files manually.'
    Write-Ok  'Each destination will be checked instead of copied.'
}

# ---------------------------------------------------------------- step 2: clients
Write-Step 'Step 2/8  Selecting clients'
Write-Host '    Detected on this machine:' -ForegroundColor Gray
if (Test-Path (Join-Path $env:USERPROFILE '.claude'))  { Write-Host '      - Claude Code   (.claude exists)'  -ForegroundColor Gray }
if (Test-Path (Join-Path $env:USERPROFILE '.codex'))   { Write-Host '      - Codex CLI     (.codex exists)'   -ForegroundColor Gray }
if (Test-Path (Join-Path $env:USERPROFILE '.copilot')) { Write-Host '      - Copilot CLI   (.copilot exists)' -ForegroundColor Gray }
$DoClaude  = Confirm-YesNo '    Install for Claude Code?' $true
$DoCodex   = Confirm-YesNo '    Install for OpenAI Codex CLI?' (Test-Path (Join-Path $env:USERPROFILE '.codex'))
$DoCopilot = Confirm-YesNo '    Install for GitHub Copilot?' (Test-Path (Join-Path $env:USERPROFILE '.copilot'))
if (-not ($DoClaude -or $DoCodex -or $DoCopilot)) { Write-Fail 'No client selected.'; exit 0 }

# ---------------------------------------------------------------- step 3: user .claude
Write-Step 'Step 3/8  Locating your user-scope Claude folder'
$userClaude = Join-Path $env:USERPROFILE '.claude'
if (Test-Path $userClaude) {
    Write-Ok "Found: $userClaude"
} else {
    Write-Warn2 "Not found: $userClaude"
    if (Confirm-YesNo '    Create it?' $true) { New-Item -ItemType Directory -Path $userClaude -Force | Out-Null; Write-Ok 'Created.' }
    else { Write-Fail 'Cannot continue without a user .claude folder.'; exit 1 }
}

# ---------------------------------------------------------------- step 4: Claude user scope
if ($VerifyMode) {
    Write-Step "Step 4/8  Verifying agent + skills in $userClaude"
    $orchestrator = Get-ChildItem (Join-Path $userClaude 'agents') -Filter *.md -Recurse -ErrorAction SilentlyContinue |
        Where-Object { (Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue) -match '(?m)^name:\s*claude-agentic-orchestrator\s*$' }
    if ($orchestrator) { Write-Ok "Orchestrator agent present: $($orchestrator[0].FullName)" }
    else { Write-Warn2 'claude-agentic-orchestrator agent NOT found in agents\. Copy user-claude\agents\claude-agentic-orchestrator.md there.' }
    $missingSkills = @()
    foreach ($s in $ExpectedSkills) {
        if (Test-Path (Join-Path $userClaude "skills\$s\SKILL.md")) { Write-Ok "skill: $s" }
        else { $missingSkills += $s; Write-Warn2 "skill MISSING: $s" }
    }
    if ((-not $orchestrator) -or $missingSkills.Count -gt 0) {
        if (-not (Confirm-YesNo '    Some pieces are missing (see above). Continue anyway?' $true)) { exit 0 }
    }
} else {
    Write-Step "Step 4/8  Installing agent + skills  ->  $userClaude"
    if ($DoClaude) { Copy-Tree $userPayload $userClaude } else { Write-Ok 'Skipped (Claude Code not selected).' }
}

# ---------------------------------------------------------------- step 5: Codex / Copilot user scope
Write-Step 'Step 5/8  Codex / Copilot user-scope agents and skills'
$skillsSource = if (-not $VerifyMode) { Join-Path $userPayload 'skills' } else { $null }
if ($DoCodex) {
    $codexAgents = Join-Path $env:USERPROFILE '.codex\agents'
    $sharedSkills = Join-Path $env:USERPROFILE '.agents\skills'
    if ($VerifyMode) {
        if (Test-Path (Join-Path $codexAgents 'claude-agentic-orchestrator.toml')) { Write-Ok 'Codex: orchestrator agent present' }
        else { Write-Warn2 'Codex: .codex\agents\claude-agentic-orchestrator.toml missing (copy from user-codex\agents)' }
    } else {
        New-Item -ItemType Directory -Path $codexAgents, $sharedSkills -Force | Out-Null
        Copy-Tree (Join-Path $PackRoot 'user-codex\agents') $codexAgents
        Copy-Tree $skillsSource $sharedSkills
        Write-Ok 'Codex: agent -> ~\.codex\agents ; skills -> ~\.agents\skills (shared open standard)'
    }
}
if ($DoCopilot) {
    $copilotAgents = Join-Path $env:USERPROFILE '.copilot\agents'
    $sharedSkills = Join-Path $env:USERPROFILE '.agents\skills'
    if ($VerifyMode) {
        if (Test-Path (Join-Path $copilotAgents 'claude-agentic-orchestrator.agent.md')) { Write-Ok 'Copilot: orchestrator agent present' }
        else { Write-Warn2 'Copilot: .copilot\agents\claude-agentic-orchestrator.agent.md missing (copy from user-copilot\agents)' }
    } else {
        New-Item -ItemType Directory -Path $copilotAgents, $sharedSkills -Force | Out-Null
        Copy-Tree (Join-Path $PackRoot 'user-copilot\agents') $copilotAgents
        if (-not $DoCodex) { Copy-Tree $skillsSource $sharedSkills }
        Write-Ok 'Copilot: agent -> ~\.copilot\agents ; skills -> ~\.agents\skills (shared open standard)'
    }
}
if (-not ($DoCodex -or $DoCopilot)) { Write-Ok 'Skipped (Claude only).' }

# ---------------------------------------------------------------- step 6: repository
Write-Step 'Step 6/8  Repository tooling and hooks'
while ([string]::IsNullOrWhiteSpace($RepoPath) -or -not (Test-Path $RepoPath -PathType Container)) {
    if (-not [string]::IsNullOrWhiteSpace($RepoPath)) { Write-Warn2 "Not a folder: $RepoPath" }
    $RepoPath = Read-Host '    Path to the repository where workflows will run'
    $RepoPath = $RepoPath.Trim('"',' ')
}
$RepoPath = (Resolve-Path $RepoPath).Path
Write-Ok "Target repository: $RepoPath"
if ($VerifyMode) {
    $repoOk = $true
    foreach ($rel in @('hooks\claude_event.py', 'tooling\workflow.py', 'tooling\agent-registry.yml')) {
        if (Test-Path (Join-Path $RepoPath $rel)) { Write-Ok "present: $rel" }
        else { $repoOk = $false; Write-Warn2 "MISSING: $rel  (copy it from the pack's repo-root\ into the repository)" }
    }
    if (-not $repoOk) {
        Write-Warn2 'The Python steps below will fail until the missing files are in place.'
        if (-not (Confirm-YesNo '    Continue anyway?' $true)) { exit 0 }
    }
} else {
    Get-ChildItem $repoPayload -Directory | Where-Object { $_.Name -notin @('.claude', '.codex', '.github') } | ForEach-Object {
        Copy-Tree $_.FullName (Join-Path $RepoPath $_.Name)
    }
    if ($DoCodex)   { Copy-Tree (Join-Path $repoPayload '.codex')  (Join-Path $RepoPath '.codex') }
    if ($DoCopilot) { Copy-Tree (Join-Path $repoPayload '.github') (Join-Path $RepoPath '.github') }
}
# AGENTS.md orchestration section (Codex + Copilot read AGENTS.md)
if ($DoCodex -or $DoCopilot) {
    $agBlock = if (-not $VerifyMode) { Join-Path $repoPayload 'AGENTS-orchestrator.md' } else { Join-Path $RepoPath 'AGENTS-orchestrator.md' }
    $agPath = Join-Path $RepoPath 'AGENTS.md'
    if (-not (Test-Path $agBlock)) {
        Write-Warn2 'AGENTS-orchestrator.md not found; skipping AGENTS.md update.'
    } elseif ((Test-Path $agPath) -and ((Get-Content $agPath -Raw) -match 'BEGIN claude-agentic-orchestrator')) {
        Write-Ok 'AGENTS.md already contains the orchestration section.'
    } else {
        if (Test-Path $agPath) { Add-Content $agPath "`n" }
        Add-Content $agPath (Get-Content $agBlock -Raw)
        Write-Ok 'Orchestration section appended to AGENTS.md'
    }
}

# ---------------------------------------------------------------- step 7: settings merge
Write-Step "Step 7/8  Merging Claude hook entries into $RepoPath\.claude\settings.json"
if ($DoClaude -or $DoCopilot) {
    $settingsDir = Join-Path $RepoPath '.claude'
    $settingsPath = Join-Path $settingsDir 'settings.json'
    if (-not (Test-Path $settingsDir)) { New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null }
    $packSettings = $HookSettingsJson | ConvertFrom-Json
    if (-not (Test-Path $settingsPath)) {
        Set-Content $settingsPath $HookSettingsJson -Encoding UTF8
        Write-Ok 'No settings.json existed; hook settings installed as settings.json.'
    } else {
        Copy-Item $settingsPath "$settingsPath.backup-orchestrator" -Force
        Write-Ok 'Backup written: settings.json.backup-orchestrator'
        $existing = Get-Content $settingsPath -Raw | ConvertFrom-Json
        if (-not ($existing.PSObject.Properties.Name -contains 'hooks')) {
            $existing | Add-Member -MemberType NoteProperty -Name hooks -Value ([pscustomobject]@{})
        }
        $added = 0; $present = 0
        foreach ($eventProp in $packSettings.hooks.PSObject.Properties) {
            $eventName = $eventProp.Name
            $already = $false
            if ($existing.hooks.PSObject.Properties.Name -contains $eventName) {
                $json = $existing.hooks.$eventName | ConvertTo-Json -Depth 10
                if ($json -match 'claude_event\.py') { $already = $true }
            } else {
                $existing.hooks | Add-Member -MemberType NoteProperty -Name $eventName -Value @()
            }
            if ($already) { $present++; continue }
            $existing.hooks.$eventName = @($existing.hooks.$eventName) + $eventProp.Value
            $added++
        }
        $existing | ConvertTo-Json -Depth 20 | Set-Content $settingsPath -Encoding UTF8
        Write-Ok "$added hook event(s) merged, $present already present. Existing settings preserved."
    }
    if ($DoCopilot) { Write-Warn2 'VS Code Copilot reads these Claude hooks only when chat.useClaudeHooks is enabled (off by default).' }
} else {
    Write-Ok 'Skipped (Codex only; Codex uses .codex\hooks.sample.json instead).'
}

# ---------------------------------------------------------------- step 8: guided tooling run
Write-Step 'Step 8/8  Running the Python workflow tooling (guided)'
$python = $null
foreach ($candidate in @('py -3', 'python', 'python3')) {
    try {
        $probe = & cmd /c "$candidate --version 2>&1"
        if ($LASTEXITCODE -eq 0 -and "$probe" -match 'Python 3') { $python = $candidate; break }
    } catch { }
}
if (-not $python) {
    Write-Warn2 'Python 3 was not found on PATH. Files are in place; when Python is'
    Write-Warn2 'available, run from the repo root:'
    Write-Warn2 '    python tooling\workflow.py registry'
    Write-Warn2 '    python tooling\workflow.py discover'
    exit 0
}
Write-Ok "Using: $python"
if (-not (Test-Path (Join-Path $RepoPath 'tooling\workflow.py'))) {
    Write-Warn2 'tooling\workflow.py is not in the repository; skipping the guided run.'
    exit 0
}
Push-Location $RepoPath
try {
    Write-Host ''
    Write-Host '    The registry is generated from your INSTALLED agents (all ecosystems, repo + user scope).' -ForegroundColor Gray
    if (Confirm-YesNo '    Run now: workflow.py registry ?' $true) {
        & cmd /c "$python tooling\workflow.py registry"
    }
    Write-Host ''
    Write-Host '    Discover reports which registry agents are installed, where, and for which clients.' -ForegroundColor Gray
    if (Confirm-YesNo '    Run now: workflow.py discover ?' $true) {
        & cmd /c "$python tooling\workflow.py discover"
    }
    Write-Host ''
    Write-Host '    A workflow records delegation state under .agentic\ before any agent runs.' -ForegroundColor Gray
    if (Confirm-YesNo '    Create a workflow now (workflow.py init)?' $false) {
        $mode = ''
        while ($mode -notin @('one', 'selected', 'all')) { $mode = (Read-Host '      Mode  [one | selected | all]').Trim().ToLower() }
        $agents = ''
        $optional = ''
        if ($mode -in @('selected', 'one')) {
            $roster = Get-AgentRoster $python $RepoPath
            if ($roster) {
                $chosen = Select-AgentsFromRoster $roster ($mode -eq 'one')
                $agents = $chosen -join ','
                Write-Ok "Selected: $agents"
                if ($mode -eq 'selected' -and $chosen.Count -gt 1) {
                    if (Confirm-YesNo '      Mark any of these OPTIONAL (skipped instead of blocking when unavailable)?' $false) {
                        $optChosen = Select-AgentsFromRoster ($roster | Where-Object { $_.id -in $chosen })
                        $optional = $optChosen -join ','
                        Write-Ok "Optional: $optional"
                    }
                }
            } else {
                Write-Warn2 'Discovery failed; type ids manually.'
                $agents = (Read-Host '      Agent ids, comma-separated').Trim()
            }
        }
        $objective = ''
        while ([string]::IsNullOrWhiteSpace($objective)) { $objective = Read-Host '      Objective (one line)' }
        $enforce = if (Confirm-YesNo '      Enforce completion at session stop (--enforce-stop)?' $false) { '--enforce-stop' } else { '' }
        $agentArg = if ($agents) { "--agents `"$agents`"" } else { '' }
        $optArg = if ($optional) { "--optional-agents `"$optional`"" } else { '' }
        & cmd /c "$python tooling\workflow.py init --mode $mode $agentArg $optArg --objective `"$objective`" $enforce"
        Write-Host ''
        Write-Host '    Validate later with:' -ForegroundColor Gray
        Write-Host '      python tooling\workflow.py validate --workflow <workflow-id>' -ForegroundColor Gray
    }
} finally { Pop-Location }

Write-Host ''
Write-Host '=============================================================' -ForegroundColor Green
Write-Host '  Install complete.' -ForegroundColor Green
if ($DoClaude)  { Write-Host "  Claude Code : new session from $RepoPath, then @agent-claude-agentic-orchestrator or claude --agent claude-agentic-orchestrator" -ForegroundColor Green }
if ($DoCodex)   { Write-Host '  Codex CLI   : codex, then ask for the orchestrator agent; enable .codex\hooks.sample.json after review + trust via /hooks' -ForegroundColor Green }
if ($DoCopilot) { Write-Host '  Copilot     : copilot --agent claude-agentic-orchestrator (CLI) or pick the agent in VS Code chat; enable .github\hooks\*.sample.json after review' -ForegroundColor Green }
Write-Host '=============================================================' -ForegroundColor Green
