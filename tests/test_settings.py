import pytest
from pydantic import ValidationError

from radar.settings import Settings


def configuracao_base(**sobrescritas: str) -> dict[str, str]:
    valores = {
        "adzuna_app_id": "adzuna-id",
        "adzuna_app_key": "adzuna-chave",
        "gemini_api_key": "",
        "telegram_bot_token": "telegram-token",
        "telegram_chat_id": "123",
    }
    valores.update(sobrescritas)
    return valores


def test_modo_agy_nao_exige_chave_da_api_gemini():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert settings.avaliador == "agy"
    assert settings.gemini_api_key == ""


def test_modo_gemini_api_exige_chave():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **configuracao_base(avaliador="gemini_api"))


def test_fonte_padrao_e_so_a_adzuna():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert settings.fontes_selecionadas() == ["adzuna"]


def test_jooble_nao_entra_nas_fontes_padrao_e_exige_chave():
    padrao = Settings(_env_file=None, **configuracao_base(avaliador="agy"))
    assert "jooble" not in padrao.fontes_selecionadas()

    com_chave = Settings(
        _env_file=None,
        **configuracao_base(avaliador="agy", fontes="adzuna,jooble", jooble_api_key="chave"),
    )
    assert com_chave.fontes_selecionadas() == ["adzuna", "jooble"]

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **configuracao_base(avaliador="agy", fontes="jooble"))


def configurar_o_ambiente_do_workflow(
    monkeypatch: pytest.MonkeyPatch, fontes: str, chave_da_jooble: str
) -> None:
    ambiente = {
        "ADZUNA_APP_ID": "adzuna-id",
        "ADZUNA_APP_KEY": "adzuna-chave",
        "GEMINI_API_KEY": "gemini-chave",
        "TELEGRAM_BOT_TOKEN": "telegram-token",
        "TELEGRAM_CHAT_ID": "123",
        "FONTES": fontes,
        "JOOBLE_API_KEY": chave_da_jooble,
    }
    for nome, valor in ambiente.items():
        monkeypatch.setenv(nome, valor)


def test_workflow_sem_a_variavel_e_sem_o_secret_da_jooble_roda_so_com_a_adzuna(
    monkeypatch: pytest.MonkeyPatch,
):
    configurar_o_ambiente_do_workflow(monkeypatch, fontes="adzuna", chave_da_jooble="")

    assert Settings(_env_file=None).fontes_selecionadas() == ["adzuna"]


def test_variavel_ligada_sem_o_secret_da_jooble_invalida_a_configuracao_inteira(
    monkeypatch: pytest.MonkeyPatch,
):
    configurar_o_ambiente_do_workflow(monkeypatch, fontes="adzuna,jooble", chave_da_jooble="")

    with pytest.raises(ValidationError, match="JOOBLE_API_KEY é obrigatória"):
        Settings(_env_file=None)


def test_secret_da_jooble_sem_a_variavel_ligada_nao_liga_a_fonte(
    monkeypatch: pytest.MonkeyPatch,
):
    configurar_o_ambiente_do_workflow(monkeypatch, fontes="adzuna", chave_da_jooble="chave")

    assert Settings(_env_file=None).fontes_selecionadas() == ["adzuna"]


def test_variavel_e_secret_da_jooble_ligam_as_duas_fontes(monkeypatch: pytest.MonkeyPatch):
    configurar_o_ambiente_do_workflow(monkeypatch, fontes="adzuna,jooble", chave_da_jooble="chave")

    assert Settings(_env_file=None).fontes_selecionadas() == ["adzuna", "jooble"]


def test_fontes_aceitam_espacos_e_maiusculas():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy", fontes=" Gupy "))

    assert settings.fontes_selecionadas() == ["gupy"]


@pytest.mark.parametrize("fontes", ["", "linkedin", "adzuna,linkedin"])
def test_fontes_desconhecidas_ou_vazias_sao_rejeitadas(fontes: str):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **configuracao_base(avaliador="agy", fontes=fontes))


def test_sem_banco_exige_chat_id_do_telegram():
    with pytest.raises(ValidationError, match="TELEGRAM_CHAT_ID"):
        Settings(_env_file=None, **configuracao_base(avaliador="agy", telegram_chat_id=""))


def test_com_banco_o_chat_id_e_opcional():
    settings = Settings(
        _env_file=None,
        **configuracao_base(
            avaliador="agy", telegram_chat_id="", database_url="postgresql://radar@localhost/radar"
        ),
    )

    assert settings.usa_banco()
    assert settings.telegram_chat_id == ""


def test_sem_database_url_nao_usa_banco():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert not settings.usa_banco()


def test_nota_minima_padrao_e_40():
    assert Settings(_env_file=None, **configuracao_base(avaliador="agy")).nota_minima == 40


def test_busca_vagas_dos_ultimos_3_dias_por_padrao():
    assert Settings(_env_file=None, **configuracao_base(avaliador="agy")).dias_recentes == 3


def test_prazo_da_extracao_padrao_e_de_dez_minutos():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert settings.prazo_da_extracao_segundos == 600


def test_prazo_da_extracao_zero_e_rejeitado():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None, **configuracao_base(avaliador="agy", prazo_da_extracao_segundos="0")
        )


@pytest.mark.parametrize("nota", ["-1", "101"])
def test_nota_minima_fora_de_0_a_100_e_rejeitada(nota: str):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **configuracao_base(avaliador="agy", nota_minima=nota))


def test_conta_excluida_e_apagada_60_dias_depois_do_pedido():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert settings.dias_ate_apagar_conta_excluida == 60


def test_carencia_de_zero_dia_para_apagar_a_conta_e_rejeitada():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None, **configuracao_base(avaliador="agy", dias_ate_apagar_conta_excluida="0")
        )


def test_raciocinio_da_extracao_e_baixo_por_padrao():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert settings.gemini_raciocinio == "low"


def test_raciocinio_fora_dos_niveis_do_gemini_e_rejeitado():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **configuracao_base(avaliador="agy", gemini_raciocinio="alto"))
