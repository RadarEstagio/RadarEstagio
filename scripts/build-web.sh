#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
WEB_DIR="$ROOT_DIR/web"
DIST_DIR="$WEB_DIR/dist"

falhar() {
  printf 'build-web: %s\n' "$*" >&2
  exit 1
}

[[ -d "$WEB_DIR" ]] || falhar "diretório web ausente: $WEB_DIR"
[[ ! -L "$WEB_DIR" ]] || falhar "diretório web não pode ser um link simbólico"
[[ -d "$WEB_DIR/assets" && ! -L "$WEB_DIR/assets" ]] || falhar "diretório de assets inválido"
[[ "$DIST_DIR" == "$WEB_DIR/dist" ]] || falhar "destino de build inválido"
[[ "$DIST_DIR" != "/" && "$DIST_DIR" != "$ROOT_DIR" && "$DIST_DIR" != "$WEB_DIR" ]] || falhar "destino de limpeza amplo demais"
if [[ -L "$DIST_DIR" ]]; then
  falhar "destino de build não pode ser um link simbólico"
fi
if [[ -e "$DIST_DIR" && ! -d "$DIST_DIR" ]]; then
  falhar "destino de build não é um diretório"
fi

ARQUIVOS_HTML=("index.html" "termos.html" "privacidade.html")
ARQUIVOS_RAIZ=("config.js")
ARQUIVOS_ASSETS=("styles.css" "app.js" "areas.json" "cidades.json" "adzuna-logo.png")
RECURSOS_VITE=("areas.json" "cidades.json" "adzuna-logo.png")

validar_arquivo_fonte() {
  local caminho="$1"
  [[ -f "$caminho" && ! -L "$caminho" ]] || falhar "arquivo público ausente ou inválido: ${caminho#$ROOT_DIR/}"
}

validar_manifesto() {
  local pacote="$WEB_DIR/package.json"
  local lockfile="$WEB_DIR/package-lock.json"
  local vite="$WEB_DIR/vite.config.js"
  [[ -f "$pacote" && ! -L "$pacote" ]] || falhar "package.json inválido"
  [[ -f "$lockfile" && ! -L "$lockfile" ]] || falhar "package-lock.json ausente"
  [[ -f "$vite" && ! -L "$vite" ]] || falhar "vite.config.js ausente"
  command -v node >/dev/null 2>&1 || falhar "Node.js é necessário para validar o manifesto Vite"
  if ! node - "$pacote" <<'NODE'
const fs = require("fs");
const caminho = process.argv[2];
const pacote = JSON.parse(fs.readFileSync(caminho, "utf8"));
if (!pacote.scripts || typeof pacote.scripts.build !== "string" || pacote.scripts.build.trim() === "") process.exit(1);
NODE
  then
    falhar "package.json inválido ou sem script build"
  fi
}

limpar_destino() {
  rm -rf -- "$DIST_DIR"
  mkdir -p -- "$DIST_DIR/assets"
}

copiar_arquivo() {
  local relativo="$1"
  local origem="$WEB_DIR/$relativo"
  local destino="$DIST_DIR/$relativo"
  validar_arquivo_fonte "$origem"
  mkdir -p -- "$(dirname -- "$destino")"
  cp -- "$origem" "$destino"
}

validar_artefato() {
  [[ -d "$DIST_DIR" && ! -L "$DIST_DIR" ]] || falhar "artefato não foi gerado em web/dist"
  [[ -d "$DIST_DIR/assets" && ! -L "$DIST_DIR/assets" ]] || falhar "diretório de assets ausente no artefato"
  local relativo
  for relativo in "${ARQUIVOS_HTML[@]}" "${ARQUIVOS_RAIZ[@]}"; do
    [[ -f "$DIST_DIR/$relativo" && ! -L "$DIST_DIR/$relativo" ]] || falhar "arquivo obrigatório ausente no artefato: $relativo"
  done
  for relativo in "${RECURSOS_VITE[@]}"; do
    [[ -f "$DIST_DIR/assets/$relativo" && ! -L "$DIST_DIR/assets/$relativo" ]] || falhar "recurso público ausente no artefato: assets/$relativo"
  done
  while IFS= read -r -d '' proibido; do
    falhar "link simbólico no artefato: ${proibido#$DIST_DIR/}"
  done < <(find "$DIST_DIR" -type l -print0)
  while IFS= read -r -d '' proibido; do
    falhar "arquivo proibido no artefato: ${proibido#$DIST_DIR/}"
  done < <(find "$DIST_DIR" \( -type f -o -type d \) \( -name 'package.json' -o -name 'package-lock.json' -o -name '.env' -o -name '.env.*' -o -name 'node_modules' -o -name 'tests' -o -name 'coverage' -o -name 'reports' -o -name '.git' \) -print0)
}

if [[ -e "$WEB_DIR/package.json" || -L "$WEB_DIR/package.json" ]]; then
  validar_manifesto
  command -v npm >/dev/null 2>&1 || falhar "npm é necessário para o build Vite"
  limpar_destino
  npm --prefix "$WEB_DIR" ci
  npm --prefix "$WEB_DIR" run build
else
  limpar_destino
  for arquivo in "${ARQUIVOS_HTML[@]}" "${ARQUIVOS_RAIZ[@]}"; do
    copiar_arquivo "$arquivo"
  done
  for arquivo in "${ARQUIVOS_ASSETS[@]}"; do
    copiar_arquivo "assets/$arquivo"
  done
fi

validar_artefato
