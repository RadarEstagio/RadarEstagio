import { createClient } from "jsr:@supabase/supabase-js@2";
import { dispararEntregaImediata } from "./entrega_imediata.ts";
import { criarTratadorDoWebhook } from "./servidor.ts";

Deno.serve(criarTratadorDoWebhook({
  supabase: createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  ),
  ambiente: Deno.env,
  agora: () => new Date(),
  enviar: fetch,
  dispararEntregaImediata,
}));
