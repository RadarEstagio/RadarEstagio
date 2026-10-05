import { dentroDaJanelaDoDiario } from "./entrega_imediata.ts";
import {
  type PedidoDeVinculo,
  RESPOSTA_VINCULADO_COM_BUSCA,
  RESPOSTA_VINCULADO_NA_JANELA,
  RESPOSTA_VINCULADO_SEM_DISPARO,
  RESPOSTAS_DO_VINCULO,
  type ResultadoDoVinculo,
} from "./vinculo.ts";

export interface VinculoRealizado {
  resultado: ResultadoDoVinculo;
  perfilId: string | null;
}

export interface OperacoesDeVinculo {
  vincularChat: (token: string, chatId: string) => Promise<VinculoRealizado>;
  responder: (chatId: string, texto: string) => Promise<void>;
  reivindicarEntregaImediata: (perfilId: string) => Promise<boolean>;
  dispararEntregaImediata: (perfilId: string) => Promise<boolean>;
}

export async function processarVinculo(
  pedido: PedidoDeVinculo,
  operacoes: OperacoesDeVinculo,
  agora: Date = new Date(),
): Promise<void> {
  const { resultado, perfilId } = await operacoes.vincularChat(pedido.token, pedido.chatId);
  if (resultado !== "vinculado" || !perfilId) {
    await operacoes.responder(pedido.chatId, RESPOSTAS_DO_VINCULO[resultado]);
    return;
  }
  if (dentroDaJanelaDoDiario(agora)) {
    await operacoes.responder(pedido.chatId, RESPOSTA_VINCULADO_NA_JANELA);
    return;
  }
  if (!(await operacoes.reivindicarEntregaImediata(perfilId))) {
    await operacoes.responder(pedido.chatId, RESPOSTAS_DO_VINCULO.vinculado);
    return;
  }
  const disparou = await operacoes.dispararEntregaImediata(perfilId);
  await operacoes.responder(
    pedido.chatId,
    disparou ? RESPOSTA_VINCULADO_COM_BUSCA : RESPOSTA_VINCULADO_SEM_DISPARO,
  );
}
