from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# O dataset em si: as duas tabelas que o trabalho entrega.
PASTA_DATASETS = RAIZ / "datasets"
CAMINHO_NOS = PASTA_DATASETS / "nos.csv"
CAMINHO_ARCOS = PASTA_DATASETS / "arcos.csv"

# Subprodutos da extração: grafo salvo, pontos s/t, figura e documentação.
PASTA_AUXILIARES = RAIZ / "auxiliares"
CAMINHO_GRAFO = PASTA_AUXILIARES / "grafo.graphml"
CAMINHO_FIGURA = PASTA_AUXILIARES / "malha.png"
CAMINHO_PONTOS = PASTA_AUXILIARES / "pontos.json"

# Recorte da malha. Um bairro, e não a cidade inteira: Curitiba toda passa de
# 100 mil arcos e deixa de ser inspecionável.
LUGAR = "Batel, Curitiba, Parana, Brazil"

# "drive" = só vias onde carro pode trafegar, respeitando mão única.
TIPO_DE_MALHA = "drive"

# Precisam estar dentro de LUGAR: um endereço de fora é grudado no cruzamento
# mais próximo da borda da malha, sem aviso, e a rota sai falsa.
ENDERECO_ORIGEM = "Shopping Pátio Batel, Curitiba, Parana, Brazil"
ENDERECOS_DESTINO = [
    "Rua Desembargador Motta, Curitiba, Parana, Brazil",
    "Rua Olavo Bilac, Curitiba, Parana, Brazil",
]

# Velocidade em km/h por classificação de via, usada quando o OSM não informa
# 'maxspeed' no trecho. Baseada nos limites urbanos brasileiros típicos.
VELOCIDADES_BR = {
    "motorway": 90,
    "trunk": 70,
    "primary": 60,
    "secondary": 50,
    "tertiary": 40,
    "residential": 30,
    "living_street": 20,
    "unclassified": 30,
    "service": 20,
}
VELOCIDADE_PADRAO = 40

# Colunas exportadas. Os nomes vêm do OSMnx e por isso ficam em inglês.
COLUNAS_NOS = ["y", "x", "street_count"]
COLUNAS_ARCOS = ["name", "highway", "oneway", "length", "speed_kph", "travel_time"]

# --- Etapa 2: Dijkstra ---

# Saídas da resolução: tabela de comparação e uma figura por destino, na mesma
# ordem de ENDERECOS_DESTINO.
CAMINHO_COMPARACAO = PASTA_AUXILIARES / "comparacao.csv"
CAMINHOS_FIGURAS_ROTAS = [
    PASTA_AUXILIARES / "rotas_t1_desembargador_motta.png",
    PASTA_AUXILIARES / "rotas_t2_olavo_bilac.png",
]

# Os dois pesos comparados: travel_time é o custo `w` do modelo, length é a
# referência de menor distância. Nomes em inglês porque são atributos do OSMnx.
PESOS = ["travel_time", "length"]
UNIDADES = {"travel_time": "s", "length": "m"}

# Cor, espessura e rótulo de cada rota nas figuras. A rota por tempo é desenhada
# primeiro e mais grossa, para continuar visível nos trechos em que as duas
# coincidem.
ESTILOS_ROTAS = {
    "travel_time": {"cor": "#1f77b4", "espessura": 5.0},
    "length": {"cor": "#ff7f0e", "espessura": 2.2},
}

# Quantas iterações do passo a passo imprimir por execução.
ITERACOES_EXIBIDAS = 15

# Colunas da tabela de comparação gravada em comparacao.csv.
COLUNAS_COMPARACAO = ["destino", "no", "endereco", "peso", "arcos", "tempo_s", "distancia_m"]
