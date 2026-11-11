"""Parâmetros do projeto. Único arquivo com valores a ajustar."""

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
