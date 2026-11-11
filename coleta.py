import osmnx as ox

import config

# Carrega o grafo do arquivo local, ou baixa do OpenStreetMap e salva.
def obter_grafo(forcar_download=False):
    if config.CAMINHO_GRAFO.exists() and not forcar_download:
        print(f"Reaproveitando o grafo de {config.CAMINHO_GRAFO}")
        return ox.io.load_graphml(str(config.CAMINHO_GRAFO))

    print(f"Baixando a malha viária de {config.LUGAR!r} (leva alguns minutos)...")
    grafo = ox.graph_from_place(config.LUGAR, network_type=config.TIPO_DE_MALHA)
    grafo = calcular_pesos(grafo)

    ox.io.save_graphml(grafo, filepath=str(config.CAMINHO_GRAFO))
    print(f"Grafo salvo em {config.CAMINHO_GRAFO}")
    return grafo

# Preenche speed_kph e travel_time, o peso `w` do modelo, em cada arco.
def calcular_pesos(grafo):
    grafo = ox.routing.add_edge_speeds(
        grafo, hwy_speeds=config.VELOCIDADES_BR, fallback=config.VELOCIDADE_PADRAO
    )
    return ox.routing.add_edge_travel_times(grafo)

# Geocodifica um endereço e devolve o cruzamento mais próximo dele.
def localizar_ponto(grafo, endereco, papel):
    latitude, longitude = ox.geocode(endereco)
    # ox.geocode devolve (lat, lon); nearest_nodes espera X=longitude, Y=latitude.
    no = int(ox.distance.nearest_nodes(grafo, X=longitude, Y=latitude))
    return {
        "papel": papel,
        "endereco": endereco,
        "no": no,
        "latitude": float(grafo.nodes[no]["y"]),
        "longitude": float(grafo.nodes[no]["x"]),
    }

# Resolve o nó de origem `s` e os nós de destino `t`.
def localizar_origem_e_destinos(grafo):
    origem = localizar_ponto(grafo, config.ENDERECO_ORIGEM, "origem")
    destinos = [localizar_ponto(grafo, endereco, "destino")
                for endereco in config.ENDERECOS_DESTINO]
    return origem, destinos
