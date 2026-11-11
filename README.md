# Otimização da Malha Viária de Curitiba

Projeto de Pesquisa Operacional — **Grupo 16**. Caminho mínimo entre um centro de
distribuição e o endereço do cliente, com o algoritmo de **Dijkstra**.

Etapa atual: **extração do dataset**. O Dijkstra vem na Etapa 2.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Como rodar

```powershell
python extrair.py
```

A primeira execução baixa a malha do OpenStreetMap e leva alguns minutos. As
seguintes reaproveitam o `grafo.graphml` já salvo. Use `--forcar-download` para
refazer a coleta ou `--sem-figura` para pular o `malha.png`.

## O código

| Arquivo | O que faz |
|---|---|
| `config.py` | parâmetros: bairro, endereços, velocidades, caminhos |
| `coleta.py` | fala com o OpenStreetMap: baixa a malha e geocodifica os endereços |
| `saidas.py` | grava os arquivos e imprime as estatísticas |
| `extrair.py` | chama os três na ordem |

## Onde ficam os arquivos

**`datasets/`** — o dataset que o trabalho entrega: `nos.csv` e `arcos.csv`.

**`auxiliares/`** — o resto: o grafo salvo, os pontos `s`/`t`, as figuras e a
documentação técnica.

| Arquivo | |
|---|---|
| `auxiliares/grafo.graphml` | o grafo completo, com a geometria das ruas |
| `auxiliares/pontos.json` | os nós `s` e `t` |
| `auxiliares/malha.png` | figura da malha extraída |
| `auxiliares/malha_batel_google_maps.png` | captura do Google Maps, para comparação |
| `auxiliares/DOCUMENTACAO.md` | documentação técnica completa |

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

**`auxiliares/pontos.json`** — os nós `s` (centro de distribuição) e `t` (clientes) já
resolvidos, com endereço, identificador do nó e coordenadas. Evita que a Etapa 2
precise geocodificar de novo e garante que ela use os mesmos pontos do checkpoint.

**`auxiliares/malha.png`** — figura da malha viária, evidência visual da coleta para o
documento.

## Atenção

Os endereços em `config.py` precisam estar dentro do bairro definido em `LUGAR`.
Um endereço de fora é grudado no cruzamento mais próximo da borda da malha, sem
aviso, e a rota sai falsa — confira os links que a execução imprime.

---

Dados: OpenStreetMap, sob [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
© colaboradores do OpenStreetMap. Coleta com [OSMnx](https://osmnx.readthedocs.io).
