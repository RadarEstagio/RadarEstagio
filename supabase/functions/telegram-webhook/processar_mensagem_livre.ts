import { CONTATO_DA_EQUIPE, RESPOSTA_CHAT_JA_VINCULADO, RESPOSTA_SEM_TOKEN } from "./vinculo.ts";

const LIMITE_DO_TELEGRAM_EM_UNIDADES_UTF16 = 4096;
const RETICENCIAS = "…";

export interface MensagemLivre {
  chatId: string;
  texto: string | null;
}

export interface PerfilDoChat {
  id: string;
  ativo: boolean;
}

export interface OperacoesDeMensagemLivre {
  perfilDoChat: (chatId: string) => Promise<PerfilDoChat | null>;
  responder: (chatId: string, texto: string) => Promise<void>;
  encaminharParaOperacao: (texto: string) => Promise<boolean>;
}

function contatos(urlDaConta: string): string {
  return `Escreva para ${CONTATO_DA_EQUIPE} ou entre na sua conta: ${urlDaConta}`;
}

function cortarEmUnidadesUtf16(texto: string, limite: number): string {
  if (texto.length <= limite) return texto;
  let cortado = "";
  for (const caractere of texto) {
    if (cortado.length + caractere.length > limite - RETICENCIAS.length) break;
    cortado += caractere;
  }
  return cortado + RETICENCIAS;
}

function textoParaOperacao(perfilId: string, texto: string): string {
  const cabecalho = `Mensagem de um usuário pelo bot (perfil ${perfilId}):\n\n`;
  return cabecalho +
    cortarEmUnidadesUtf16(texto, LIMITE_DO_TELEGRAM_EM_UNIDADES_UTF16 - cabecalho.length);
}

async function perfilOuNulo(
  operacoes: OperacoesDeMensagemLivre,
  chatId: string,
): Promise<PerfilDoChat | null | "indisponivel"> {
  try {
    return await operacoes.perfilDoChat(chatId);
  } catch (erro) {
    console.error("falha ao consultar o perfil do chat na mensagem livre", erro);
    return "indisponivel";
  }
}

async function encaminhou(
  operacoes: OperacoesDeMensagemLivre,
  texto: string,
): Promise<boolean> {
  try {
    return await operacoes.encaminharParaOperacao(texto);
  } catch (erro) {
    console.error("falha ao encaminhar mensagem livre ao chat de operação", erro);
    return false;
  }
}

function respostaAoComando(perfil: PerfilDoChat, urlDaConta: string): string {
  if (!perfil.ativo) {
    return "Suas entregas estão pausadas. Para retomar, entre na sua conta: " + urlDaConta +
      " Se quiser falar com a equipe, é só escrever uma mensagem aqui.";
  }
  return `${RESPOSTA_CHAT_JA_VINCULADO} Para falar com a equipe, é só escrever uma mensagem aqui.`;
}

export async function processarMensagemLivre(
  mensagem: MensagemLivre,
  operacoes: OperacoesDeMensagemLivre,
  urlDaConta: string,
): Promise<void> {
  const perfil = await perfilOuNulo(operacoes, mensagem.chatId);
  if (perfil === "indisponivel") {
    await operacoes.responder(
      mensagem.chatId,
      `Não consegui ler sua conta agora. ${contatos(urlDaConta)}`,
    );
    return;
  }
  if (!perfil) {
    await operacoes.responder(mensagem.chatId, RESPOSTA_SEM_TOKEN);
    return;
  }
  const texto = mensagem.texto?.trim() ?? "";
  if (!texto) {
    await operacoes.responder(
      mensagem.chatId,
      `Por aqui só consigo ler mensagens de texto. ${contatos(urlDaConta)}`,
    );
    return;
  }
  if (texto.startsWith("/")) {
    await operacoes.responder(mensagem.chatId, respostaAoComando(perfil, urlDaConta));
    return;
  }
  if (await encaminhou(operacoes, textoParaOperacao(perfil.id, texto))) {
    await operacoes.responder(
      mensagem.chatId,
      `Recebemos sua mensagem; a equipe lê todas. ${contatos(urlDaConta)}`,
    );
    return;
  }
  await operacoes.responder(
    mensagem.chatId,
    `Não consegui entregar sua mensagem à equipe agora. ${contatos(urlDaConta)}`,
  );
}
