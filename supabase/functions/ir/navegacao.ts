import { type PerfilDoDestinatario, podeProcessarInteracao } from "../_shared/privacidade.ts";

export interface EnvioDaVaga {
  perfilId: string;
  userId: string;
  vagaId: number;
  url: string;
  perfil: PerfilDoDestinatario;
}

const ESQUEMAS_PERMITIDOS = ["http:", "https:"];

export function enderecoNavegavel(url: string): boolean {
  try {
    return ESQUEMAS_PERMITIDOS.includes(new URL(url).protocol);
  } catch {
    return false;
  }
}

export async function destinoDoEnvio(
  envio: EnvioDaVaga | null,
  landing: string,
  registrar: boolean,
  registrarAbertura: (envio: EnvioDaVaga) => Promise<void>,
): Promise<string> {
  if (!envio || envio.perfil.excluida_em) return landing;
  if (!enderecoNavegavel(envio.url)) {
    console.error("envio com endereço fora de http(s)", envio.vagaId);
    return landing;
  }
  if (registrar && podeProcessarInteracao(envio.perfil)) {
    try {
      await registrarAbertura(envio);
    } catch (erro) {
      console.error("vaga_aberta não foi registrada", erro);
    }
  }
  return envio.url;
}
