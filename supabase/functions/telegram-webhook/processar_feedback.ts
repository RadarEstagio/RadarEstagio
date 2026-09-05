import {
  ACAO_DE_FEEDBACK,
  ACAO_DE_RECUSA,
  ACAO_SEM_RECUSA,
  AVISO_DE_CONSULTA_DESCONHECIDA,
  AVISO_DE_RECUSA_REGISTRADA,
  AVISO_DE_TUDO_CERTO,
  type ConsultaDeFeedback,
  eventoDoFeedback,
} from "./feedback.ts";

export interface EnvioDoToken {
  perfilId: string;
  userId: string;
  vagaId: number;
  titulo: string;
  empresa: string;
}

export interface OperacoesDeFeedback {
  envioDoToken: (token: string, chatId: string) => Promise<EnvioDoToken | null>;
  registrarFeedback: (envio: EnvioDoToken, acao: string) => Promise<void>;
  perguntarOMotivo: (consulta: ConsultaDeFeedback, envio: EnvioDoToken) => Promise<void>;
  encerrarPergunta: (consulta: ConsultaDeFeedback) => Promise<void>;
}

export async function processarFeedback(
  consulta: ConsultaDeFeedback,
  operacoes: OperacoesDeFeedback,
): Promise<string> {
  const envio = await operacoes.envioDoToken(consulta.token, consulta.chatId);
  if (!envio) return AVISO_DE_CONSULTA_DESCONHECIDA;
  if (consulta.acao === ACAO_DE_RECUSA || consulta.acao === ACAO_DE_FEEDBACK) {
    await operacoes.perguntarOMotivo(consulta, envio);
    return "";
  }
  if (consulta.acao === ACAO_SEM_RECUSA) {
    await operacoes.encerrarPergunta(consulta);
    return AVISO_DE_TUDO_CERTO;
  }
  if (!eventoDoFeedback(consulta.acao)) return AVISO_DE_CONSULTA_DESCONHECIDA;
  await operacoes.registrarFeedback(envio, consulta.acao);
  try {
    await operacoes.encerrarPergunta(consulta);
  } catch (erro) {
    console.error("feedback gravado, mas pergunta não pôde ser fechada", erro);
  }
  return AVISO_DE_RECUSA_REGISTRADA;
}

export async function responderConsultaDeFeedback(
  consulta: ConsultaDeFeedback,
  operacoes: OperacoesDeFeedback,
  confirmarConsulta: (aviso: string) => Promise<void>,
): Promise<Response> {
  let aviso: string;
  try {
    aviso = await processarFeedback(consulta, operacoes);
  } catch (erro) {
    console.error("falha ao tratar clique do telegram", erro);
    return new Response(null, { status: 500 });
  }
  try {
    await confirmarConsulta(aviso);
  } catch (erro) {
    console.error("consulta processada, mas confirmação do telegram falhou", erro);
  }
  return new Response(null, { status: 200 });
}
