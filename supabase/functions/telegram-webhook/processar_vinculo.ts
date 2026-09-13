import { dentroDaJanelaDoDiario } from "./entrega_imediata.ts";
import { type PedidoDeVinculo, RESPOSTAS_DO_VINCULO, type ResultadoDoVinculo } from "./vinculo.ts";

export interface VinculoRealizado {
  resultado: ResultadoDoVinculo;
  perfilId: string | null;
}

export interface OperacoesDeVinculo {
  vincularChat: (token: string, chatId: string) => Promise<VinculoRealizado>;
  responder: (chatId: string, texto: string) => Promise<void>;
  dispararEntregaImediata: (perfilId: string) => Promise<void>;
}

export async function processarVinculo(
  pedido: PedidoDeVinculo,
  operacoes: OperacoesDeVinculo,
  agora: Date = new Date(),
): Promise<void> {
  const { resultado, perfilId } = await operacoes.vincularChat(pedido.token, pedido.chatId);
  await operacoes.responder(pedido.chatId, RESPOSTAS_DO_VINCULO[resultado]);
  if (resultado !== "vinculado" || !perfilId || dentroDaJanelaDoDiario(agora)) return;
  await operacoes.dispararEntregaImediata(perfilId);
}
