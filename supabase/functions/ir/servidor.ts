import { type SupabaseClient } from "jsr:@supabase/supabase-js@2";
import { redirecionarPara, tokenDaRequisicao } from "./redirecionamento.ts";
import { type PerfilDoDestinatario } from "../_shared/privacidade.ts";
import { destinoDoEnvio, type EnvioDaVaga } from "./navegacao.ts";

export interface VariaveisDeAmbiente {
  get: (nome: string) => string | undefined;
}

export interface DependenciasDoRedirecionador {
  supabase: SupabaseClient;
  ambiente: VariaveisDeAmbiente;
}

export function criarTratadorDoRedirecionador(
  dependencias: DependenciasDoRedirecionador,
): (requisicao: Request) => Promise<Response> {
  const { supabase, ambiente } = dependencias;
  const urlDaLandingConfigurada = ambiente.get("URL_DA_LANDING");
  if (!urlDaLandingConfigurada) {
    throw new Error(
      "URL_DA_LANDING é obrigatória: sem ela o token inválido não tem para onde ir",
    );
  }
  const urlDaLanding: string = urlDaLandingConfigurada;

  async function envioDoToken(token: string): Promise<EnvioDaVaga | null> {
    const { data, error } = await supabase
      .from("envios")
      .select(
        "perfil_id, vaga_id, vagas (url), perfis (user_id, ativo, excluida_em, telegram_chat_id)",
      )
      .eq("token", token)
      .maybeSingle();
    if (error) throw error;
    if (!data) return null;
    const vaga = data.vagas as unknown as { url: string } | null;
    const perfil = data.perfis as unknown as PerfilDoDestinatario | null;
    if (!vaga || !perfil) return null;
    return {
      perfilId: data.perfil_id,
      userId: perfil.user_id,
      vagaId: data.vaga_id,
      url: vaga.url,
      perfil,
    };
  }

  async function registrarVagaAberta(envio: EnvioDaVaga): Promise<void> {
    const { error } = await supabase.from("eventos_produto").insert({
      nome: "vaga_aberta",
      origem: "telegram",
      user_id: envio.userId,
      perfil_id: envio.perfilId,
      vaga_id: envio.vagaId,
    });
    if (error) throw error;
  }

  async function destinoDoToken(
    url: string,
    registrar: boolean,
  ): Promise<string> {
    const token = tokenDaRequisicao(url);
    if (!token) return urlDaLanding;
    const envio = await envioDoToken(token);
    return destinoDoEnvio(envio, urlDaLanding, registrar, registrarVagaAberta);
  }

  return async (requisicao) => {
    if (requisicao.method !== "GET" && requisicao.method !== "HEAD") {
      return new Response(null, { status: 405 });
    }
    try {
      const destino = await destinoDoToken(
        requisicao.url,
        requisicao.method === "GET",
      );
      return redirecionarPara(destino);
    } catch (erro) {
      console.error("falha ao redirecionar para a vaga", erro);
      return redirecionarPara(urlDaLanding);
    }
  };
}
