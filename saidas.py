import json

import osmnx as ox

import config

# Colunas do OSM podem vir como lista; viram texto separado por barra.
def achatar(valor):
    if isinstance(valor, list):
        return " / ".join(str(item) for item in valor)
    return valor

# Grava nos.csv e arcos.csv, e devolve a tabela de arcos.
def salvar_tabelas(grafo):
    nos, arcos = ox.graph_to_gdfs(grafo)

    nos = nos.reindex(columns=config.COLUNAS_NOS).reset_index()
    arcos = arcos.reindex(columns=config.COLUNAS_ARCOS).reset_index()
    for coluna in ["name", "highway"]:
        arcos[coluna] = arcos[coluna].map(achatar)

    nos.to_csv(config.CAMINHO_NOS, index=False, encoding="utf-8")
    arcos.to_csv(config.CAMINHO_ARCOS, index=False, encoding="utf-8")

    print(f"nos.csv   -> {nos.shape[0]:>6} linhas, {nos.shape[1]} colunas")
    print(f"arcos.csv -> {arcos.shape[0]:>6} linhas, {arcos.shape[1]} colunas")
    return arcos

# Grava pontos.json com os nós s e t, e imprime os links para conferência.
def salvar_pontos(origem, destinos):
    print()
    print("=== ORIGEM E DESTINOS ===")
    print(f"Origem  s = {origem['no']}  ({origem['endereco']})")
    for indice, destino in enumerate(destinos, start=1):
        print(f"Destino t{indice} = {destino['no']}  ({destino['endereco']})")

    print()
    print("Confira no mapa se os pontos fazem sentido:")
    for ponto in [origem, *destinos]:
        print(f"  https://www.openstreetmap.org/#map=17/{ponto['latitude']}/{ponto['longitude']}")

    conteudo = {"lugar": config.LUGAR, "origem": origem, "destinos": destinos}
    config.CAMINHO_PONTOS.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Pontos salvos em {config.CAMINHO_PONTOS}")

# Grava malha.png, a evidência visual da coleta.
def salvar_figura(grafo):
    figura, eixo = ox.plot_graph(
        grafo, node_size=3, node_color="#4a90d9", edge_linewidth=0.5,
        edge_color="#999999", bgcolor="white", figsize=(10, 10),
        show=False, close=False,
    )
    eixo.set_title(
        f"Malha viária — {config.LUGAR}\n"
        f"{grafo.number_of_nodes()} nós, {grafo.number_of_edges()} arcos",
        color="black", fontsize=12,
    )
    figura.savefig(config.CAMINHO_FIGURA, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Figura salva em {config.CAMINHO_FIGURA}")

# Imprime os números da seção *Cenário e Dataset* do documento.
def imprimir_estatisticas(grafo, arcos):
    print()
    print("=== RESUMO DA REDE ===")
    print(f"Região:     {config.LUGAR}")
    print(f"Nós (V):    {grafo.number_of_nodes()}")
    print(f"Arcos (A):  {grafo.number_of_edges()}")
    print(f"Grau médio: {2 * grafo.number_of_edges() / grafo.number_of_nodes():.2f}")
    print(f"Extensão total da malha: {arcos['length'].sum() / 1000:.1f} km")

    print()
    print("=== PESOS (travel_time) E DIMENSÕES ===")
    print(arcos[["length", "speed_kph", "travel_time"]].describe().round(2).to_string())

    menor = arcos["travel_time"].min()
    print()
    print(f"Menor travel_time: {menor:.2f} s", end="  ")
    print("OK, hipótese do Dijkstra satisfeita." if menor >= 0
          else "ATENÇÃO: peso negativo encontrado.")

    print()
    print("=== ARCOS POR CLASSIFICAÇÃO DE VIA ===")
    print(arcos["highway"].value_counts().head(10).to_string())

    print()
    print("=== MÃO ÚNICA ===  (rua de mão dupla = dois arcos opostos)")
    print(arcos["oneway"].value_counts().to_string())
