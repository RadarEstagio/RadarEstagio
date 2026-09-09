from pydantic import BaseModel

from radar.domain.areas import ROTULOS_DAS_SUBAREAS
from radar.domain.models import Julgamento, Perfil, Vaga

LIMITE_DA_DESCRICAO = 2500
PROBLEMAS_EXPLICADOS = (
    "nenhum: a recomendação faz sentido",
    "outra_area: a vaga é de outra formação ou de um campo que não conversa com o curso",
    "exige_demais: pede experiência, nível ou formação além de um estágio ou do momento do "
    "estudante",
    "logistica: cidade ou modalidade inviáveis para o estudante",
    "repetida: é a mesma vaga de outro anúncio da lista",
    "anuncio_fraco: não é estágio, é vago demais ou parece enganoso",
)
INSTRUCOES = (
    "Você é um orientador de carreira universitário criterioso. Vai avaliar recomendações de "
    "estágio que um sistema enviou a um estudante e dizer, para cada uma, se ela merecia ter "
    "sido enviada hoje.\n\n"
    "Julgue só com o texto do anúncio e o perfil do estudante. Não invente requisitos nem "
    "presuma informações que o anúncio não traz. Habilidades vazias significam que o estudante "
    "ainda não informou, não que ele é incapaz. Anúncio aberto a qualquer curso é relevante "
    "quando a área de atuação faz sentido para a formação. Vaga em outra cidade só é viável se "
    "for remota ou se o anúncio admitir trabalho remoto; estudante presencial precisa da própria "
    "cidade; estudante remoto precisa de vaga remota.\n\n"
    "Para cada vaga, responda:\n"
    "- relevante: true se você recomendaria a candidatura hoje, false caso contrário;\n"
    "- nota_juiz: de 0 a 100, sua confiança de que a candidatura vale a pena;\n"
    "- problema: um destes valores — " + "; ".join(PROBLEMAS_EXPLICADOS) + ";\n"
    "- motivo: uma frase curta em português.\n\n"
    "Devolva exatamente um julgamento para cada id listado, sem repetir ids e sem inventar ids."
)


class JulgamentosDeEntregas(BaseModel):
    julgamentos: list[Julgamento]


def montar_prompt_do_juiz(perfil: Perfil, vagas: list[Vaga]) -> str:
    return "\n\n".join([INSTRUCOES, descrever_perfil(perfil), descrever_vagas(vagas)])


def descrever_perfil(perfil: Perfil) -> str:
    habilidades = ", ".join(perfil.habilidades) or "ainda não informadas"
    interesses = ", ".join(
        ROTULOS_DAS_SUBAREAS.get(area.value, area.value) for area in perfil.areas_de_interesse
    )
    return "\n".join(
        [
            "Estudante:",
            f"- curso: {perfil.curso}",
            f"- período: {perfil.periodo}",
            f"- cidade: {perfil.cidade}",
            f"- modalidade que aceita: {perfil.modalidade.value}",
            f"- habilidades: {habilidades}",
            f"- áreas de interesse: {interesses or 'não informadas'}",
        ]
    )


def descrever_vagas(vagas: list[Vaga]) -> str:
    blocos = []
    for vaga in vagas:
        modalidade = vaga.modalidade.value if vaga.modalidade else "não informada"
        blocos.append(
            "\n".join(
                [
                    f"id: {vaga.id_externo}",
                    f"título: {vaga.titulo}",
                    f"empresa: {vaga.empresa}",
                    f"local: {vaga.localizacao} · modalidade: {modalidade}",
                    f"publicada em: {vaga.publicada_em:%d/%m/%Y}",
                    f"descrição: {resumir(vaga.descricao)}",
                ]
            )
        )
    return "Vagas recomendadas:\n\n" + "\n\n".join(blocos)


def resumir(descricao: str) -> str:
    texto = " ".join(descricao.split())
    if len(texto) <= LIMITE_DA_DESCRICAO:
        return texto
    return texto[:LIMITE_DA_DESCRICAO] + " […]"


def apenas_das_vagas(julgamentos: list[Julgamento], vagas: list[Vaga]) -> list[Julgamento]:
    por_id = {}
    for julgamento in julgamentos:
        por_id.setdefault(julgamento.id_vaga, julgamento)
    return [por_id[vaga.id_externo] for vaga in vagas if vaga.id_externo in por_id]
