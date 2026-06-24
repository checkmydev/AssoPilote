"""
get-timestamps.py
Extrait les timestamps mot-par-mot avec Whisper et les mappe
sur les lignes de dialogue du transcript formaté.

Sortie : deux tableaux JS prêts à coller dans le HTML.

Usage (depuis dossier Etienne) :
    python get-timestamps.py
"""

import pathlib, sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

import whisper as _w
print("Chargement du modele Whisper medium...")
model = _w.load_model("medium")

ASSETS = pathlib.Path("assets")

# ── Lignes de dialogue (correspondant exactement au transcript dans le HTML) ──

LINES_13 = [
    None,   # ligne système — pas de timestamp
    "Association Leucémie Espoir, bonjour, Mathieu Leroux à votre écoute. Comment puis-je vous aider ?",
    "Oui, bonjour Monsieur. Je vous appelle parce que j'ai essayé de faire un virement hier soir pour un don et je ne suis pas sûr qu'il soit bien parti. Je suis Yves Beaumont, j'habite à Bordeaux.",
    "Bonjour Monsieur Beaumont, pas de souci, je vais vérifier ça pour vous immédiatement. Vous vous souvenez du montant et de l'établissement bancaire depuis lequel vous avez effectué le virement ?",
    "Oui, c'était 150 euros depuis le Crédit Agricole. J'ai fait ça vers 20 heures hier soir.",
    "Très bien. Je vois dans notre système un virement entrant correspondant à cette description, reçu à 20h12 pour 150 euros. C'est bien enregistré sous votre référence donateur.",
    "Ah, ça me rassure. Parce que l'année dernière j'avais eu un problème similaire et le don n'était jamais arrivé.",
    "Je comprends votre inquiétude. Cette fois tout est parfaitement enregistré. Je vous envoie une confirmation par e-mail dès que nous raccrochons et votre reçu fiscal sera disponible en janvier comme d'habitude.",
    "C'est parfait. Et est-ce que je peux mettre à jour mon adresse e-mail en même temps ? J'ai changé de fournisseur, je suis maintenant sur yves.beaumont@orange.fr.",
    "Bien sûr, je mets ça à jour dans les deux minutes. Donc yves.beaumont@orange.fr ?",
    "C'est exactement ça.",
    "Parfait, c'est modifié. Vous recevrez la confirmation de don à cette nouvelle adresse. Y a-t-il autre chose que je puisse faire pour vous ?",
    "Non, c'est tout. Merci beaucoup pour votre efficacité, c'est vraiment appréciable.",
    "Avec plaisir, Monsieur Beaumont. Bonne fin de journée et merci pour votre fidélité à notre association !",
    "Merci. Au revoir, Monsieur.",
    "Au revoir !",
]

LINES_14 = [
    None,
    "Association Leucémie Espoir, bonjour, Mathieu Leroux à l'écoute.",
    "Bonjour, je vous appelle au sujet de mon père, Gérard Mercier. Il est décédé le mois dernier et nous avions trouvé parmi ses affaires une note indiquant qu'il souhaitait que nous fassions un don à votre association en sa mémoire. Je suis Sandrine Mercier, sa fille.",
    "Madame Mercier, je vous présente mes sincères condoléances pour le décès de votre père. Je suis très touché que vous me contactiez dans ce moment difficile pour honorer sa dernière volonté.",
    "Merci. Il avait lui-même eu la leucémie il y a dix ans et votre association l'avait beaucoup soutenu à l'époque. C'était vraiment important pour lui.",
    "C'est très émouvant. Votre père était donateur chez nous depuis longtemps et ce geste de mémoire lui aurait sûrement beaucoup touché le cœur. Comment souhaiteriez-vous procéder pour ce don en mémoire ?",
    "Nous sommes quatre enfants et on aimerait faire un don groupé de 2 000 euros. Est-ce que c'est possible de le faire au nom de notre père ?",
    "Absolument. Nous avons une procédure spécifique pour les dons en mémoire. Je vais vous envoyer un formulaire dédié par e-mail qui permettra d'associer le don au nom de Gérard Mercier. Vous recevrez également un reçu fiscal au nom de chacun des donateurs si vous le souhaitez.",
    "C'est exactement ce qu'on cherchait. Vous pouvez m'envoyer ça à sandrine.mercier@gmail.com ?",
    "Bien sûr. sandrine.mercier@gmail.com ?",
    "C'est ça. Et est-ce qu'il serait possible que son nom apparaisse quelque part dans vos communications, qu'il ne soit pas juste un numéro dans une base de données ?",
    "Votre demande me touche beaucoup. Nous avons un espace de mémoire sur notre site où nous publions, avec l'accord de la famille, un petit hommage aux donateurs disparus. Je vous enverrai les informations avec le formulaire. C'est entièrement facultatif, bien sûr.",
    "Ce serait merveilleux. Merci infiniment pour votre bienveillance.",
    "C'est nous qui vous remercions, Madame Mercier. Votre geste perpétue le souvenir de votre père d'une façon très belle. Je vous envoie tout ça dans l'heure.",
    "Merci. Au revoir.",
    "Au revoir Madame Mercier, et encore toutes mes condoléances.",
]

# ────────────────────────────────────────────────────────────────────────────

def normalize(txt):
    return re.sub(r"[^\w]", "", txt.lower())

def get_flat_words(audio_path):
    print(f"  Whisper word_timestamps=True sur {audio_path.name}...")
    r = model.transcribe(str(audio_path), language="fr", word_timestamps=True)
    flat = []
    for seg in r["segments"]:
        for w in seg.get("words", []):
            flat.append({"w": normalize(w["word"]), "t": round(w["start"], 2)})
    print(f"  {len(flat)} mots avec timestamps.")
    return flat

def find_start(flat_words, line_text, search_from=0):
    """
    Cherche les 3 premiers mots normalisés de line_text dans flat_words
    à partir de l'index search_from. Retourne le timestamp du 1er mot trouvé.
    """
    targets = [normalize(w) for w in line_text.split()[:3] if normalize(w)]
    if not targets:
        return flat_words[search_from]["t"] if flat_words else 0

    nw = len(flat_words)
    for i in range(search_from, nw - len(targets) + 1):
        if all(flat_words[i + j]["w"] == targets[j] for j in range(len(targets))):
            return flat_words[i]["t"]

    # Fallback : cherche juste le 1er mot sans contrainte de position
    t0 = normalize(line_text.split()[0]) if line_text.split() else ""
    for i in range(search_from, nw):
        if flat_words[i]["w"] == t0:
            return flat_words[i]["t"]

    # Dernier recours : proportionnel
    return None

def compute_times(flat_words, lines):
    times = []
    cursor = 0
    for line in lines:
        if line is None:
            times.append(None)
            continue
        t = find_start(flat_words, line, cursor)
        if t is None:
            # Proportionnel si pas trouvé
            t = flat_words[cursor]["t"] if cursor < len(flat_words) else 0
        times.append(t)
        # Avance le curseur au-delà de ce timestamp pour la prochaine ligne
        while cursor < len(flat_words) and flat_words[cursor]["t"] < t:
            cursor += 1
    return times

# ── Email 13 ─────────────────────────────────────────────────────────────────

print("\n=== Email 13 — Yves Beaumont ===")
flat13 = get_flat_words(ASSETS / "Yves Beaumont.wav")
times13 = compute_times(flat13, LINES_13)
print("Timestamps email 13 :")
for i, (line, t) in enumerate(zip(LINES_13, times13)):
    label = "(sys)" if line is None else (line[:50] + "…" if len(line or "") > 50 else line)
    print(f"  [{i:2d}] {str(t):>8}  {label}")

# ── Email 14 ─────────────────────────────────────────────────────────────────

print("\n=== Email 14 — Sandrine Mercier ===")
flat14 = get_flat_words(ASSETS / "Gérard Mercier.wav")
times14 = compute_times(flat14, LINES_14)
print("Timestamps email 14 :")
for i, (line, t) in enumerate(zip(LINES_14, times14)):
    label = "(sys)" if line is None else (line[:50] + "…" if len(line or "") > 50 else line)
    print(f"  [{i:2d}] {str(t):>8}  {label}")

# ── Sortie JS ─────────────────────────────────────────────────────────────────

def js_arr(times):
    parts = []
    for t in times:
        parts.append("null" if t is None else str(t))
    return "[" + ",".join(parts) + "]"

print("\n\n=== COLLER DANS LE HTML ===")
print(f"\n// Email 13 — transcriptTimes:")
print(f"transcriptTimes:{js_arr(times13)},")
print(f"\n// Email 14 — transcriptTimes:")
print(f"transcriptTimes:{js_arr(times14)},")
