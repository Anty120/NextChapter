# Optional maintainer tool. The committed WAV plays on every supported platform.
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    Add-Type -AssemblyName System.Speech
    $demoNarrator = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $demoNarrator.SelectVoice('Microsoft Zira Desktop')
        $demoNarrator.Rate = -2
        $demoNarration = python -c "from catalog.demo_content import ENGLISH_AUDIO; print(ENGLISH_AUDIO)"
        if ($LASTEXITCODE -ne 0) { throw 'Could not load demo narration text.' }
        $demoAudioDirectory = Join-Path (Get-Location) 'catalog/static/catalog/audio'
        New-Item -ItemType Directory -Path $demoAudioDirectory -Force | Out-Null
        $demoNarrator.SetOutputToWaveFile((Join-Path $demoAudioDirectory 'the-blue-door.wav'))
        $demoNarrator.Speak(($demoNarration -join ' '))
    } finally { $demoNarrator.Dispose() }
} finally { Pop-Location }
