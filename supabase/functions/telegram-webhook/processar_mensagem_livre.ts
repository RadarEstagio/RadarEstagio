import { CONTATO_DA_EQUIPE, RESPOSTA_CHAT_JA_VINCULADO, RESPOSTA_SEM_TOKEN } from "./vinculo.ts";

export const TAMANHO_MAXIMO_DO_TEXTO_ENCAMINHADO = 3000;

export interface MensagemLivre {
  chatId: string;
  texto: string | null;
}

export interface OperacoesDeMensagemLivre {
  perfilDoChat: (chatId: string) => Promise<string | null>;
  responder: (chatId: string, texto: string) => Promise<void>;
  encaminharParaOperacao: (texto: string) => Promise<boolean>;
}

function contatos(urlDaConta: string): string {
  return `Escreva para ${CONTATO_DA_EQUIPE} ou entre na sua conta: ${urlDaConta}`;
}

function textoParaOperacao(perfilId: string, texto: string): string {
  const caracteres = Array.from(texto);
  const recebido = caracteres.length > TAMANHO_MAXIMO_DO_TEXTO_ENCAMINHADO
    ? `${caracteres.slice(0, TAMANHO_MAXIMO_DO_TEXTO_ENCAMINHADO).join("")}…`
    : texto;
  return `Mensagem de um usuário pelo bot (perfil ${perfilId}):\n\n${recebido}`;
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

export async function processarMensagemLivre(
  mensagem: MensagemLivre,
  operacoes: OperacoesDeMensagemLivre,
  urlDaConta: string,
): Promise<void> {
  const perfilId = await operacoes.perfilDoChat(mensagem.chatId);
  if (!perfilId) {
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
    await operacoes.responder(
      mensagem.chatId,
      `${RESPOSTA_CHAT_JA_VINCULADO} Para falar com a equipe, é só escrever uma mensagem aqui.`,
    );
    return;
  }
  if (await encaminhou(operacoes, textoParaOperacao(perfilId, texto))) {
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
