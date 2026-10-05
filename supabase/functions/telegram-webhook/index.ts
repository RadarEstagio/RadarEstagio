import { createClient } from "jsr:@supabase/supabase-js@2";
import { type PerfilDoDestinatario, podeProcessarInteracao } from "../_shared/privacidade.ts";
import {
  type AtualizacaoDoTelegram,
  chatIdDaMensagem,
  conversaPrivada,
  extrairPedidoDeVinculo,
  RESPOSTA_SOMENTE_EM_PRIVADO,
  textoDaMensagem,
} from "./vinculo.ts";
import { processarVinculo, type VinculoRealizado } from "./processar_vinculo.ts";
import { processarMensagemLivre } from "./processar_mensagem_livre.ts";
import {
  type ConsultaDeFeedback,
  eventoDoFeedback,
  extrairClique,
  tecladoDeFeedback,
} from "./feedback.ts";
import { type EnvioDoToken, responderConsultaDeFeedback } from "./processar_feedback.ts";
import { dispararEntregaImediata } from "./entrega_imediata.ts";
import {
  cliqueQuePrecisaDeResposta,
  interpretarCorpo,
  responderCliqueSemTratamento,
} from "./atualizacao.ts";

const CABECALHO_DO_SEGREDO = "x-telegram-bot-api-secret-token";
const CODIGO_DE_VALOR_DUPLICADO = "23505";
const LANDING_PADRAO = "https://radarestagio.com";

const tokenDoBot = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const segredoDoWebhook = Deno.env.get("TELEGRAM_WEBHOOK_SECRET")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function responderNoTelegram(
  chatId: string,
  texto: string,
): Promise<void> {
  await fetch(`https://api.telegram.org/bot${tokenDoBot}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: texto }),
  });
}

async function vincularChat(
  token: string,
  chatId: string,
): Promise<VinculoRealizado> {
  const { data, error } = await supabase
    .from("perfis")
    .update({
      telegram_chat_id: chatId,
      token_vinculo: crypto.randomUUID(),
      atualizado_em: new Date().toISOString(),
    })
    .eq("token_vinculo", token)
    .is("excluida_em", null)
    .select("id");
  if (error?.code === CODIGO_DE_VALOR_DUPLICADO) {
    return { resultado: "chat_de_outra_conta", perfilId: null };
  }
  if (error) throw error;
  if (data.length === 1) return { resultado: "vinculado", perfilId: data[0].id };
  return {
    resultado: (await chatJaVinculado(chatId)) ? "chat_ja_vinculado" : "token_ja_usado",
    perfilId: null,
  };
}

async function chatJaVinculado(chatId: string): Promise<boolean> {
  const { data, error } = await supabase
    .from("perfis")
    .select("id")
    .eq("telegram_chat_id", chatId)
    .maybeSingle();
  if (error) throw error;
  return data !== null;
}

async function perfilDoChat(chatId: string): Promise<string | null> {
  const { data, error } = await supabase
    .from("perfis")
    .select("id")
    .eq("telegram_chat_id", chatId)
    .is("excluida_em", null)
    .maybeSingle();
  if (error) throw error;
  return data?.id ?? null;
}

function enderecoDaConta(): string {
  const landing = Deno.env.get("URL_DA_LANDING") ?? LANDING_PADRAO;
  return `${landing.replace(/\/+$/, "")}/?conta`;
}

async function encaminharParaOperacao(texto: string): Promise<boolean> {
  const chatDeOperacao = Deno.env.get("TELEGRAM_CHAT_ID");
  if (!chatDeOperacao) {
    console.warn("TELEGRAM_CHAT_ID ausente: a mensagem livre não chega ao chat de operação");
    return false;
  }
  await chamarTelegram("sendMessage", { chat_id: chatDeOperacao, text: texto });
  return true;
}

async function reivindicarEntregaImediata(perfilId: string): Promise<boolean> {
  const { data, error } = await supabase
    .from("perfis")
    .update({ entrega_imediata_disparada_em: new Date().toISOString() })
    .eq("id", perfilId)
    .is("entrega_imediata_disparada_em", null)
    .select("id");
  if (error) throw error;
  return data.length === 1;
}

async function tratarAtualizacao(
  atualizacao: AtualizacaoDoTelegram,
): Promise<void> {
  const pedido = extrairPedidoDeVinculo(atualizacao);
  if (!pedido) {
    const chatId = chatIdDaMensagem(atualizacao);
    if (!chatId) return;
    if (!conversaPrivada(atualizacao)) {
      await responderNoTelegram(chatId, RESPOSTA_SOMENTE_EM_PRIVADO);
      return;
    }
    await processarMensagemLivre(
      { chatId, texto: textoDaMensagem(atualizacao) },
      { perfilDoChat, responder: responderNoTelegram, encaminharParaOperacao },
      enderecoDaConta(),
    );
    return;
  }
  await processarVinculo(pedido, {
    vincularChat,
    responder: responderNoTelegram,
    reivindicarEntregaImediata,
    dispararEntregaImediata,
  });
}

async function chamarTelegram(metodo: string, corpo: unknown): Promise<void> {
  const resposta = await fetch(`https://api.telegram.org/bot${tokenDoBot}/${metodo}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(corpo),
  });
  const resultado = await resposta.json();
  if (!resposta.ok || !resultado.ok) throw new Error(`Telegram recusou ${metodo}`);
}

async function envioDoToken(
  token: string,
  chatId: string,
): Promise<EnvioDoToken | null> {
  const { data, error } = await supabase
    .from("envios")
    .select(
      "perfil_id, vaga_id, vagas (titulo, empresa), perfis (user_id, ativo, excluida_em, telegram_chat_id)",
    )
    .eq("token", token)
    .maybeSingle();
  if (error) throw error;
  if (!data) return null;
  const perfil = data.perfis as unknown as PerfilDoDestinatario | null;
  if (!perfil || !podeProcessarInteracao(perfil, chatId)) return null;
  const vaga = data.vagas as unknown as { titulo: string; empresa: string } | null;
  if (!vaga) return null;
  return {
    titulo: vaga.titulo,
    empresa: vaga.empresa,
    perfilId: data.perfil_id,
    userId: perfil.user_id,
    vagaId: data.vaga_id,
  };
}

async function registrarFeedback(
  envio: EnvioDoToken,
  acao: string,
): Promise<void> {
  const evento = eventoDoFeedback(acao);
  if (!evento) return;
  const { error } = await supabase.from("eventos_produto").insert({
    ...evento,
    origem: "telegram",
    user_id: envio.userId,
    perfil_id: envio.perfilId,
    vaga_id: envio.vagaId,
  });
  if (error) throw error;
}

async function perguntarOMotivo(consulta: ConsultaDeFeedback, envio: EnvioDoToken): Promise<void> {
  await chamarTelegram("sendMessage", {
    chat_id: consulta.chatId,
    text: `${envio.titulo} — ${envio.empresa}\n\nEssa vaga serviu para você?`,
    reply_markup: { inline_keyboard: tecladoDeFeedback(consulta.token) },
  });
}

async function encerrarPergunta(consulta: ConsultaDeFeedback): Promise<void> {
  await chamarTelegram("deleteMessage", {
    chat_id: consulta.chatId,
    message_id: consulta.mensagemId,
  });
}

Deno.serve(async (requisicao) => {
  if (requisicao.method !== "POST") return new Response(null, { status: 405 });
  if (requisicao.headers.get(CABECALHO_DO_SEGREDO) !== segredoDoWebhook) {
    return new Response(null, { status: 401 });
  }
  const atualizacao = await interpretarCorpo(requisicao);
  if (!atualizacao) return new Response(null, { status: 200 });
  const consulta = extrairClique(atualizacao);
  if (!consulta) {
    const cliqueSemTratamento = cliqueQuePrecisaDeResposta(atualizacao);
    if (cliqueSemTratamento) {
      return await responderCliqueSemTratamento(
        cliqueSemTratamento,
        (id) => chamarTelegram("answerCallbackQuery", { callback_query_id: id }),
      );
    }
  }
  if (consulta) {
    return await responderConsultaDeFeedback(consulta, {
      envioDoToken,
      registrarFeedback,
      perguntarOMotivo,
      encerrarPergunta,
    }, async (aviso) => {
      await chamarTelegram("answerCallbackQuery", {
        callback_query_id: consulta.id,
        text: aviso || undefined,
      });
    });
  }

  try {
    await tratarAtualizacao(atualizacao);
  } catch (erro) {
    console.error("falha ao tratar atualização do telegram", erro);
  }
  return new Response(null, { status: 200 });
});
