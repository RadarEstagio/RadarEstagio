from datetime import UTC, date, datetime
from uuid import uuid4

from radar.domain.models import ExtracaoDaVaga, ResultadoMatch, Usuario, Vaga
from radar.domain.perfil_fixo import perfil_de_exemplo
from radar.storage.memoria import RepositorioDoModoLocal, RepositorioEmMemoria


def usuario_exemplo() -> Usuario:
    return Usuario(id=uuid4(), perfil=perfil_de_exemplo(), chat_id="123")


def vaga_exemplo() -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio Python",
        empresa="Empresa",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url="https://exemplo.com/1",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


def test_lista_os_usuarios_recebidos():
    usuario = usuario_exemplo()

    assert RepositorioEmMemoria([usuario]).listar_ativos() == [usuario]


def test_nao_guarda_nada_entre_chamadas():
    usuario = usuario_exemplo()
    repositorio = RepositorioEmMemoria([usuario])
    resultado = ResultadoMatch(vaga=vaga_exemplo(), nota=80)

    repositorio.guardar_avaliacoes(usuario, [resultado], "modelo")
    repositorio.registrar_envios(usuario, [resultado])

    assert repositorio.ids_ja_enviadas(usuario) == set()
    assert repositorio.vagas_enviadas_recentemente(usuario) == []
    assert repositorio.recusas_do_usuario(usuario).areas == []
    assert repositorio.recusas_do_usuario(usuario).vagas_repetidas == []
    assert repositorio.travar_atendimento(usuario) is None
    assert repositorio.liberar_atendimento(usuario) is None
    assert repositorio.registrar_falha_de_envio(usuario) == 0


def test_conta_em_quantos_dias_diferentes_cada_vaga_ficou_sem_extracao():
    repositorio = RepositorioEmMemoria([])
    primeira = vaga_exemplo()
    segunda = vaga_exemplo().model_copy(update={"id_externo": "2"})

    assert repositorio.registrar_vagas_sem_extracao([primeira], date(2026, 9, 10)) == {
        ("adzuna", "1"): 1
    }
    assert repositorio.registrar_vagas_sem_extracao([primeira], date(2026, 9, 10)) == {
        ("adzuna", "1"): 1
    }
    assert repositorio.registrar_vagas_sem_extracao([primeira, segunda], date(2026, 9, 11)) == {
        ("adzuna", "1"): 2,
        ("adzuna", "2"): 1,
    }


def test_extracao_guardada_recomeca_a_contagem_de_dias_sem_extracao():
    repositorio = RepositorioEmMemoria([])
    vaga = vaga_exemplo()
    repositorio.registrar_vagas_sem_extracao([vaga], date(2026, 9, 10))
    repositorio.registrar_vagas_sem_extracao([vaga], date(2026, 9, 11))

    repositorio.guardar_extracoes(
        [(vaga, ExtracaoDaVaga(id_vaga=vaga.identidade(), area_da_vaga="computacao"))], "m"
    )

    assert repositorio.registrar_vagas_sem_extracao([vaga], date(2026, 9, 12)) == {
        ("adzuna", "1"): 1
    }


def test_modo_local_nao_tem_historico_de_vagas_sem_extracao():
    repositorio = RepositorioDoModoLocal([])

    assert repositorio.registrar_vagas_sem_extracao([vaga_exemplo()], date(2026, 9, 10)) is None
