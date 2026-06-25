// ============================================================
//  AssoPilot — Edge Function "chat"
//  Proxy sécurisé vers Claude (la clé API reste côté serveur).
//  Pattern PROTOTYPE : tool use sur le snapshot d'emails envoyé par le client.
//  En PRODUCTION : remplacer runTool() par des requêtes Supabase (emails
//  ingérés depuis Outlook) + recherche sémantique pgvector.
//
//  Déploiement :
//    supabase functions deploy chat
//  Secrets :
//    supabase secrets set ANTHROPIC_API_KEY=sk-ant-...
//    (optionnel) supabase secrets set ANTHROPIC_MODEL=claude-sonnet-4-6
// ============================================================
import Anthropic from "npm:@anthropic-ai/sdk@^0.65.0";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// ── Outils exposés à Claude ─────────────────────────────────
const tools = [
  {
    name: "rechercher_emails",
    description: "Recherche et filtre les emails de la boîte de réception. Tous les filtres sont optionnels et combinables.",
    input_schema: {
      type: "object",
      properties: {
        statut: { type: "string", enum: ["traite", "non_traite", "tous"], description: "Filtrer par statut de traitement." },
        type: { type: "string", description: "Filtrer par type d'email (ex: 'Duplicata reçu fiscal', 'Réclamation RGPD'). Correspondance partielle." },
        donateur: { type: "string", description: "Nom (ou partie) du donateur." },
        expediteur: { type: "string", description: "Nom (ou partie) de l'expéditeur." },
      },
    },
  },
  {
    name: "statistiques_emails",
    description: "Renvoie des statistiques agrégées : total, traités, non traités, et répartition par type.",
    input_schema: { type: "object", properties: {} },
  },
];

function runTool(name: string, input: any, emails: any[]) {
  if (name === "statistiques_emails") {
    const parType: Record<string, number> = {};
    let traites = 0;
    for (const e of emails) {
      parType[e.type] = (parType[e.type] || 0) + 1;
      if (e.handled) traites++;
    }
    return { total: emails.length, traites, non_traites: emails.length - traites, par_type: parType };
  }
  if (name === "rechercher_emails") {
    const inc = (v: any, q: string) => String(v || "").toLowerCase().includes(q.toLowerCase());
    let res = emails;
    if (input.statut === "traite") res = res.filter((e) => e.handled);
    else if (input.statut === "non_traite") res = res.filter((e) => !e.handled);
    if (input.type) res = res.filter((e) => inc(e.type, input.type));
    if (input.donateur) res = res.filter((e) => inc(e.donor, input.donateur));
    if (input.expediteur) res = res.filter((e) => inc(e.from, input.expediteur));
    return { count: res.length, emails: res.slice(0, 40) };
  }
  return { error: "outil inconnu" };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

  try {
    // Lecture par requête (et non au boot) : un changement de secret s'applique sans redéploiement
    const apiKey = (Deno.env.get("ANTHROPIC_API_KEY") ?? "").trim();
    if (!apiKey) return json({ error: "ANTHROPIC_API_KEY non configurée." }, 500);
    const MODEL = Deno.env.get("ANTHROPIC_MODEL") ?? "claude-opus-4-8";
    const anthropic = new Anthropic({ apiKey });
    const { messages = [], emails = [], isAdmin = false } = await req.json();

    const system =
      "Tu es l'assistant d'AssoPilot, un outil de gestion des donateurs d'une association. " +
      "Tu réponds en français, de façon concise et factuelle, aux questions sur les emails de la boîte de réception et leur statut. " +
      "Utilise les outils pour obtenir les données avant de répondre — ne devine jamais. " +
      "Si une information n'est pas disponible, dis-le simplement. " +
      (isAdmin ? "L'utilisateur est ADMIN (vision sur toute l'équipe)." : "L'utilisateur est un agent opérationnel.");

    const convo: any[] = [...messages];
    for (let step = 0; step < 6; step++) {
      const resp = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 1024,
        system,
        tools,
        messages: convo,
      });

      if (resp.stop_reason === "tool_use") {
        const toolResults = resp.content
          .filter((b: any) => b.type === "tool_use")
          .map((b: any) => ({
            type: "tool_result",
            tool_use_id: b.id,
            content: JSON.stringify(runTool(b.name, b.input, emails)),
          }));
        convo.push({ role: "assistant", content: resp.content });
        convo.push({ role: "user", content: toolResults });
        continue;
      }

      const text = resp.content.filter((b: any) => b.type === "text").map((b: any) => b.text).join("").trim();
      return json({ answer: text || "(réponse vide)" });
    }
    return json({ answer: "Désolé, je n'ai pas pu aboutir (trop d'étapes)." });
  } catch (e) {
    return json({ error: String(e?.message ?? e) }, 500);
  }
});
