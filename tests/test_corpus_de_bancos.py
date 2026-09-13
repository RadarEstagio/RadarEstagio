import json
from pathlib import Path

from radar.domain.models import ExtracaoDaVaga, Perfil, Vaga
from radar.matching.avaliacoes import pontuar

CORPUS_DE_BANCOS = Path(__file__).parent / "fixtures" / "notas_de_bancos_em_b1ccbf1.json"
PARES_NO_CORPUS = 874


def test_nenhum_par_do_corpus_de_bancos_cai_em_relacao_ao_b1ccbf1():
    corpus = json.loads(CORPUS_DE_BANCOS.read_text())
    vaga_do_corpus = Vaga.model_validate(corpus["vaga"])
    comparados = 0
    quedas = []
    for nome_do_perfil, dados_do_perfil in corpus["perfis"].items():
        candidato = Perfil(**corpus["perfil_base"], **dados_do_perfil)
        for nome_da_extracao, dados_da_extracao in corpus["extracoes"].items():
            extracao = ExtracaoDaVaga(id_vaga=nome_da_extracao, **dados_da_extracao)
            nota = pontuar(vaga_do_corpus, extracao, candidato).nota
            nota_no_b1ccbf1 = corpus["notas"][nome_do_perfil][nome_da_extracao]
            comparados += 1
            if nota < nota_no_b1ccbf1:
                quedas.append((nome_do_perfil, nome_da_extracao, nota_no_b1ccbf1, nota))

    assert comparados == PARES_NO_CORPUS
    assert quedas == []
