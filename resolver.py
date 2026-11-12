import argparse
import json

import osmnx as ox

import config
import dijkstra
import saidas

# Carrega o grafo do graphml. Só a OSMnx converte os pesos, que o GraphML
# guarda como texto, de volta para float.
def carregar_grafo():
    print(f"Carregando o grafo de {config.CAMINHO_GRAFO}")
    return ox.io.load_graphml(str(config.CAMINHO_GRAFO))

# Lê os nós s e t já resolvidos na Etapa 1, sem geocodificar de novo.
def carregar_pontos():
    conteudo = json.loads(config.CAMINHO_PONTOS.read_text(encoding="utf-8"))
    return conteudo["origem"], conteudo["destinos"]

# Resolve os caminhos mínimos de s até cada destino, uma execução por peso.
# O Dijkstra é de origem única: uma execução rotula todos os nós da malha, então
# os dois destinos saem da mesma árvore de antecessores (ver seção 7 da
# DOCUMENTACAO.md). Devolve as linhas da comparação e as rotas por destino.
def resolver(grafo, origem, destinos, iteracoes):
    linhas = []
    rotas_por_destino = {destino["no"]: {} for destino in destinos}

    for peso in config.PESOS:
        rotulos, antecessores, registro = dijkstra.dijkstra(grafo, origem["no"], peso)
        saidas.imprimir_passo_a_passo(registro, peso, grafo.number_of_nodes(), iteracoes)

        for indice, destino in enumerate(destinos, start=1):
            caminho = dijkstra.reconstruir_caminho(antecessores, origem["no"], destino["no"])
            if caminho is None:
                print(f"t{indice} = {destino['no']} é inalcançável a partir de s.")
                continue

            medidas = dijkstra.medir_caminho(grafo, caminho, peso)
            rotas_por_destino[destino["no"]][peso] = {"caminho": caminho, "medidas": medidas}
            linhas.append({
                "destino": f"t{indice}",
                "no": destino["no"],
                "endereco": destino["endereco"],
                "peso": peso,
                "arcos": medidas["arcos"],
                "tempo_s": medidas["tempo"],
                "distancia_m": medidas["distancia"],
            })

            # O rótulo do destino é o ótimo pelo peso usado; as medidas acima
            # avaliam a mesma rota nas duas métricas.
            print(f"t{indice} = {destino['no']}: rótulo ótimo "
                  f"{rotulos[destino['no']]:.2f} {config.UNIDADES[peso]}, "
                  f"{medidas['arcos']} arcos.")

    # Ordena por destino, e dentro dele na ordem de PESOS, para que a tabela
    # mostre os dois pesos do mesmo destino lado a lado.
    linhas.sort(key=lambda linha: (linha["destino"], config.PESOS.index(linha["peso"])))
    return linhas, rotas_por_destino

def main():
    analisador = argparse.ArgumentParser(
        description="Resolve o caminho mínimo de s até cada t com o Dijkstra implementado à mão."
    )
    analisador.add_argument("--iteracoes", type=int, default=config.ITERACOES_EXIBIDAS,
                            help="Quantas iterações do passo a passo imprimir "
                                 f"(padrão: {config.ITERACOES_EXIBIDAS}).")
    analisador.add_argument("--sem-figura", action="store_true",
                            help="Não gera os PNGs das rotas.")
    argumentos = analisador.parse_args()

    config.PASTA_AUXILIARES.mkdir(parents=True, exist_ok=True)

    grafo = carregar_grafo()
    origem, destinos = carregar_pontos()

    print()
    print("=== ORIGEM E DESTINOS ===")
    print(f"Origem  s = {origem['no']}  ({origem['endereco']})")
    for indice, destino in enumerate(destinos, start=1):
        print(f"Destino t{indice} = {destino['no']}  ({destino['endereco']})")

    linhas, rotas_por_destino = resolver(grafo, origem, destinos, argumentos.iteracoes)

    saidas.imprimir_comparacao(linhas)
    saidas.salvar_comparacao(linhas)

    if not argumentos.sem_figura:
        for destino, caminho_arquivo in zip(destinos, config.CAMINHOS_FIGURAS_ROTAS):
            rotas = rotas_por_destino[destino["no"]]
            if rotas:
                saidas.salvar_figura_rotas(grafo, destino, rotas, caminho_arquivo)

    print()
    print(f"Resolução concluída. Resultados em {config.PASTA_AUXILIARES}")
    print("Dados: OpenStreetMap (ODbL). © colaboradores do OpenStreetMap.")

if __name__ == "__main__":
    main()
