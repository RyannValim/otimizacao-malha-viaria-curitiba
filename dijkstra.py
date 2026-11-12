import heapq

INFINITO = float("inf")

# Executa o Dijkstra a partir de `origem` e devolve rótulos, antecessores e o
# registro de cada iteração. Implementação própria: nada de nx.shortest_path.
def dijkstra(grafo, origem, peso):
    rotulos = {origem: 0.0}
    antecessores = {}
    fechados = set()
    registro = []
    obsoletas = 0
    fila = [(0.0, origem)]

    while fila:
        rotulo, no = heapq.heappop(fila)

        # Lazy deletion: a fila guarda rótulos antigos do mesmo nó. O primeiro a
        # sair é o definitivo; os outros já foram superados e são descartados.
        if no in fechados:
            obsoletas += 1
            continue

        fechados.add(no)
        exames = []

        for vizinho, arcos in grafo[no].items():
            # Entre arcos paralelos (mesmo par de nós), vale o mais barato.
            arco = min(arcos.values(), key=lambda dados: dados[peso])
            custo = float(arco[peso])
            candidato = rotulo + custo
            rotulo_atual = rotulos.get(vizinho, INFINITO)
            relaxado = candidato < rotulo_atual

            if relaxado:
                rotulos[vizinho] = candidato
                antecessores[vizinho] = no
                heapq.heappush(fila, (candidato, vizinho))

            exames.append({
                "vizinho": vizinho,
                "rua": arco.get("name"),
                "custo": custo,
                "candidato": candidato,
                "rotulo_atual": rotulo_atual,
                "relaxado": relaxado,
            })

        registro.append({
            "iteracao": len(fechados),
            "no": no,
            "rotulo": rotulo,
            "obsoletas": obsoletas,
            "exames": exames,
        })
        obsoletas = 0

    return rotulos, antecessores, registro

# Remonta o caminho de `origem` até `destino` seguindo os antecessores de trás
# para frente. Devolve None se o destino não foi alcançado.
def reconstruir_caminho(antecessores, origem, destino):
    if destino != origem and destino not in antecessores:
        return None

    caminho = [destino]
    while caminho[-1] != origem:
        caminho.append(antecessores[caminho[-1]])
    caminho.reverse()
    return caminho

# Mede tempo e distância de um caminho já encontrado, usando os mesmos arcos que
# o Dijkstra percorreu com `peso`.
def medir_caminho(grafo, caminho, peso):
    tempo = 0.0
    distancia = 0.0

    for no, proximo in zip(caminho, caminho[1:]):
        arco = min(grafo[no][proximo].values(), key=lambda dados: dados[peso])
        tempo += float(arco["travel_time"])
        distancia += float(arco["length"])

    return {"arcos": len(caminho) - 1, "tempo": tempo, "distancia": distancia}
