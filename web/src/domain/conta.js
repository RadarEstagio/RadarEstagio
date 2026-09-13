import { DIAS_ATE_APAGAR } from "./perfil.js";

export const SECOES_DA_CONTA = [
  {
    hash: "#account-overview-panel",
    rotulo: "Visão geral",
    titulo: "Conta",
    descricao: "Confira seu perfil de busca e controle como o Radar entrega suas recomendações.",
  },
  {
    hash: "#account-delivery-panel",
    rotulo: "Entregas",
    titulo: "Entregas",
    descricao: "Controle o envio das vagas e as comunicações do Radar.",
  },
  {
    hash: "#account-data-panel",
    rotulo: "Dados e acesso",
    titulo: "Dados e acesso",
    descricao: "Baixe suas informações ou encerre a sessão atual.",
  },
  {
    hash: "#account-privacy-panel",
    rotulo: "Privacidade",
    titulo: "Privacidade",
    descricao: "Gerencie o vínculo com o Telegram e as ações permanentes da sua conta.",
  },
];

export const MOTIVOS_DE_PAUSA = [
  ["conseguiu_estagio", "Consegui um estágio"],
  ["interrompeu_busca", "Interrompi a busca"],
  ["sem_vagas_uteis", "Não encontrei vagas úteis"],
  ["frequencia", "Minha frequência mudou"],
  ["outro", "Outro"],
];

export const VALORES_DOS_MOTIVOS_DE_PAUSA = new Set(MOTIVOS_DE_PAUSA.map(([valor]) => valor));

export const CONFIRMACOES = {
  desvincular: {
    titulo: "Desvincular o Telegram?",
    aviso: "As entregas serão interrompidas",
    detalhe: "O vínculo atual deixará de funcionar. Você poderá conectar o Telegram novamente depois.",
    copy: "Nenhuma vaga será enviada até uma nova vinculação.",
    confirmar: "Desvincular Telegram",
    origem: "#unlink-telegram",
  },
  excluir: {
    titulo: "Excluir sua conta?",
    aviso: "Sua conta será marcada para exclusão",
    detalhe: "As entregas param na hora. Seus dados serão apagados definitivamente depois de 60 dias.",
    copy: "Até o prazo terminar, você pode entrar novamente e cancelar a exclusão.",
    confirmar: "Excluir conta",
    origem: "#delete-account",
  },
};

const MODALIDADES_POR_EXTENSO = {
  remoto: "remoto",
  presencial: "presencial",
  hibrido: "híbrido",
  indiferente: "qualquer modalidade",
};

export function resumoDoPerfil(perfil) {
  return `${perfil.curso} · ${perfil.periodo}º período\n${perfil.cidade} · ${MODALIDADES_POR_EXTENSO[perfil.modalidade]}`;
}

export function visualDasEntregas(perfil) {
  if (perfil.excluida_em) return { estado: "deletion", titulo: "Exclusão agendada", simbolo: "!" };
  if (!perfil.telegram_chat_id) return { estado: "unlinked", titulo: "Telegram pendente", simbolo: "↗" };
  if (!perfil.ativo) return { estado: "paused", titulo: "Entregas pausadas", simbolo: "Ⅱ" };
  return { estado: "active", titulo: "Entregas ativas", simbolo: "✓" };
}

export function dataDoApagamento(marcadaEm) {
  const marcada = marcadaEm ? new Date(marcadaEm) : new Date();
  marcada.setDate(marcada.getDate() + DIAS_ATE_APAGAR);
  return marcada.toLocaleDateString("pt-BR");
}

export function estadoDasEntregas(perfil) {
  if (perfil.excluida_em) {
    return `Exclusão pedida. Seus dados são apagados em ${dataDoApagamento(perfil.excluida_em)}.`;
  }
  if (!perfil.telegram_chat_id) return "Telegram ainda não vinculado.";
  if (!perfil.ativo) return "Entregas pausadas. Nada chega até você retomar.";
  return "Telegram vinculado. As recomendações chegarão por lá quando houver vagas compatíveis. A primeira busca pode aguardar a próxima execução diária.";
}
