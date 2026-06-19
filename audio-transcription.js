/**
 * audio-transcription.js
 * Transcription d'enregistrements téléphoniques + traitement par Claude.
 *
 * Flux : MP3/WAV → Whisper (OpenAI STT) → Claude Opus (analyse + réponse)
 *
 * Prérequis :
 *   npm install @anthropic-ai/sdk openai
 *
 * Usage :
 *   ANTHROPIC_API_KEY=sk-ant-xxx OPENAI_API_KEY=sk-xxx node audio-transcription.js ./appels/appel_14h32.mp3
 *
 * Formats audio supportés par Whisper : mp3, mp4, mpeg, mpga, m4a, wav, webm
 */

import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const openai    = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function processPhoneCall(audioPath) {
  console.log(`\n🎙️  Fichier audio : ${path.basename(audioPath)}`);

  // ── Étape 1 : Transcription audio via Whisper ─────────────────────────────
  console.log('\n🔊 Étape 1 — Transcription Whisper (OpenAI)…');

  const audioStream = fs.createReadStream(audioPath);

  const transcription = await openai.audio.transcriptions.create({
    file: audioStream,
    model: 'whisper-1',
    language: 'fr',
    response_format: 'verbose_json',
    timestamp_granularities: ['segment'],
  });

  const dureeSec = Math.round(transcription.duration);
  const dureeStr = dureeSec >= 60
    ? `${Math.floor(dureeSec / 60)} min ${dureeSec % 60}s`
    : `${dureeSec}s`;

  console.log(`   ✅ Durée    : ${dureeStr}`);
  console.log(`   ✅ Segments : ${transcription.segments?.length ?? 'N/A'}`);
  console.log(`   ✅ Texte (${transcription.text.length} caractères)`);

  // ── Étape 2 : Analyse de la transcription par Claude ─────────────────────
  console.log('\n🤖 Étape 2 — Analyse par Claude Opus…');

  const analysisResponse = await anthropic.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 2048,
    messages: [{
      role: 'user',
      content: `Tu es l'assistant du service donateurs de l'Association Leucémie Espoir.

Voici la transcription brute d'un appel téléphonique entrant (durée : ${dureeStr}) :

"""
${transcription.text}
"""

Analyse cet appel et retourne UNIQUEMENT un objet JSON valide (sans markdown, sans balises) :
{
  "appelant": {
    "nom": "Prénom Nom ou null",
    "telephone": "numéro ou null",
    "email": "email ou null",
    "adresse": "adresse ou null"
  },
  "intentionPrincipale": "don" | "demande_recu_fiscal" | "changement_coordonnees" | "demande_info" | "reclamation" | "don_en_memoire" | "resiliation" | "urgence" | "autre",
  "resumeAppel": "Résumé factuel en 2-3 phrases",
  "actionsRequises": ["action concrète 1", "action 2"],
  "informationsCollectees": { "cle": "valeur" },
  "sensibilite": "normal" | "sensible" | "urgent",
  "transcriptionFormattee": "Transcript reformaté avec 'Conseiller :' et 'Appelant :' en alternance"
}`,
    }],
  });

  let analyse;
  try {
    analyse = JSON.parse(analysisResponse.content[0].text.trim());
  } catch {
    throw new Error('Réponse analyse non parseable : ' + analysisResponse.content[0].text);
  }

  console.log(`   ✅ Intention   : ${analyse.intentionPrincipale}`);
  console.log(`   ✅ Sensibilité : ${analyse.sensibilite}`);
  if (analyse.appelant?.nom) console.log(`   ✅ Appelant    : ${analyse.appelant.nom}`);

  // ── Étape 3 : Génération de l'email de suivi ─────────────────────────────
  console.log('\n📧 Étape 3 — Génération de l\'email de suivi…');

  const followUpResponse = await anthropic.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 1024,
    messages: [{
      role: 'user',
      content: `Suite à cet appel téléphonique :
${JSON.stringify(analyse, null, 2)}

Rédige un email de suivi à envoyer à l'appelant :
- Confirme les points évoqués pendant l'appel
- Récapitule les actions prises / en cours
- Adapte le ton à la sensibilité de la situation (${analyse.sensibilite})
- Signe : "Mathieu Leroux — Service Donateurs"

Retourne UNIQUEMENT le texte de l'email (objet + corps + signature), sans commentaire.`,
    }],
  });

  const emailSuivi = followUpResponse.content[0].text.trim();
  console.log(`   ✅ Email de suivi généré (${emailSuivi.length} caractères)`);

  return {
    fichier: path.basename(audioPath),
    duree: dureeStr,
    transcriptionBrute: transcription.text,
    analyse,
    emailSuivi,
  };
}

// ── Point d'entrée ─────────────────────────────────────────────────────────

const audioPath = process.argv[2];

if (!audioPath) {
  console.error('Usage : node audio-transcription.js <chemin_audio>');
  console.error('Exemple : node audio-transcription.js ./appels/appel_14h32.mp3');
  process.exit(1);
}

if (!fs.existsSync(audioPath)) {
  console.error(`Fichier introuvable : ${audioPath}`);
  process.exit(1);
}

processPhoneCall(audioPath)
  .then(({ duree, transcriptionBrute, analyse, emailSuivi }) => {
    console.log('\n══════════════════════════════════════════════');
    console.log(`DURÉE : ${duree}`);
    console.log('\nTRANSCRIPTION BRUTE :');
    console.log('──────────────────────────────────────────────');
    console.log(transcriptionBrute);
    console.log('\nANALYSE :');
    console.log(JSON.stringify(analyse, null, 2));
    console.log('\n📧 EMAIL DE SUIVI :');
    console.log('──────────────────────────────────────────────');
    console.log(emailSuivi);
    console.log('══════════════════════════════════════════════');
  })
  .catch(err => {
    console.error('\n❌ Erreur :', err.message);
    process.exit(1);
  });
