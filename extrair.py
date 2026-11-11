"""Extração do dataset — Pesquisa Operacional, Grupo 16.

Baixa a malha viária de um bairro de Curitiba. As tabelas do dataset vão para
`datasets/`; o grafo salvo, os pontos s/t e a figura vão para `auxiliares/`.
O Dijkstra fica na Etapa 2.

    python extrair.py
    python extrair.py --forcar-download
    python extrair.py --sem-figura

Dados: OpenStreetMap, sob Open Database License (ODbL).
© colaboradores do OpenStreetMap.
"""

import argparse

import coleta
import config
import saidas


def main():
    analisador = argparse.ArgumentParser(
        description="Extrai a malha viária do recorte definido em config.py."
    )
    analisador.add_argument("--forcar-download", action="store_true",
                            help="Baixa a malha de novo em vez de reusar o graphml.")
    analisador.add_argument("--sem-figura", action="store_true",
                            help="Não gera malha.png.")
    argumentos = analisador.parse_args()

    config.PASTA_DATASETS.mkdir(parents=True, exist_ok=True)
    config.PASTA_AUXILIARES.mkdir(parents=True, exist_ok=True)

    grafo = coleta.obter_grafo(argumentos.forcar_download)
    arcos = saidas.salvar_tabelas(grafo)
    saidas.imprimir_estatisticas(grafo, arcos)

    origem, destinos = coleta.localizar_origem_e_destinos(grafo)
    saidas.salvar_pontos(origem, destinos)

    if not argumentos.sem_figura:
        saidas.salvar_figura(grafo)

    print()
    print(f"Extração concluída. Dataset em {config.PASTA_DATASETS}")
    print(f"                    Auxiliares em {config.PASTA_AUXILIARES}")
    print("Dados: OpenStreetMap (ODbL). © colaboradores do OpenStreetMap.")


if __name__ == "__main__":
    main()
