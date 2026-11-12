import csv
import json

import matplotlib.pyplot as plt
import osmnx as ox
from matplotlib.lines import Line2D

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

# Imprime as primeiras iterações do Dijkstra: o nó fechado, seu rótulo e a conta
# de cada vizinho examinado, com o veredito de cada comparação.
def imprimir_passo_a_passo(registro, peso, total_nos, limite=config.ITERACOES_EXIBIDAS):
    unidade = config.UNIDADES[peso]
    obsoletas = sum(passo["obsoletas"] for passo in registro)

    print()
    print(f"=== PASSO A PASSO — peso {peso} ===")
    print(f"Primeiras {min(limite, len(registro))} de {len(registro)} iterações. "
          "Uma iteração fecha um nó, cujo rótulo passa a ser definitivo.")
    print(f"Para cada vizinho: rótulo do nó + custo do arco = candidato, "
          f"comparado ao rótulo atual do vizinho (em {unidade}).")

    for passo in registro[:limite]:
        origem = "  (origem)" if passo["iteracao"] == 1 else ""
        print()
        print(f"[{passo['iteracao']:>3}] fecha {passo['no']}   "
              f"rótulo = {passo['rotulo']:.2f} {unidade}{origem}")

        for exame in passo["exames"]:
            rua = achatar(exame["rua"]) or "(via sem nome)"
            # Rótulo ainda infinito se o vizinho nunca foi alcançado; o próprio
            # format() imprime 'inf'.
            atual_texto = f"{exame['rotulo_atual']:.2f}"
            print(f"        {rua:<26.26} -> {exame['vizinho']:>11}   "
                  f"{passo['rotulo']:>7.2f} + {exame['custo']:>6.2f} = {exame['candidato']:>7.2f}  "
                  f"{'<' if exame['relaxado'] else '>='} {atual_texto:>7}   "
                  f"{'relaxa' if exame['relaxado'] else 'mantém'}")

    print()
    print(f"Fila: {len(registro) + obsoletas} extrações, {obsoletas} obsoletas descartadas "
          "(a fila guarda rótulos superados; o primeiro a sair é o definitivo).")
    print(f"Nós rotulados: {len(registro)} de {total_nos}. "
          f"{total_nos - len(registro)} inalcançáveis a partir de s.")

# Imprime a tabela de comparação entre a rota de menor tempo e a de menor
# distância, com o que se ganha e o que se perde em cada troca.
def imprimir_comparacao(linhas):
    print()
    print("=== COMPARAÇÃO DAS ROTAS ===")
    print(f"{'destino':<8} {'nó':>12} {'peso':<12} {'arcos':>6} {'tempo (s)':>11} {'distância (m)':>14}")
    for linha in linhas:
        print(f"{linha['destino']:<8} {linha['no']:>12} {linha['peso']:<12} "
              f"{linha['arcos']:>6} {linha['tempo_s']:>11.2f} {linha['distancia_m']:>14.2f}")

    for destino in dict.fromkeys(linha["destino"] for linha in linhas):
        por_peso = {linha["peso"]: linha for linha in linhas if linha["destino"] == destino}
        tempo = por_peso.get("travel_time")
        distancia = por_peso.get("length")
        if not tempo or not distancia:
            continue

        tempo_perdido = distancia["tempo_s"] - tempo["tempo_s"]
        metros_poupados = tempo["distancia_m"] - distancia["distancia_m"]
        print()
        print(f"{destino} ({tempo['endereco']}):")
        print(f"  rota de menor tempo      {tempo['arcos']:>3} arcos, "
              f"{tempo['tempo_s']:>7.2f} s, {tempo['distancia_m']:>8.2f} m")
        print(f"  rota de menor distância  {distancia['arcos']:>3} arcos, "
              f"{distancia['tempo_s']:>7.2f} s, {distancia['distancia_m']:>8.2f} m")
        print(f"  ir pela mais curta custa {tempo_perdido:+.2f} s "
              f"({tempo_perdido / tempo['tempo_s']:+.1%}) e poupa "
              f"{metros_poupados:.2f} m ({-metros_poupados / tempo['distancia_m']:+.1%}).")

# Grava comparacao.csv com uma linha por par (destino, peso).
def salvar_comparacao(linhas):
    with config.CAMINHO_COMPARACAO.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=config.COLUNAS_COMPARACAO)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({
                **linha,
                "tempo_s": round(linha["tempo_s"], 2),
                "distancia_m": round(linha["distancia_m"], 2),
            })
    print()
    print(f"Tabela de comparação salva em {config.CAMINHO_COMPARACAO}")

# Grava a figura de um destino com as duas rotas sobre a malha do bairro,
# seguindo a geometria real das ruas guardada no graphml.
def salvar_figura_rotas(grafo, destino, rotas, caminho_arquivo):
    pesos = [peso for peso in config.PESOS if peso in rotas]
    figura, eixo = ox.plot.plot_graph_routes(
        grafo,
        routes=[rotas[peso]["caminho"] for peso in pesos],
        route_colors=[config.ESTILOS_ROTAS[peso]["cor"] for peso in pesos],
        route_linewidths=[config.ESTILOS_ROTAS[peso]["espessura"] for peso in pesos],
        route_alpha=0.9, orig_dest_size=0,
        node_size=4, node_color="#9a9a9a", edge_color="#c4c4c4", edge_linewidth=0.8,
        bgcolor="white", figsize=(11, 11), show=False, close=False, save=False,
    )

    origem = rotas[pesos[0]]["caminho"][0]
    for no, marcador, tamanho in [(origem, "s", 130), (destino["no"], "*", 320)]:
        eixo.scatter(grafo.nodes[no]["x"], grafo.nodes[no]["y"], s=tamanho,
                     c="#111111", marker=marcador, zorder=5)

    legendas = [
        Line2D([], [], color=config.ESTILOS_ROTAS[peso]["cor"],
               linewidth=config.ESTILOS_ROTAS[peso]["espessura"],
               label=f"peso {peso}: {rotas[peso]['medidas']['arcos']} arcos, "
                     f"{rotas[peso]['medidas']['tempo']:.2f} s, "
                     f"{rotas[peso]['medidas']['distancia']:.0f} m")
        for peso in pesos
    ]
    legendas += [
        Line2D([], [], color="#111111", marker="s", linestyle="none", label=f"s = {origem}"),
        Line2D([], [], color="#111111", marker="*", markersize=11, linestyle="none",
               label=f"t = {destino['no']}"),
    ]

    eixo.set_title(
        f"Caminho mínimo — {config.LUGAR}\n{destino['endereco']}",
        color="black", fontsize=12,
    )
    eixo.legend(handles=legendas, loc="lower right", fontsize=9, framealpha=0.95)

    figura.savefig(caminho_arquivo, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    print(f"Figura salva em {caminho_arquivo}")
