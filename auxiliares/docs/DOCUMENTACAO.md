# Documentação técnica — Etapa 1: extração do dataset

**Projeto:** Otimização da Malha Viária de Curitiba — Pesquisa Operacional, Grupo 16
**Repositório:** `d:\codes\otimizacao-malha-viaria-curitiba`
**Data desta documentação:** 11 de novembro de 2026
**Atualizada em:** 12 de novembro de 2026, com os resultados da Etapa 2

Este documento descreve o código e os dados produzidos na Etapa 1. Todos os números
aqui foram medidos nos arquivos gerados, não estimados. A Etapa 2
(implementação do Dijkstra) está resumida na seção 12.

---

## 1. Escopo da etapa

A Etapa 1 coleta e prepara os dados; ela **não** resolve o problema de caminho
mínimo. O que ela entrega é o grafo dirigido e ponderado sobre o qual o Dijkstra
será executado, mais os nós de origem e destino já identificados.

A especificação do trabalho (`SpecsTrabalhoPO_Grupo-16.pdf`) está fora do
repositório. O código implementa o que a seção *1. Cenário e dataset* daquele
documento descreve.

---

## 2. Estrutura do repositório

```
config.py                       parâmetros do cenário
coleta.py                       comunicação com o OpenStreetMap
dijkstra.py                     o algoritmo de caminho mínimo
saidas.py                       gravação dos arquivos e estatísticas
extrair.py                      ponto de entrada da Etapa 1
resolver.py                     ponto de entrada da Etapa 2
test_dijkstra.py                validação dos resultados
requirements.txt                dependências
README.md                       instruções de uso
datasets/                       o dataset que o trabalho entrega
  nos.csv
  arcos.csv
auxiliares/                     subprodutos da extração, resultados e documentação
  grafo.graphml
  pontos.json
  malha.png
  comparacao.csv                a tabela de resultados da Etapa 2
  rotas_t1_desembargador_motta.png
  rotas_t2_olavo_bilac.png
  docs/
    DOCUMENTACAO.md             este arquivo
    bairro_batel_google_maps.png            captura do Google Maps
    Trabalho_Pesquisa-Operacional-Grupo_16.pdf
cache/                          cache HTTP da OSMnx (ignorado pelo git)
.venv/                          ambiente virtual (ignorado pelo git)
```

`datasets/` guarda apenas as duas tabelas que constituem o dataset propriamente
dito. Todo o resto que o código produz — o grafo serializado, os pontos `s`/`t`,
as figuras e a tabela de comparação — fica em `auxiliares/`, com a documentação
em `auxiliares/docs/`.

São **688 linhas de Python** em 7 arquivos.

---

## 3. Como o código funciona

### Fluxo de uma execução

`python extrair.py` executa, nesta ordem:

1. `coleta.obter_grafo()` — carrega `auxiliares/grafo.graphml` se existir; caso
   contrário baixa a malha do OpenStreetMap, calcula os pesos e salva o arquivo.
2. `saidas.salvar_tabelas(grafo)` — converte o grafo em duas tabelas e grava
   `nos.csv` e `arcos.csv`. Devolve a tabela de arcos.
3. `saidas.imprimir_estatisticas(grafo, arcos)` — imprime os números do dataset.
   Nada é gravado em arquivo.
4. `coleta.localizar_origem_e_destinos(grafo)` — geocodifica os três endereços e
   devolve os nós correspondentes.
5. `saidas.salvar_pontos(origem, destinos)` — grava `pontos.json` e imprime os
   links do OpenStreetMap para conferência manual.
6. `saidas.salvar_figura(grafo)` — grava `malha.png`.

Duas opções de linha de comando: `--forcar-download` (ignora o graphml salvo e
baixa de novo) e `--sem-figura` (pula o passo 6). Nenhuma outra. Os parâmetros do
cenário ficam exclusivamente em `config.py`.

### `config.py` (77 linhas)

Constantes, sem lógica. Define os caminhos dos arquivos de saída, o recorte
(`LUGAR = "Batel, Curitiba, Parana, Brazil"`), o tipo de malha (`"drive"`), os
endereços de origem e destino, a tabela `VELOCIDADES_BR` e as listas de colunas
exportadas. A segunda metade do arquivo é da Etapa 2: os dois pesos comparados
(`PESOS`), o estilo de cada rota nas figuras e quantas iterações do passo a passo
imprimir.

### `coleta.py` (44 linhas)

Isola tudo que depende de rede. Quatro funções:

- `obter_grafo(forcar_download=False)` — decide entre ler o arquivo local e baixar.
- `calcular_pesos(grafo)` — chama `ox.routing.add_edge_speeds` e
  `ox.routing.add_edge_travel_times`.
- `localizar_ponto(grafo, endereco, papel)` — geocodifica e acha o nó mais próximo.
  Devolve um dicionário com `papel`, `endereco`, `no`, `latitude`, `longitude`.
- `localizar_origem_e_destinos(grafo)` — aplica a anterior aos três endereços.

### `saidas.py` (213 linhas)

Tudo que grava arquivo ou imprime, de ambas as etapas, e nada que use rede. Da
Etapa 1: `achatar`, `salvar_tabelas`, `salvar_pontos`, `salvar_figura` e
`imprimir_estatisticas`. Da Etapa 2: `imprimir_passo_a_passo`,
`imprimir_comparacao`, `salvar_comparacao` e `salvar_figura_rotas`.

### `extrair.py` (38 linhas)

Apenas `main()`: monta o `argparse`, cria a pasta de saída e chama as funções
acima na ordem descrita.

### `dijkstra.py` (83 linhas)

O algoritmo, descrito na seção 12. Não importa OSMnx, não imprime e não lê
arquivo: só `heapq` e o grafo que recebe.

### `resolver.py` (100 linhas)

Ponto de entrada da Etapa 2. Carrega o grafo e o `pontos.json`, roda o Dijkstra
uma vez por peso, monta a tabela de comparação e manda o `saidas.py` gravar.
Duas opções: `--iteracoes N` e `--sem-figura`. Não acessa a rede.

### `test_dijkstra.py` (133 linhas)

As 20 asserções que validam os resultados contra os valores da seção 8.

---

## 4. Como o peso do modelo é calculado

O custo `w` de cada arco é o **tempo de travessia em segundos**:

```
travel_time = length / speed_kph    (convertido para segundos)
```

`length` vem do OpenStreetMap, em metros. `speed_kph` é resolvido assim:

1. Se o trecho tem `maxspeed` preenchido no OSM, esse valor é usado.
2. Caso contrário, aplica-se a velocidade da classificação da via, pela tabela
   `VELOCIDADES_BR` em `config.py`, baseada nos limites urbanos brasileiros:

| Classificação | km/h | Classificação | km/h |
|---|---|---|---|
| `motorway` | 90 | `residential` | 30 |
| `trunk` | 70 | `living_street` | 20 |
| `primary` | 60 | `unclassified` | 30 |
| `secondary` | 50 | `service` | 20 |
| `tertiary` | 40 | *demais* | 40 (`VELOCIDADE_PADRAO`) |

No dataset atual, **202 dos 326 arcos (62%) têm `maxspeed` vindo do OSM**; os
demais 124 receberam a velocidade da tabela.

Passar essa tabela não é apenas uma conveniência: a função `add_edge_speeds` da
OSMnx levanta `ValueError` se nenhum trecho da região tiver `maxspeed` preenchido,
situação comum em áreas mapeadas de forma incompleta no Brasil. Informar
`hwy_speeds` e `fallback` torna o código robusto e o critério auditável.

**Consequência para o modelo:** como `length ≥ 0` e `speed_kph > 0`, todo
`travel_time` é não negativo. O menor valor observado no dataset é **0,48 s**. A
hipótese de não negatividade exigida pelo Dijkstra está satisfeita.

---

## 5. Os dados produzidos

### Procedência

OpenStreetMap, sob Open Database License (ODbL), © colaboradores do OpenStreetMap.
A coleta usa a biblioteca OSMnx 2.1.1: o nome do bairro vai ao Nominatim, que
devolve o polígono; o polígono vira consulta à Overpass API, que devolve as vias; a
OSMnx monta o grafo dirigido.

### `datasets/nos.csv` — 166 linhas, 6.221 bytes

Um cruzamento ou extremidade de via por linha. É o conjunto `V` do modelo.

| Coluna | Tipo | Significado |
|---|---|---|
| `osmid` | int | identificador do nó no OpenStreetMap |
| `y` | float | latitude |
| `x` | float | longitude |
| `street_count` | int | número de ruas incidentes no cruzamento |

```csv
osmid,y,x,street_count
267191327,-25.4421697,-49.2824551,3
267191331,-25.4444126,-49.2881283,4
```

### `datasets/arcos.csv` — 326 linhas, 34.257 bytes

Um trecho de rua dirigido por linha. É o conjunto `A` do modelo.

| Coluna | Tipo | Significado |
|---|---|---|
| `u` | int | nó de origem do arco |
| `v` | int | nó de destino do arco |
| `key` | int | distingue arcos paralelos entre o mesmo par de nós |
| `name` | str | nome da rua (3 valores nulos) |
| `highway` | str | classificação da via no OSM |
| `oneway` | bool | mão única |
| `length` | float | comprimento em metros (`L` do modelo) |
| `speed_kph` | float | velocidade da via (`v` do modelo) |
| `travel_time` | float | **peso `w` do modelo**, em segundos |

```csv
u,v,key,name,highway,oneway,length,speed_kph,travel_time
267191327,1738398147,0,Avenida Visconde de Guarapuava,primary_link,True,16.984627064914687,30.0,2.0381552477897626
267191331,267191333,0,Avenida Visconde de Guarapuava,primary,True,187.38924434132355,50.0,13.492025592575295
```

Uma rua de mão dupla aparece como **dois arcos opostos**, não como um arco
bidirecional — por isso o grafo é dirigido e a rota encontrada é efetivamente
dirigível.

### `auxiliares/grafo.graphml` — 200.009 bytes

O grafo completo serializado, como a OSMnx o monta. Contém atributos que os CSVs
não exportam:

| Atributo | Arcos que o possuem |
|---|---|
| `osmid`, `highway`, `oneway`, `reversed`, `length`, `speed_kph`, `travel_time` | 326 (todos) |
| `name` | 323 |
| `lanes` | 235 |
| `maxspeed` | 202 |
| `geometry` | 191 |
| `access` | 9 |

Dois papéis:

1. **Reprodutibilidade.** Evita rebaixar da Overpass a cada execução e garante que
   a Etapa 2 rode sobre exatamente os mesmos dados apresentados no checkpoint. O
   OpenStreetMap é uma base viva: uma coleta feita daqui a semanas pode diferir.
2. **Geometria.** Os 191 arcos com `geometry` guardam a curva real da rua entre
   dois cruzamentos. Sem isso, ao desenhar a rota sobre o mapa, as ruas apareceriam
   como linhas retas ligando cruzamentos.

Carrega-se com `ox.io.load_graphml("auxiliares/grafo.graphml")`.

### `auxiliares/pontos.json` — 667 bytes

Os nós `s` e `t` já resolvidos, para a Etapa 2 não precisar geocodificar de novo e
para garantir que use os mesmos pontos do checkpoint.

```json
{
  "lugar": "Batel, Curitiba, Parana, Brazil",
  "origem": {
    "papel": "origem",
    "endereco": "Shopping Pátio Batel, Curitiba, Parana, Brazil",
    "no": 11220213870,
    "latitude": -25.4425462,
    "longitude": -49.2915118
  },
  "destinos": [
    { "papel": "destino", "endereco": "Rua Desembargador Motta, ...", "no": 1386657461, ... },
    { "papel": "destino", "endereco": "Rua Olavo Bilac, ...",        "no": 324728738,  ... }
  ]
}
```

### `auxiliares/malha.png` — 203.155 bytes

Figura da malha completa, 10×10 polegadas a 200 dpi, com título indicando região,
número de nós e número de arcos. Evidência visual da coleta.

---

## 6. Números do dataset

Medidos nos arquivos atuais. Podem ser citados diretamente na seção *Cenário e
Dataset* do documento acadêmico.

| Medida | Valor |
|---|---|
| Recorte | Bairro Batel, Curitiba, Paraná |
| Nós (`\|V\|`) | 166 |
| Arcos (`\|A\|`) | 326 |
| Grafo dirigido | sim |
| Grau médio | 3,93 |
| Extensão total da malha | 37,1 km |
| Caixa envolvente | lat −25,4484 a −25,4345; lon −49,2989 a −49,2777 |
| Ruas nomeadas distintas | 46 |
| Componentes fracamente conexas | 1 |
| Componentes fortemente conexas | 4 (tamanhos: 163, 1, 1, 1) |

### Distribuição dos pesos

```
       length  speed_kph  travel_time
count  326.00     326.00       326.00
mean   113.78      40.18        10.89
std     66.89       9.48         7.38
min      7.50      20.00         0.48
25%     65.10      30.00         5.32
50%    119.37      40.00        10.00
75%    148.17      50.00        14.78
max    405.93      60.00        48.71
```

### Composição da malha

| Classificação | Arcos | | Mão única | Arcos |
|---|---|---|---|---|
| `residential` | 127 | | `True` | 192 |
| `secondary` | 89 | | `False` | 134 |
| `primary` | 51 | | | |
| `tertiary` | 42 | | | |
| `busway` | 9 | | | |
| `primary_link` | 8 | | | |

---

## 7. Correspondência com a modelagem do PDF

| Símbolo no documento | Onde está nos dados |
|---|---|
| `V` — conjunto dos nós | linhas de `nos.csv`; nós do `grafo.graphml` |
| `A` — conjunto dos arcos dirigidos | linhas de `arcos.csv` |
| `s` — origem (centro de distribuição) | `pontos.json` → `origem.no` = `11220213870` |
| `t` — destino (cliente) | `pontos.json` → `destinos[i].no` |
| `L` — comprimento do arco | coluna `length`, em metros |
| `v` — velocidade permitida | coluna `speed_kph`, em km/h |
| `w = L / v` — custo do arco | coluna `travel_time`, em segundos |

### Dois destinos em vez de um

O PDF descreve o modelo com um único par `s`→`t`. O dataset traz **dois destinos**,
e isso não altera a modelagem: o Dijkstra é de **origem única**, então uma execução
a partir de `s` produz o rótulo de caminho mínimo para todos os nós da malha ao
mesmo tempo. Parar quando `t` sai da fila é apenas uma otimização de parada
antecipada. Dois clientes atendidos a partir do mesmo centro de distribuição são
duas aplicações independentes do mesmo modelo `s`→`t`.

Não se trata de roteirização com sequência de visitas, que seria o problema do
caixeiro viajante — explicitamente descartado na seção *Alternativas descartadas*
do PDF.

### Cenário adotado

| Papel | Endereço | Nó |
|---|---|---|
| Origem (`s`) | Shopping Pátio Batel | 11220213870 |
| Destino (`t₁`) | Rua Desembargador Motta | 1386657461 |
| Destino (`t₂`) | Rua Olavo Bilac | 324728738 |

---

## 8. Valores de referência para validar a Etapa 2

Calculados com o `nx.shortest_path_length` do NetworkX sobre `grafo.graphml`, com
`weight="travel_time"`. **A implementação própria do Dijkstra deve reproduzir estes
valores.** Se divergir, há erro na implementação.

| Rota | Tempo mínimo | Arcos | Distância mínima |
|---|---|---|---|
| `s` → `t₁` (Desembargador Motta) | 195,5 s | 20 | 2.431 m |
| `s` → `t₂` (Olavo Bilac) | 87,6 s | 7 | 753 m |

**Reproduzidos.** O `dijkstra.py` chega a 195,48 s e 87,63 s, com 20 e 7 arcos, e
a 2.430,80 m e 752,74 m quando o peso é `length`. O `test_dijkstra.py` falha se
algum desses números sair da tolerância de 0,05 s e 0,5 m, ou se a contagem de
arcos mudar.

Ambos os destinos são alcançáveis a partir de `s`: os três nós estão na componente
fortemente conexa principal, que contém 163 dos 166 nós. A partir de `s`, 164 dos
166 nós recebem rótulo finito — os outros dois são extremidades onde a mão única
impede a entrada.

---

## 9. Decisões tomadas e suas justificativas

| Decisão | Justificativa |
|---|---|
| Recorte por bairro, não pela cidade | Curitiba inteira gera ~130 mil arcos, ~91 MB. Inviabiliza inspeção manual e versionamento no git (o GitHub bloqueia arquivos acima de 100 MB). O Batel dá 326 arcos, conferíveis à mão. |
| `travel_time` como peso, `length` como comparação | O tempo é o compromisso da operação de entrega com o cliente. Rodar o mesmo modelo com `length` mede quanto se ganha em relação à rota de menor distância. |
| Tabela de velocidades explícita | Evita o `ValueError` da OSMnx em regiões sem `maxspeed` e torna o critério auditável: dá para dizer de onde veio cada velocidade. |
| `grafo.graphml` versionado | Reprodutibilidade entre checkpoint e entrega final, e preservação da geometria das ruas. |
| Datasets versionados no git | O grupo e o professor acessam os mesmos dados sem rodar a coleta. Total de 434 KB entre `datasets/` e `auxiliares/`. |
| Reuso do graphml por padrão | A Overpass API é lenta e tem limite de requisições. |
| Dois destinos | Explorar mais de um par origem–destino sem custo adicional de execução (ver seção 7). |
| Sem validação de endereço no código | Avaliada e descartada: exigiria uma consulta extra ao Nominatim e `shapely` para proteger um cenário fixo. O limite está documentado em vez de imposto (ver seção 10). |

---

## 10. Limitações conhecidas

**Endereço fora do recorte não é detectado.** `ox.distance.nearest_nodes` sempre
devolve algum nó. Um endereço de outro bairro seria grudado silenciosamente no
cruzamento mais próximo da borda da malha, e a rota resultante pareceria válida sem
ser. Por isso o código imprime os links do OpenStreetMap de cada ponto ao final: a
conferência é manual. Há avisos nesse sentido em `config.py` e no `README.md`.

**O destino `t₁` está na borda.** O nó 1386657461 tem longitude −49,2777111, que é
exatamente o limite leste da malha extraída. Isso é o sintoma típico de um endereço
que o Nominatim resolveu num ponto fora do Batel. A rota até ele existe e tem
195,5 s, mas vale considerar trocar esse destino por uma rua mais central antes da
Etapa 2.

**3 nós isolados.** O grafo tem 4 componentes fortemente conexas: uma com 163 nós e
três com 1 nó cada. Esses três são becos ou extremidades em que a mão única impede
entrada ou saída. Não afetam o cenário atual, já que `s`, `t₁` e `t₂` estão todos na
componente principal.

**Dependência de rede.** A geocodificação dos três endereços acontece em toda
execução, mesmo quando o grafo é reaproveitado do arquivo local. Sem internet, o
script falha nesse ponto, depois de já ter gravado os CSVs.

**`scikit-learn` é obrigatório.** A OSMnx o trata como dependência opcional, mas
`nearest_nodes` o exige para buscar em grafo não projetado. Sem ele, a execução
falha com `ImportError` após gravar os CSVs. Está no `requirements.txt`.

---

## 11. Ambiente

Python 3.14 em Windows 11, dentro de `.venv`. Dependências em `requirements.txt`:

```
osmnx>=2.0,<3.0        consulta Nominatim/Overpass e monta o grafo viário
pandas>=2.0            tabelas de nós e arcos
matplotlib>=3.8        figura da malha
networkx>=3.0          estrutura de grafo usada pelo osmnx
geopandas>=1.0         graph_to_gdfs devolve GeoDataFrames
scikit-learn>=1.4      exigido por nearest_nodes
```

Versões efetivamente instaladas na coleta que gerou estes dados: OSMnx 2.1.1,
GeoPandas 1.2.0.

---

## 12. O que a Etapa 2 entregou

### O algoritmo

`dijkstra.py` implementa o algoritmo à mão, com `heapq` — sem
`nx.shortest_path` nem qualquer solver pronto. Três funções:

| Função | O que faz |
|---|---|
| `dijkstra(grafo, origem, peso)` | devolve `(rotulos, antecessores, registro)` |
| `reconstruir_caminho(antecessores, origem, destino)` | remonta a sequência de nós; `None` se inalcançável |
| `medir_caminho(grafo, caminho, peso)` | mede arcos, tempo e distância do caminho |

A fila de prioridade guarda pares `(rótulo, nó)`. Quando um rótulo melhora, o par
novo é empilhado sem remover o antigo — *lazy deletion*: o primeiro par de um nó a
sair da fila é o definitivo, e os seguintes são descartados. São 173 extrações
para 164 nós fechados com `travel_time`, e 170 para os mesmos 164 com `length`.
O custo é `O((|V| + |A|) log |V|)`, aqui com `|V| = 166` e `|A| = 326`.

Entre arcos paralelos — mesmo par de nós, `key` diferente — vale o mais barato
pelo peso em uso. Este grafo não tem nenhum, mas o `MultiDiGraph` admite.

### Uma execução por peso, não uma por destino

O Dijkstra é de origem única. Partindo de `s`, **uma** execução rotula todos os
nós alcançáveis, e os dois destinos saem da mesma árvore de antecessores — é o
argumento da seção 7. Parar quando um `t` específico sai da fila seria apenas uma
otimização de parada antecipada, não outro algoritmo. Por isso o `resolver.py`
roda duas vezes, uma por peso, e não quatro.

### O passo a passo

`dijkstra()` não imprime: devolve o `registro`, uma lista com um dicionário por
iteração — o nó fechado, seu rótulo definitivo, quantas extrações obsoletas foram
descartadas antes dele, e todos os vizinhos examinados com a conta
(`rótulo + custo = candidato`), o rótulo que o vizinho tinha e o veredito
(`relaxa` ou `mantém`). Quem formata é o `saidas.imprimir_passo_a_passo`, que
mostra as primeiras 15 iterações de cada execução.

Separar o registro da impressão deixa o algoritmo testável sem capturar `stdout`
e permite imprimir 15 ou 200 iterações sem tocar nele.

### Os resultados

Cada rota foi medida nas duas métricas, não só naquela que a gerou:

| Destino | Peso | Arcos | Tempo | Distância |
|---|---|---|---|---|
| `t₁` (Desembargador Motta) | `travel_time` | 20 | **195,48 s** | 2.559,00 m |
| `t₁` | `length` | 19 | 207,87 s | **2.430,80 m** |
| `t₂` (Olavo Bilac) | `travel_time` | 7 | **87,63 s** | 789,29 m |
| `t₂` | `length` | 6 | 90,33 s | **752,74 m** |

Ir pela rota mais curta custa 12,39 s a mais (+6,3%) até `t₁` e 2,70 s (+3,1%)
até `t₂`, poupando 128 m e 37 m. As rotas por tempo preferem as vias arteriais:
mais metros, menos segundos. É exatamente o efeito que o modelo pretende
capturar ao adotar `travel_time` como peso `w` em vez de `length`.

A tabela sai em `auxiliares/comparacao.csv`, uma linha por par (destino, peso).

### As figuras

`auxiliares/rotas_t1_desembargador_motta.png` e `rotas_t2_olavo_bilac.png`: a
malha do bairro em cinza e, sobre ela, as duas rotas daquele destino — azul para
a de menor tempo, laranja para a de menor distância. O traçado segue a curva real
das ruas, lida do atributo `geometry` do graphml (seção 5); onde as duas rotas
coincidem, a laranja é desenhada por dentro da azul, mais fina, para que ambas
continuem visíveis.

### A validação

`python -m pytest` roda 20 asserções em `test_dijkstra.py`: os tempos e as
distâncias ótimas da seção 8, a contagem de arcos, a não negatividade dos pesos,
a igualdade entre o rótulo do destino e o custo do caminho medido arco a arco, a
ordem não decrescente dos rótulos fechados, o alcance de 164 dos 166 nós, e a
conferência de que os nós `s`, `t₁` e `t₂` do `pontos.json` continuam sendo os do
enunciado.

### Fluxo de uma execução

`python resolver.py` executa, nesta ordem:

1. `carregar_grafo()` — lê `auxiliares/grafo.graphml` pela `ox.io.load_graphml`,
   que converte de volta para `float` os pesos que o GraphML guarda como texto.
2. `carregar_pontos()` — lê `auxiliares/pontos.json`, sem geocodificar de novo.
3. `resolver()` — para cada peso, roda o Dijkstra, imprime o passo a passo e
   extrai os dois caminhos da árvore de antecessores.
4. `saidas.imprimir_comparacao()` e `saidas.salvar_comparacao()`.
5. `saidas.salvar_figura_rotas()` para cada destino, salvo com `--sem-figura`.

Nenhum desses passos acessa a rede.
