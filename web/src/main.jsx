import { createClient } from "@supabase/supabase-js";
import { iniciarAplicacao } from "./app/iniciar.jsx";

iniciarAplicacao({ janela: window, criarCliente: createClient });
