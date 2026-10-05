import { assertEquals } from "jsr:@std/assert@1";
import { dentroDaJanelaDoDiario, dispararEntregaImediata } from "./entrega_imediata.ts";

Deno.test("janela do diario cobre 06:23 a 07:23 de brasilia", () => {
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T09:23:00Z")), true);
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T10:22:59Z")), true);
});

Deno.test("fora da janela a entrega imediata e liberada", () => {
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T09:22:59Z")), false);
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T10:23:00Z")), false);
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T23:59:00Z")), false);
});

function disparar(token: string | null, resposta: () => Response): Promise<boolean> {
  const consolaOriginal = [console.warn, console.error];
  console.warn = () => {};
  console.error = () => {};
  return dispararEntregaImediata(
    "perfil",
    token,
    (() => Promise.resolve(resposta())) as typeof fetch,
  )
    .finally(() => {
      [console.warn, console.error] = consolaOriginal;
    });
}

Deno.test("o disparo diz se saiu: sem token, com recusa do GitHub ou falha de rede não saiu", async () => {
  const aceito = () => new Response(null, { status: 204 });
  assertEquals(await disparar(null, aceito), false);
  assertEquals(await disparar("t", aceito), true);
  assertEquals(await disparar("t", () => new Response(null, { status: 404 })), false);
  assertEquals(
    await disparar("t", () => {
      throw new Error("rede");
    }),
    false,
  );
});
