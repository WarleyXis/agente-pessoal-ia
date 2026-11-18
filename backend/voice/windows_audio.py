import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

SYNTHESIZE = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voice = $synth.GetInstalledVoices() | Where-Object {
        $_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'pt-BR'
    } | Select-Object -First 1
    if (-not $voice) { throw 'Voz em portugues do Brasil indisponivel.' }
    $synth.SelectVoice($voice.VoiceInfo.Name)
    $synth.SetOutputToWaveFile($env:ATLAS_WAV_OUTPUT)
    $text = [IO.File]::ReadAllText($env:ATLAS_VOICE_TEXT, [Text.Encoding]::UTF8)
    $synth.Speak($text)
} finally {
    $synth.Dispose()
}
"""


def synthesize_wav(text: str) -> bytes:
    if sys.platform != "win32":
        raise RuntimeError("A síntese de áudio requer Windows.")
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    with TemporaryDirectory(prefix="atlas-speech-") as directory:
        source = Path(directory) / "speech.txt"
        output = Path(directory) / "speech.wav"
        source.write_text(text, encoding="utf-8")
        subprocess.run(
            [str(powershell), "-NoProfile", "-NonInteractive", "-Command", SYNTHESIZE],
            env=dict(os.environ, ATLAS_WAV_OUTPUT=str(output), ATLAS_VOICE_TEXT=str(source)),
            timeout=20,
            capture_output=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return output.read_bytes()
