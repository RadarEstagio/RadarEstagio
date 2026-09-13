import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const raiz = fileURLToPath(new URL(".", import.meta.url));
const paginas = ["index.html", "termos.html", "privacidade.html"];
const recursosSemBundle = ["config.js", "assets/areas.json", "assets/cidades.json"];

function copiarRecursosSemBundle() {
  return {
    name: "copiar-recursos-sem-bundle",
    async generateBundle() {
      for (const fileName of recursosSemBundle) {
        this.emitFile({ type: "asset", fileName, source: await readFile(resolve(raiz, fileName)) });
      }
    },
  };
}

export default defineConfig({
  root: raiz,
  base: "./",
  publicDir: false,
  plugins: [react(), copiarRecursosSemBundle()],
  server: { host: "localhost", port: 8000, strictPort: true },
  preview: { host: "localhost", port: 8000, strictPort: true },
  build: {
    outDir: resolve(raiz, "dist"),
    emptyOutDir: true,
    assetsInlineLimit: 0,
    rollupOptions: {
      input: Object.fromEntries(paginas.map((pagina) => [pagina.replace(".html", ""), resolve(raiz, pagina)])),
      output: { assetFileNames: "assets/[name][extname]" },
    },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{js,jsx}"],
  },
});
