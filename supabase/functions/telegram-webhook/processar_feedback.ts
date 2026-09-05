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
  await operacoes.encerrarPergunta(consulta);
  return AVISO_DE_RECUSA_REGISTRADA;
}
