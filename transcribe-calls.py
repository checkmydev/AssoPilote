"""
transcribe-calls.py
Transcrit les enregistrements d'appel avec Whisper (OpenAI),
puis reformate avec labels Conseiller / Appelant via Claude.

Usage (depuis le dossier Etienne) :
    set OPENAI_API_KEY=sk-...
    set ANTHROPIC_API_KEY=sk-ant-...
    python transcribe-calls.py
"""

import os, json, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

# Whisper local (pip install openai-whisper)
try:
    import whisper as _whisper
    _wmodel = _whisper.load_model("medium")
    print("Whisper local charge (medium).")
except ImportError:
    print("ERREUR : installe d'abord Whisper local :")
    print("  pip install openai-whisper")
    sys.exit(1)

ASSETS = pathlib.Path("assets")

CALLS = [
    {
        "file":   ASSETS / "Yves Beaumont.wav",
        "caller": "Yves Beaumont (homme, appelant)",
        "header": "[Enregistrement — 18 juin 2024, 14h32 | Durée : {dur}]",
        "label":  "email 13 — Yves Beaumont",
    },
    {
        "file":   ASSETS / "Gérard Mercier.wav",
        "caller": "Sandrine Mercier (femme), qui appelle au sujet de son père/frère Gérard Mercier décédé",
        "header": "[Enregistrement — 18 juin 2024, 15h47 | Durée : {dur}]",
        "label":  "email 14 — Sandrine Mercier",
    },
]

def fmt_dur(secs):
    m, s = int(secs)//60, int(secs)%60
    return f"{m} min {s:02d}s"

def transcribe(path):
    print(f"  Whisper local --> {path.name} ...")
    r = _wmodel.transcribe(str(path), language="fr")
    segs = r.get("segments", [])
    duration = segs[-1]["end"] if segs else 0
    print(f"       duree reelle : {fmt_dur(duration)}")
    return r["text"].strip(), duration

def add_speakers(raw_text, caller_desc):
    # Retourne le texte brut — labels ajoutés manuellement ensuite
    return raw_text

results = {}

for call in CALLS:
    print(f"\n{'='*55}")
    print(f"  {call['label']}")
    print(f"{'='*55}")

    if not call["file"].exists():
        print(f"  ❌ Fichier introuvable : {call['file']}")
        continue

    raw, duration = transcribe(call["file"])
    formatted     = add_speakers(raw, call["caller"])
    header        = call["header"].format(dur=fmt_dur(duration))
    full_transcript = f"{header}\n\n{formatted}"

    out = ASSETS / (call["file"].stem + "_transcript.txt")
    out.write_text(full_transcript, encoding="utf-8")

    results[call["label"]] = full_transcript

    print(f"\n--- TRANSCRIPT ({call['label']}) ---")
    print(full_transcript)
    print(f"--- FIN ---\n")

# Dump JSON compact pour mise à jour HTML
print("\n{'='*55}")
print("  JSON POUR MISE À JOUR HTML")
print("{'='*55}")
print(json.dumps(results, ensure_ascii=False, indent=2))
print("\n✅ Fichiers .txt sauvés dans assets/")
