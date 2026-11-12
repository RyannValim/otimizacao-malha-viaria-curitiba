import json

import osmnx as ox
import pytest

import config
import dijkstra

# Cenário e valores de referência do enunciado da Etapa 2, conferidos na seção 8
# da DOCUMENTACAO.md. Se a implementação divergir destes números, há erro nela.
S = 11220213870
T1 = 1386657461
T2 = 324728738

TEMPOS_OTIMOS = {T1: 195.5, T2: 87.6}
DISTANCIAS_OTIMAS = {T1: 2431.0, T2: 753.0}
ARCOS_POR_TEMPO = {T1: 20, T2: 7}

# O enunciado publica os valores arredondados; a tolerância cobre só isso.
TOLERANCIA_TEMPO = 0.05
TOLERANCIA_DISTANCIA = 0.5

# Nós que a mão única isola: existem na malha, mas não são alcançáveis de s.
INALCANCAVEIS = [324363513, 3605030038]

@pytest.fixture(scope="module")
def grafo():
    return ox.io.load_graphml(str(config.CAMINHO_GRAFO))

@pytest.fixture(scope="module")
def por_tempo(grafo):
    return dijkstra.dijkstra(grafo, S, "travel_time")

@pytest.fixture(scope="module")
def por_distancia(grafo):
    return dijkstra.dijkstra(grafo, S, "length")

# O peso do modelo é não negativo, hipótese que o Dijkstra exige.
def test_pesos_nao_sao_negativos(grafo):
    for _, _, arco in grafo.edges(data=True):
        assert arco["travel_time"] >= 0
        assert arco["length"] >= 0

# O cenário resolvido na Etapa 1 continua sendo o que o enunciado valida.
def test_pontos_conferem_com_o_enunciado():
    conteudo = json.loads(config.CAMINHO_PONTOS.read_text(encoding="utf-8"))
    assert conteudo["origem"]["no"] == S
    assert [destino["no"] for destino in conteudo["destinos"]] == [T1, T2]

@pytest.mark.parametrize("destino", [T1, T2])
def test_tempo_otimo(por_tempo, destino):
    rotulos, _, _ = por_tempo
    assert rotulos[destino] == pytest.approx(TEMPOS_OTIMOS[destino], abs=TOLERANCIA_TEMPO)

@pytest.mark.parametrize("destino", [T1, T2])
def test_numero_de_arcos_da_rota_de_menor_tempo(por_tempo, destino):
    _, antecessores, _ = por_tempo
    caminho = dijkstra.reconstruir_caminho(antecessores, S, destino)
    assert len(caminho) - 1 == ARCOS_POR_TEMPO[destino]

@pytest.mark.parametrize("destino", [T1, T2])
def test_distancia_otima(por_distancia, destino):
    rotulos, _, _ = por_distancia
    assert rotulos[destino] == pytest.approx(DISTANCIAS_OTIMAS[destino], abs=TOLERANCIA_DISTANCIA)

# O caminho remontado liga mesmo s a t, sem buracos: todo par consecutivo é um
# arco que existe na malha.
@pytest.mark.parametrize("destino", [T1, T2])
def test_caminho_e_uma_sequencia_valida_de_arcos(grafo, por_tempo, destino):
    _, antecessores, _ = por_tempo
    caminho = dijkstra.reconstruir_caminho(antecessores, S, destino)

    assert caminho[0] == S
    assert caminho[-1] == destino
    assert len(set(caminho)) == len(caminho)
    for no, proximo in zip(caminho, caminho[1:]):
        assert grafo.has_edge(no, proximo)

# O rótulo do destino tem que ser igual ao custo do caminho medido arco a arco.
@pytest.mark.parametrize("destino", [T1, T2])
def test_rotulo_bate_com_a_medicao_do_caminho(grafo, por_tempo, destino):
    rotulos, antecessores, _ = por_tempo
    caminho = dijkstra.reconstruir_caminho(antecessores, S, destino)
    medidas = dijkstra.medir_caminho(grafo, caminho, "travel_time")
    assert medidas["tempo"] == pytest.approx(rotulos[destino])

# Otimalidade: nenhuma outra rota pode ser mais rápida que a de menor tempo, e a
# rota de menor distância não pode ser mais curta que a ótima em distância.
@pytest.mark.parametrize("destino", [T1, T2])
def test_rota_por_distancia_nao_supera_a_otima_em_tempo(grafo, por_tempo, por_distancia, destino):
    rotulos_tempo, _, _ = por_tempo
    _, antecessores_distancia, _ = por_distancia
    caminho = dijkstra.reconstruir_caminho(antecessores_distancia, S, destino)
    medidas = dijkstra.medir_caminho(grafo, caminho, "length")
    assert medidas["tempo"] >= rotulos_tempo[destino]

def test_rotulo_da_origem_e_zero(por_tempo):
    rotulos, antecessores, _ = por_tempo
    assert rotulos[S] == 0.0
    assert S not in antecessores

# Uma execução de origem única rotula toda a malha alcançável de uma vez.
def test_alcance_a_partir_da_origem(grafo, por_tempo):
    rotulos, _, registro = por_tempo
    assert grafo.number_of_nodes() == 166
    assert len(rotulos) == 164
    assert len(registro) == 164
    assert [no for no in grafo.nodes if no not in rotulos] == INALCANCAVEIS

@pytest.mark.parametrize("destino", INALCANCAVEIS)
def test_destino_inalcancavel_nao_tem_caminho(por_tempo, destino):
    _, antecessores, _ = por_tempo
    assert dijkstra.reconstruir_caminho(antecessores, S, destino) is None

# Cada iteração fecha um nó, com rótulo nunca menor que o da iteração anterior,
# que é o que garante que o rótulo fechado é definitivo.
def test_rotulos_fecham_em_ordem_nao_decrescente(por_tempo):
    _, _, registro = por_tempo
    rotulos_fechados = [passo["rotulo"] for passo in registro]
    assert rotulos_fechados == sorted(rotulos_fechados)
    assert [passo["iteracao"] for passo in registro] == list(range(1, len(registro) + 1))

# O registro traz a conta de cada vizinho examinado, não só dos relaxados.
def test_registro_guarda_os_exames_de_cada_iteracao(grafo, por_tempo):
    _, _, registro = por_tempo
    primeira = registro[0]

    assert primeira["no"] == S
    assert primeira["rotulo"] == 0.0
    assert len(primeira["exames"]) == grafo.out_degree(S)
    for exame in primeira["exames"]:
        assert exame["candidato"] == pytest.approx(primeira["rotulo"] + exame["custo"])
        assert exame["relaxado"] == (exame["candidato"] < exame["rotulo_atual"])
