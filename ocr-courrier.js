/**
 * ocr-courrier.js
 * Traitement de courrier papier scanné (PDF / images) avec l'API Claude.
 *
 * Flux : PDF → Claude Vision (extraction OCR + classification) → Claude (rédaction réponse)
 *
 * Prérequis :
 *   npm install @anthropic-ai/sdk
 *
 * Usage :
 *   ANTHROPIC_API_KEY=sk-ant-xxx node ocr-courrier.js ./scans/lettre.pdf
 *   ANTHROPIC_API_KEY=sk-ant-xxx node ocr-courrier.js ./scans/cheque.jpg
 */

import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// Formats supportés → media type MIME
const MIME_MAP = {
  '.pdf': 'application/pdf',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
};

async function processCourrierFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeType = MIME_MAP[ext];
  if (!mimeType) throw new Error(`Format non supporté : ${ext}`);

  console.log(`\n📄 Fichier : ${path.basename(filePath)}`);
  console.log(`   Type    : ${mimeType}`);

  const fileData = fs.readFileSync(filePath);
  const base64 = fileData.toString('base64');

  // ── Étape 1 : Extraction OCR + classification ─────────────────────────────
  console.log('\n🔍 Étape 1 — Extraction OCR et analyse du document…');

  const extractionResponse = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 2048,
    messages: [{
      role: 'user',
      content: [
        {
          type: mimeType === 'application/pdf' ? 'document' : 'image',
          source: { type: 'base64', media_type: mimeType, data: base64 },
        },
        {
          type: 'text',
          text: `Tu es l'assistant du service donateurs d'une association caritative française.

Analyse ce document et retourne UNIQUEMENT un objet JSON valide (sans markdown, sans balises) :
{
  "typeDocument": "lettre_manuscrite" | "lettre_imprimee" | "cheque" | "formulaire" | "releve_bancaire" | "autre",
  "qualiteOCR": "excellente" | "bonne" | "moyenne" | "difficile",
  "expediteur": {
    "nom": "Prénom Nom ou null",
    "adresse": "adresse complète ou null",
    "telephone": "numéro ou null",
    "email": "email ou null"
  },
  "contenuBrut": "texte tel que lu par l'OCR, avec artefacts éventuels",
  "contenuNettoye": "texte corrigé, accents rétablis, artefacts OCR supprimés",
  "intentionPrincipale": "don" | "demande_recu_fiscal" | "changement_coordonnees" | "reclamation" | "demande_info" | "resiliation" | "don_en_memoire" | "autre",
  "montant": null,
  "numeroCheque": null,
  "resumeAction": "Une phrase décrivant précisément l'action requise par le service donateurs",
  "priorite": "normale" | "urgente" | "sensible"
}`,
        },
      ],
    }],
  });

  let extraction;
  try {
    extraction = JSON.parse(extractionResponse.content[0].text.trim());
  } catch {
    throw new Error('Réponse OCR non parseable : ' + extractionResponse.content[0].text);
  }

  console.log(`   ✅ Type     : ${extraction.typeDocument}`);
  console.log(`   ✅ Qualité  : ${extraction.qualiteOCR}`);
  console.log(`   ✅ Intention: ${extraction.intentionPrincipale}`);
  if (extraction.expediteur?.nom) console.log(`   ✅ Expéditeur: ${extraction.expediteur.nom}`);

  // ── Étape 2 : Rédaction de la réponse ────────────────────────────────────
  console.log('\n✉️  Étape 2 — Rédaction de la réponse…');

  const reponseResponse = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 1024,
    messages: [{
      role: 'user',
      content: `Tu travailles au service donateurs de l'Association Leucémie Espoir.

Voici le résumé d'un courrier papier reçu et analysé :
${JSON.stringify(extraction, null, 2)}

Rédige une réponse appropriée :
- Si l'expéditeur a un email connu : rédige un email de réponse
- Sinon : rédige un courrier papier formel à expédier

Ton, chaleureux et professionnel. Signe : "Mathieu Leroux — Service Donateurs"
Retourne UNIQUEMENT le texte de la réponse (objet / corps / signature), sans commentaire.`,
    }],
  });

  const reponse = reponseResponse.content[0].text.trim();
  console.log(`   ✅ Réponse générée (${reponse.length} caractères)`);

  return { fichier: path.basename(filePath), extraction, reponse };
}

// ── Point d'entrée ─────────────────────────────────────────────────────────

const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage : node ocr-courrier.js <chemin_vers_pdf_ou_image>');
  console.error('Exemple : node ocr-courrier.js ./scans/lettre_gauthier.pdf');
  process.exit(1);
}

if (!fs.existsSync(filePath)) {
  console.error(`Fichier introuvable : ${filePath}`);
  process.exit(1);
}

processCourrierFile(filePath)
  .then(({ extraction, reponse }) => {
    console.log('\n══════════════════════════════════════════════');
    console.log('EXTRACTION OCR :');
    console.log(JSON.stringify(extraction, null, 2));
    console.log('\n📧 RÉPONSE GÉNÉRÉE :');
    console.log('──────────────────────────────────────────────');
    console.log(reponse);
    console.log('══════════════════════════════════════════════');
  })
  .catch(err => {
    console.error('\n❌ Erreur :', err.message);
    process.exit(1);
  });
