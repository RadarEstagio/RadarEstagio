export const VERSAO_DOS_TERMOS = "2026-09-05";
export const MAXIMO_DE_HABILIDADES = 50;
export const TAMANHO_MAXIMO_DA_HABILIDADE = 100;
export const DIAS_ATE_APAGAR = 60;
export const MODALIDADES_ACEITAS = new Set(["remoto", "presencial", "hibrido", "indiferente"]);
export const MENSAGEM_SEM_SESSAO = "Sua sessão expirou. Feche e entre de novo para continuar.";
export const MENSAGEM_SEM_PERFIL = "Não encontramos seu perfil. Feche e entre de novo.";
export const MENSAGEM_SEM_CONFIGURACAO =
  "O cadastro ainda não foi configurado. Informe a chave pública do Supabase em web/config.js.";

export const mensagensDeValidacao = {
  curso: "Informe o nome do seu curso.",
  periodo: "Selecione o período que você está cursando.",
  cidade: "Informe a cidade onde você procura vaga.",
  modalidade: "Escolha uma modalidade.",
  email: "Digite um e-mail como nome@exemplo.com.",
  aceitou_termos: "Aceite os Termos de Uso e a Política de Privacidade para criar a conta.",
  senha: "Use pelo menos 8 caracteres.",
};

const PADRAO_DE_EMAIL =
  /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

export function emailValido(email) {
  return PADRAO_DE_EMAIL.test(email);
}

export function erroDeValidacao(mensagem) {
  const erro = new Error(mensagem);
  erro.name = "RadarValidationError";
  return erro;
}

export function mensagemHumana(erro, { perfilPendente = false } = {}) {
  const mensagem = String(erro?.message ?? "").toLowerCase();
  const codigo = String(erro?.code ?? "").toLowerCase();
  const status = Number(erro?.status);

  if (mensagem.startsWith("o cadastro ainda não foi configurado")) return erro.message;
  if (erro?.name === "RadarValidationError") return erro.message;
  if (perfilPendente) {
    return "Sua conta foi criada, mas o perfil ainda não foi salvo. Entre novamente para concluir o perfil.";
  }
  if (codigo === "user_already_exists" || codigo === "email_exists" || mensagem.includes("user already registered")) {
    return "Já existe uma conta com esse e-mail. Escolha “Entrar” ou use outro e-mail.";
  }
  if (codigo === "invalid_credentials" || mensagem.includes("invalid login credentials")) {
    return "E-mail ou senha incorretos. Confira os dados ou crie uma conta.";
  }
  if (codigo === "email_not_confirmed" || mensagem.includes("email not confirmed")) {
    return "Confirme seu e-mail pelo link recebido antes de entrar.";
  }
  if (codigo === "weak_password" || mensagem.includes("password should be at least")) {
    return "A senha precisa ter pelo menos 8 caracteres.";
  }
  if (codigo === "over_email_send_rate_limit" || status === 429) {
    return "Muitas tentativas em pouco tempo. Aguarde alguns minutos e tente novamente.";
  }
  if (codigo === "23505" || mensagem.includes("duplicate key")) {
    return "Este perfil já existe. Recarregue a página e tente novamente.";
  }
  if (codigo === "42501" || mensagem.includes("row-level security") || mensagem.includes("permission denied")) {
    return "Não foi possível salvar o perfil nesta conta. Entre novamente e tente outra vez.";
  }
  if (mensagem.includes("failed to fetch") || mensagem.includes("network") || mensagem.includes("fetch")) {
    return "Não foi possível conectar ao cadastro. Verifique a conexão e tente novamente.";
  }
  return "Não foi possível concluir o cadastro agora. Verifique os dados e tente novamente.";
}
