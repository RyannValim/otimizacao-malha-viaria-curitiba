# Documentação técnica — Etapa 1: extração do dataset

**Projeto:** Otimização da Malha Viária de Curitiba — Pesquisa Operacional, Grupo 16
**Repositório:** `d:\codes\up\otimizacao-malha-viaria-curitiba`
**Data desta documentação:** 11 de novembro de 2026

Este documento descreve o código e os dados produzidos na Etapa 1. Todos os números
aqui foram medidos nos arquivos gerados, não estimados. A Etapa 2
(implementação do Dijkstra) ainda não começou.

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
saidas.py                       gravação dos arquivos e estatísticas
extrair.py                      ponto de entrada
requirements.txt                dependências
README.md                       instruções de uso
datasets/                       o dataset que o trabalho entrega
  nos.csv
  arcos.csv
auxiliares/                     subprodutos da extração e documentação
  grafo.graphml
  pontos.json
  malha.png
  malha_batel_google_maps.png   captura do Google Maps, para comparação visual
  DOCUMENTACAO.md               este arquivo
cache/                          cache HTTP da OSMnx (ignorado pelo git)
.venv/                          ambiente virtual (ignorado pelo git)
```

`datasets/` guarda apenas as duas tabelas que constituem o dataset propriamente
dito. Todo o resto que a extração produz — o grafo serializado, os pontos `s`/`t`
e a figura — fica em `auxiliares/`.

São **242 linhas de Python** em 4 arquivos.

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

### `config.py` (45 linhas)

Constantes, sem lógica. Define os caminhos dos cinco arquivos de saída, o recorte
(`LUGAR = "Batel, Curitiba, Parana, Brazil"`), o tipo de malha (`"drive"`), os
endereços de origem e destino, a tabela `VELOCIDADES_BR` e as listas de colunas
exportadas.

### `coleta.py` (52 linhas)

Isola tudo que depende de rede. Quatro funções:

- `obter_grafo(forcar_download=False)` — decide entre ler o arquivo local e baixar.
- `calcular_pesos(grafo)` — chama `ox.routing.add_edge_speeds` e
  `ox.routing.add_edge_travel_times`.
- `localizar_ponto(grafo, endereco, papel)` — geocodifica e acha o nó mais próximo.
  Devolve um dicionário com `papel`, `endereco`, `no`, `latitude`, `longitude`.
- `localizar_origem_e_destinos(grafo)` — aplica a anterior aos três endereços.

### `saidas.py` (96 linhas)

Cinco funções: `achatar`, `salvar_tabelas`, `salvar_pontos`, `salvar_figura` e
`imprimir_estatisticas`. Nenhuma faz chamada de rede.

### `extrair.py` (49 linhas)

Apenas `main()`: monta o `argparse`, cria a pasta de saída e chama as funções
acima na ordem descrita.

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

| Rota | Tempo mínimo |
|---|---|
| `s` → `t₁` (Desembargador Motta) | 195,5 s |
| `s` → `t₂` (Olavo Bilac) | 87,6 s |

Ambos os destinos são alcançáveis a partir de `s`: os três nós estão na componente
fortemente conexa principal, que contém 163 dos 166 nós.

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

## 12. O que falta para a Etapa 2

1. Implementar o Dijkstra com `heapq`, lendo `auxiliares/grafo.graphml` e
   `auxiliares/pontos.json`.
2. Executar duas vezes para cada destino: uma com `travel_time`, outra com
   `length`, e comparar as rotas.
3. Sobrepor as rotas ao mapa do bairro (a geometria do graphml permite traçado
   real das ruas).
4. Validar os tempos contra os valores de referência da seção 8.
