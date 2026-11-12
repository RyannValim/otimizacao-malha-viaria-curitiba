# Otimização da Malha Viária de Curitiba

Projeto de Pesquisa Operacional — **Grupo 16**. Caminho mínimo entre um centro de
distribuição e o endereço do cliente, com o algoritmo de **Dijkstra**.

Duas etapas, as duas concluídas:

| Etapa | O que faz | Ponto de entrada |
|---|---|---|
| 1 | extrai a malha viária do OpenStreetMap e monta o dataset | `python extrair.py` |
| 2 | resolve o caminho mínimo com Dijkstra implementado à mão | `python resolver.py` |

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Como rodar

```powershell
python extrair.py     # Etapa 1 — só precisa rodar de novo para refazer a coleta
python resolver.py    # Etapa 2 — roda offline, sobre o grafo já salvo
python -m pytest      # valida os resultados contra os valores de referência
```

A Etapa 1 baixa a malha do OpenStreetMap na primeira execução e leva alguns
minutos; as seguintes reaproveitam o `grafo.graphml`. Use `--forcar-download`
para refazer a coleta ou `--sem-figura` para pular o `malha.png`.

A Etapa 2 não acessa a rede: lê o grafo e os pontos `s`/`t` já gravados. Aceita
`--iteracoes N` (quantas iterações do passo a passo imprimir, padrão 15) e
`--sem-figura`.

## O código

| Arquivo | O que faz |
|---|---|
| `config.py` | parâmetros: bairro, endereços, velocidades, pesos, caminhos |
| `coleta.py` | fala com o OpenStreetMap: baixa a malha e geocodifica os endereços |
| `dijkstra.py` | o algoritmo: fila de prioridade com `heapq`, sem biblioteca de caminho mínimo |
| `saidas.py` | grava os arquivos e imprime as estatísticas, o passo a passo e a comparação |
| `extrair.py` | ponto de entrada da Etapa 1 |
| `resolver.py` | ponto de entrada da Etapa 2 |
| `test_dijkstra.py` | o teste de validação |

## O algoritmo

`dijkstra.py` tem três funções e nenhuma dependência além da `heapq`: não importa
OSMnx, não imprime nada e não lê arquivo.

```python
rotulos, antecessores, registro = dijkstra(grafo, origem, peso)
caminho = reconstruir_caminho(antecessores, origem, destino)
medidas = medir_caminho(grafo, caminho, peso)
```

A fila guarda pares `(rótulo, nó)`. Quando o rótulo de um nó melhora, o par novo
é empilhado sem remover o antigo (*lazy deletion*): o primeiro par de um nó a
sair da fila é o definitivo, e os seguintes são descartados. Com `|V| = 166` e
`|A| = 326`, isso custa `O((|V| + |A|) log |V|)`.

**Uma execução por peso, não uma por destino.** O Dijkstra é de origem única:
partindo de `s`, uma única execução rotula todos os nós alcançáveis da malha, e
os dois destinos saem da mesma árvore de antecessores. Parar quando um `t`
específico sai da fila seria apenas uma otimização de parada antecipada, não um
algoritmo diferente. É o argumento da seção 7 da documentação técnica.

### O passo a passo

`resolver.py` imprime as primeiras 15 iterações de cada execução. Uma iteração
fecha um nó — seu rótulo passa a ser definitivo — e examina todos os vizinhos
dele, mostrando a conta e o veredito de cada comparação:

```
[  3] fecha 324728731   rótulo = 22.89 s
        Rua Desembargador Costa Ca ->   324728722     22.89 +  10.59 =   33.48  <     inf   relaxa
        Rua Desembargador Costa Ca ->   324728732     22.89 +  10.67 =   33.56  >=   12.21   mantém
        Rua Carmelo Rangel         ->   324728736     22.89 +  47.55 =   70.43  <     inf   relaxa
        Rua Carmelo Rangel         ->   324724619     22.89 +  17.74 =   40.63  <     inf   relaxa
```

Ao fim de cada execução sai o total: 164 nós fechados em 173 extrações da fila
(9 obsoletas descartadas), e 2 dos 166 nós inalcançáveis a partir de `s` — becos
onde a mão única impede a entrada.

## Os resultados

Origem `s = 11220213870` (Shopping Pátio Batel). Cada rota foi medida nas duas
métricas, não só naquela que a gerou:

| Destino | Peso | Arcos | Tempo | Distância |
|---|---|---|---|---|
| `t₁` 1386657461 (Desembargador Motta) | `travel_time` | 20 | **195,48 s** | 2.559,00 m |
| `t₁` 1386657461 | `length` | 19 | 207,87 s | **2.430,80 m** |
| `t₂` 324728738 (Olavo Bilac) | `travel_time` | 7 | **87,63 s** | 789,29 m |
| `t₂` 324728738 | `length` | 6 | 90,33 s | **752,74 m** |

Ir pela rota mais curta custa 12,39 s a mais (+6,3%) até `t₁` e 2,70 s (+3,1%)
até `t₂`, economizando 128 m e 37 m. As duas rotas por tempo preferem as vias
arteriais: mais metros, menos segundos — que é exatamente o que o modelo
pretende capturar ao usar `travel_time` como peso `w`.

## Validação

`python -m pytest` confere 20 asserções contra os valores de referência da seção
8 da documentação técnica, entre elas:

- tempo ótimo de 195,5 s em 20 arcos até `t₁`, e 87,6 s em 7 arcos até `t₂`;
- distância ótima de 2.431 m e 753 m;
- todo peso não negativo, hipótese que o Dijkstra exige;
- o rótulo de cada destino igual ao custo do caminho medido arco a arco;
- os rótulos fechando em ordem não decrescente;
- os nós `s`, `t₁` e `t₂` do `pontos.json` ainda sendo os do enunciado.

## Onde ficam os arquivos

**`datasets/`** — o dataset que o trabalho entrega: `nos.csv` e `arcos.csv`.

**`auxiliares/`** — o resto: o grafo salvo, os pontos `s`/`t`, as figuras, a
tabela de comparação e a documentação.

| Arquivo | |
|---|---|
| `auxiliares/grafo.graphml` | o grafo completo, com a geometria das ruas |
| `auxiliares/pontos.json` | os nós `s` e `t` |
| `auxiliares/malha.png` | figura da malha extraída |
| `auxiliares/comparacao.csv` | a tabela de resultados acima |
| `auxiliares/rotas_t1_desembargador_motta.png` | as duas rotas até `t₁` sobre o mapa |
| `auxiliares/rotas_t2_olavo_bilac.png` | as duas rotas até `t₂` sobre o mapa |
| `auxiliares/docs/DOCUMENTACAO.md` | documentação técnica completa |
| `auxiliares/docs/bairro_batel_google_maps.png` | captura do Google Maps, para comparação |

## O que é cada arquivo

**`datasets/nos.csv`** — um cruzamento por linha: `osmid` (identificador no OSM), `y`
(latitude), `x` (longitude) e `street_count` (quantas ruas incidem nele). É o
conjunto `V` do modelo.

**`datasets/arcos.csv`** — um trecho de rua por linha. É o conjunto `A` do modelo.

| Coluna | Significado |
|---|---|
| `u`, `v` | nó de origem e de destino do arco |
| `key` | distingue arcos paralelos entre o mesmo par de nós |
| `name` | nome da rua |
| `highway` | classificação da via no OSM |
| `oneway` | mão única (uma rua de mão dupla aparece como dois arcos opostos) |
| `length` | comprimento em metros (`L`) |
| `speed_kph` | velocidade da via (`v`) |
| `travel_time` | `length / speed_kph` em segundos — **o peso `w` do modelo** |

**`auxiliares/grafo.graphml`** — o grafo completo, do jeito que a OSMnx o monta. Guarda o que
os CSVs não guardam: a geometria (a curva real de cada rua), além de `lanes`,
`maxspeed` e `access`. É o arquivo que a Etapa 2 carrega, por dois motivos: evita
rebaixar tudo do OpenStreetMap a cada execução — garantindo que o Dijkstra rode
sobre exatamente os mesmos dados apresentados no checkpoint — e permite desenhar a
rota seguindo o traçado real das ruas, em vez de linhas retas entre cruzamentos.
Carregá-lo pela OSMnx não é detalhe: o GraphML guarda tudo como texto, e é a
`ox.io.load_graphml` que converte os pesos de volta para `float`.

**`auxiliares/pontos.json`** — os nós `s` (centro de distribuição) e `t` (clientes) já
resolvidos, com endereço, identificador do nó e coordenadas. É o que permite a
Etapa 2 rodar sem rede e garante que ela use os mesmos pontos do checkpoint.

**`auxiliares/comparacao.csv`** — uma linha por par (destino, peso), com número de
arcos, tempo e distância. É a tabela de resultados, gerada pelo `resolver.py`.

**`auxiliares/rotas_t*.png`** — a malha do bairro em cinza e, sobre ela, as duas
rotas até aquele destino: azul para a de menor tempo, laranja para a de menor
distância. Onde as duas coincidem, a laranja fica desenhada por dentro da azul.

## Atenção

Os endereços em `config.py` precisam estar dentro do bairro definido em `LUGAR`.
Um endereço de fora é grudado no cruzamento mais próximo da borda da malha, sem
aviso, e a rota sai falsa — confira os links que a execução imprime.

---

Dados: OpenStreetMap, sob [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
© colaboradores do OpenStreetMap. Coleta com [OSMnx](https://osmnx.readthedocs.io).
