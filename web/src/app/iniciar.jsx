import { createRoot } from "react-dom/client";
import { iniciarDemonstracao } from "../landing/demonstracao.js";
import { iniciarTema } from "../landing/tema.js";
import { App } from "./App.jsx";
import { criarControlador } from "./controlador.js";

export function iniciarAplicacao({ janela, criarCliente }) {
  const pararTema = iniciarTema(janela);
  const pararDemonstracao = iniciarDemonstracao(janela);
  const controlador = criarControlador({ janela, criarCliente });
  const raiz = createRoot(controlador.paginaDaConta);
  raiz.render(<App controlador={controlador} />);
  void controlador.iniciar();
  return {
    controlador,
    encerrar() {
      controlador.encerrar();
      pararDemonstracao();
      pararTema();
      raiz.unmount();
    },
  };
}
