import { createClient } from "jsr:@supabase/supabase-js@2";
import { criarTratadorDoRedirecionador } from "./servidor.ts";

Deno.serve(criarTratadorDoRedirecionador({
  supabase: createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  ),
  ambiente: Deno.env,
}));
