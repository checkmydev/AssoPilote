"""
generate-demo-assets.py
Génère les assets audio et image pour la démo AssoPilot.

  • Appel Yves Beaumont    → assets/appel_beaumont.mp3  (OpenAI tts-1-hd)
  • Appel Sandrine Mercier → assets/appel_mercier.mp3   (OpenAI tts-1-hd)
  • Lettre René Gauthier  → assets/lettre_gauthier.jpg  (DALL-E 3)

Prérequis : pip install openai requests   (pas de pydub, pas de ffmpeg)

Usage :
    set OPENAI_API_KEY=sk-...
    set GITHUB_TOKEN=ghp_...    (optionnel — push auto vers GitHub)
    python generate-demo-assets.py
"""

import os, io, wave, time, textwrap, pathlib, base64, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from openai import OpenAI

client  = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
ASSETS  = pathlib.Path("assets")
ASSETS.mkdir(exist_ok=True)

# ── Voix OpenAI tts-1-hd ──────────────────────────────────────────────────────
# onyx   = grave, posé, professionnel   → Conseiller
# fable  = expressif, chaleureux        → Yves Beaumont (plus de range émotionnel)
# shimmer = féminin, doux, empathique   → Sandrine Mercier
VOICE_CONSEILLER  = "onyx"
VOICE_APPELANT_M  = "fable"
VOICE_APPELANTE_F = "shimmer"

SAMPLE_RATE = 24000          # Hz — format PCM OpenAI
SILENCE_MS  = 450            # pause entre répliques
SCENE_MS    = 950            # pause après ligne [système]

def _sil(ms): return b'\x00\x00' * int(SAMPLE_RATE * ms / 1000)
SIL, SIL_SCENE = _sil(SILENCE_MS), _sil(SCENE_MS)

# ── Transcriptions ────────────────────────────────────────────────────────────

TRANSCRIPT_BEAUMONT = """\
[Appel entrant – 11 mars 2025, 14h32]
Conseiller : Association Leucémie Espoir, bonjour, Mathieu Leroux à votre écoute, comment puis-je vous aider ?
Appelant : Oui, bonjour monsieur. Je vous appelle parce que j'ai essayé de faire un virement hier soir pour un don, et je ne suis pas sûr qu'il soit bien parti. Je suis Yves Beaumont, j'habite à Bordeaux.
Conseiller : Bonjour Monsieur Beaumont, pas de souci, je vais vérifier ça pour vous immédiatement. Vous vous souvenez du montant et de l'établissement bancaire depuis lequel vous avez effectué le virement ?
Appelant : Oui, c'était cent cinquante euros, depuis le Crédit Agricole. J'ai fait ça vers vingt heures hier soir.
Conseiller : Très bien. Je vois dans notre système un virement entrant correspondant à cette description, reçu à vingt heures douze, pour cent cinquante euros. C'est bien enregistré sous votre référence donateur.
Appelant : Ah, ça me rassure ! Parce que l'année dernière j'avais eu un problème similaire et le don n'était jamais arrivé.
Conseiller : Je comprends votre inquiétude. Cette fois tout est parfaitement enregistré. Je vous envoie une confirmation par email dès que nous raccrochons, et votre reçu fiscal sera disponible en janvier comme d'habitude.
Appelant : C'est parfait. Et est-ce que je peux mettre à jour mon adresse email en même temps ? J'ai changé de fournisseur, je suis maintenant sur yves.beaumont@orange.fr.
Conseiller : Bien sûr, je mets ça à jour dans les deux minutes. Donc : y-v-e-s point beaumont arobase orange point f-r ?
Appelant : C'est exactement ça.
Conseiller : Parfait, c'est modifié. Vous recevrez la confirmation de don à cette nouvelle adresse. Y a-t-il autre chose que je puisse faire pour vous ?
Appelant : Non, c'est tout. Merci beaucoup pour votre efficacité, c'est vraiment appréciable.
Conseiller : Avec plaisir Monsieur Beaumont. Bonne fin de journée et merci pour votre fidélité à notre association !
Appelant : Merci, au revoir monsieur.
Conseiller : Au revoir !
[Fin d'appel]"""

TRANSCRIPT_MERCIER = """\
[Appel entrant – 15 mars 2025, 09h17]
Conseiller : Association Leucémie Espoir, bonjour, Mathieu Leroux à l'écoute.
Appelante : Bonjour. Je vous appelle au sujet de mon père, Gérard Mercier. Il est décédé le mois dernier, et nous avions trouvé parmi ses affaires une note indiquant qu'il souhaitait que nous fassions un don à votre association en sa mémoire. Je suis Sandrine Mercier, sa fille.
Conseiller : Madame Mercier, je vous présente mes sincères condoléances pour le décès de votre père. Je suis très touché que vous me contactiez dans ce moment difficile pour honorer sa dernière volonté.
Appelante : Merci. Il avait lui-même eu la leucémie il y a dix ans, et votre association l'avait beaucoup soutenu à l'époque. C'était vraiment important pour lui.
Conseiller : C'est très émouvant. Votre père était donateur chez nous depuis longtemps, et ce geste de mémoire lui aurait sûrement beaucoup touché le cœur. Comment souhaiteriez-vous procéder pour ce don en mémoire ?
Appelante : Nous sommes quatre enfants, et on aimerait faire un don groupé de deux mille euros. Est-ce que c'est possible de le faire au nom de notre père ?
Conseiller : Absolument. Nous avons une procédure spécifique pour les dons en mémoire. Je vais vous envoyer un formulaire dédié par email, qui permettra d'associer le don au nom de Gérard Mercier. Vous recevrez également un reçu fiscal au nom de chacun des donateurs si vous le souhaitez.
Appelante : C'est exactement ce qu'on cherchait. Vous pouvez m'envoyer ça à sandrine.mercier@gmail.com ?
Conseiller : Bien sûr. S-a-n-d-r-i-n-e point mercier arobase gmail point com ?
Appelante : C'est ça. Et est-ce qu'il serait possible que son nom apparaisse quelque part dans vos communications ? Qu'il ne soit pas juste un numéro dans une base de données ?
Conseiller : Votre demande me touche beaucoup. Nous avons un espace de mémoire sur notre site où nous publions, avec l'accord de la famille, un petit hommage aux donateurs disparus. Je vous enverrai les informations avec le formulaire. C'est entièrement facultatif bien sûr.
Appelante : Ce serait merveilleux. Merci infiniment pour votre bienveillance.
Conseiller : C'est nous qui vous remercions, Madame Mercier. Votre geste perpétue le souvenir de votre père d'une façon très belle. Je vous envoie tout ça dans l'heure.
Appelante : Merci. Au revoir.
Conseiller : Au revoir Madame Mercier, et encore toutes mes condoléances.
[Fin d'appel]"""


# ── Synthèse ligne par ligne → PCM brut → WAV → MP3 ──────────────────────────

def parse_lines(transcript, voice_appelant):
    result = []
    for raw in transcript.strip().split('\n'):
        line = raw.strip()
        if not line: continue
        if line.startswith('['): result.append((None, None)); continue
        colon = line.index(':') if ':' in line else -1
        if colon < 0: continue
        spk = line[:colon].strip()
        txt = line[colon+1:].strip()
        if not txt: continue
        voice = VOICE_CONSEILLER if spk.startswith('Conseiller') else voice_appelant
        result.append((txt, voice))
    return result

def synth_pcm(text, voice):
    """Appelle OpenAI TTS et retourne du PCM brut 24kHz 16-bit mono."""
    resp = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text,
        response_format="pcm",   # raw PCM — aucune dépendance externe
    )
    return b"".join(resp.iter_bytes())

def build_audio(transcript, voice_appelant, output_path):
    print(f"\nGénération de {output_path}…")
    lines = parse_lines(transcript, voice_appelant)
    all_pcm = b""

    for i, (text, voice) in enumerate(lines):
        if text is None:
            all_pcm += SIL_SCENE
            continue
        label = (text[:68] + "…") if len(text) > 68 else text
        print(f"  [{i+1}/{len(lines)}] {voice:8s} : {label}")
        all_pcm += synth_pcm(text, voice) + SIL
        time.sleep(0.1)   # évite le rate-limit

    # WAV 24kHz 16-bit mono (stdlib Python, zéro dépendance)
    with wave.open(str(output_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(all_pcm)

    dur = len(all_pcm) / (SAMPLE_RATE * 2)
    print(f"  ✅ {output_path}  ({dur:.0f}s — {output_path.stat().st_size//1024} Ko)")


# ── Lettre manuscrite DALL-E 3 ────────────────────────────────────────────────

LETTER_PROMPT = textwrap.dedent("""\
    A photograph of a handwritten letter on slightly aged cream-coloured writing paper,
    lying flat on a wooden table. Written in French by an elderly man in his seventies,
    René Gauthier, using a navy-blue ballpoint pen. The handwriting is slightly shaky and
    irregular — pen pressure varies between lines, some letters lean forward and some are
    more upright, consistent with natural elderly handwriting. Each occurrence of the same
    letter looks slightly different. The letter is dated "Reims, le 5 mars 2025" in the
    top right. It begins "Cher Monsieur ou Madame,". The body mentions a donation of 200
    euros with a cheque, and his granddaughter Emilie who was treated for leukaemia.
    At the bottom there is a real cursive signature reading "René Gauthier" with a short
    underline flourish beneath it. Very faint horizontal pencil guidelines barely visible.
    Photo slightly off-angle (about 3 degrees), taken from directly above with natural
    window light, soft shadow on the left edge, faint fold lines from the envelope.
    High resolution, photorealistic, no digital sharpening artifacts.
""")

def generate_letter_image(output_path):
    print(f"\nGénération de {output_path} (DALL-E 3)…")
    import requests as req
    resp = client.images.generate(
        model="dall-e-3", prompt=LETTER_PROMPT,
        size="1024x1024", quality="hd", n=1,
    )
    output_path.write_bytes(req.get(resp.data[0].url, timeout=60).content)
    print(f"  ✅ {output_path}  ({output_path.stat().st_size//1024} Ko)")


# ── Push vers GitHub ──────────────────────────────────────────────────────────

def push_assets_to_github(token, repo="checkmydev/AssoPilote"):
    print(f"\nPush des assets vers {repo}…")
    base = f"https://api.github.com/repos/{repo}/contents"
    hdr  = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json",
            "User-Agent": "generate-demo-assets", "Content-Type": "application/json"}
    for f in sorted(ASSETS.iterdir()):
        url, sha = f"{base}/assets/{f.name}", None
        try:
            sha = json.loads(urlopen(Request(url, headers=hdr)).read())["sha"]
        except HTTPError as e:
            if e.code != 404: raise
        body = {"message": f"assets: add {f.name}",
                "content": base64.b64encode(f.read_bytes()).decode()}
        if sha: body["sha"] = sha
        commit = json.loads(urlopen(Request(url, data=json.dumps(body).encode(),
                            headers=hdr, method="PUT")).read())["commit"]["sha"][:8]
        print(f"  ✅ assets/{f.name}  (commit {commit})")


# ── Point d'entrée ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_audio(TRANSCRIPT_BEAUMONT, VOICE_APPELANT_M,  ASSETS / "appel_beaumont.wav")
    build_audio(TRANSCRIPT_MERCIER,  VOICE_APPELANTE_F, ASSETS / "appel_mercier.wav")
    generate_letter_image(ASSETS / "lettre_gauthier.jpg")

    print("\n✅ Assets générés.")
    gh = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if gh:
        push_assets_to_github(gh)
    else:
        print("\nPour pousser sur GitHub, relancer avec :")
        print("  set GITHUB_TOKEN=ghp_xxx...")
