export async function interpretarCorpo(
  requisicao: { json: () => Promise<unknown> },
): Promise<Record<string, unknown> | null> {
  try {
    const corpo = await requisicao.json();
    if (!corpo || typeof corpo !== "object" || Array.isArray(corpo)) return null;
    return corpo as Record<string, unknown>;
  } catch (erro) {
    console.error("corpo da atualização não é JSON de objeto", erro);
    return null;
  }
}

export function cliqueQuePrecisaDeResposta(atualizacao: unknown): string | null {
  const clique = (atualizacao as { callback_query?: { id?: unknown } })?.callback_query;
  return typeof clique?.id === "string" ? clique.id : null;
}
