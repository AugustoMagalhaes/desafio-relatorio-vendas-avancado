[English](README.md) | **Português**

# sales-cli

[![CI](https://github.com/AugustoMagalhaes/desafio-relatorio-vendas-avancado/actions/workflows/ci.yml/badge.svg)](https://github.com/AugustoMagalhaes/desafio-relatorio-vendas-avancado/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/AugustoMagalhaes/desafio-relatorio-vendas-avancado/graph/badge.svg)](https://codecov.io/gh/AugustoMagalhaes/desafio-relatorio-vendas-avancado)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![basedpyright - checked](https://img.shields.io/badge/basedpyright-checked-42b983)](https://docs.basedpyright.com)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

Ferramenta de linha de comando que lê um arquivo CSV de vendas e gera um relatório com o total por produto, o valor total das vendas e o produto mais vendido, em texto formatado ou JSON, com filtro opcional por período.

O pacote se chama `sales-cli` e o comando instalado é `vendas-cli`.

## Funcionalidades

- Leitura de CSV apenas com a biblioteca padrão (`csv`, `argparse`, `logging`), sem dependências de execução.
- Total de vendas por produto, valor total e produto mais vendido.
- Filtro por intervalo de datas (`--start` e `--end`).
- Saída em tabela de texto ou JSON (`--format text|json`).
- Tolerância a variações nos arquivos: codificação, delimitador, nomes de colunas, formatos de data e de número.
- Logs claros na saída de erro, sem misturar com o relatório.

## Requisitos

Python 3.10 ou superior. Não há dependências de execução.

## Instalação

### Com ambiente virtual

```bash
git clone https://github.com/AugustoMagalhaes/desafio-relatorio-vendas-avancado.git
cd desafio-relatorio-vendas-avancado

python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

No Windows, a ativação do ambiente é `.venv\Scripts\activate`.

Para desenvolvimento (testes, lint e tipos), use a instalação editável com as dependências de desenvolvimento:

```bash
python -m pip install -e ".[dev]"
```

### Com Docker

```bash
docker build -t sales-cli .
```

## Uso

```bash
vendas-cli vendas.csv --format text
vendas-cli vendas.csv --format json --start 2025-01-01 --end 2025-03-31
```

Com Docker, o CSV é lido de um volume montado em `/data`:

```bash
docker run --rm -v "$PWD:/data:ro" sales-cli vendas.csv --format json
```

Sem argumentos, a imagem exibe a ajuda. Para ver os logs coloridos no contêiner, adicione `-t` ao `docker run`.

Também é possível executar o pacote como módulo, sem usar o comando instalado:

```bash
python -m sales_cli vendas.csv
```

### Opções

| Opção | Descrição |
| --- | --- |
| `path` | Caminho do arquivo CSV (obrigatório). |
| `-f`, `--format {text,json}` | Formato de saída. Padrão: `text`. |
| `--start DATA` | Inclui apenas vendas nesta data ou depois (inclusive). |
| `--end DATA` | Inclui apenas vendas nesta data ou antes (inclusive). |
| `-v`, `--verbose` | Mostra mensagens de depuração. |
| `-q`, `--quiet` | Mostra apenas avisos e erros. |
| `--version` | Mostra a versão. |
| `-h`, `--help` | Mostra a ajuda. |

`--verbose` e `--quiet` não podem ser usados juntos, e `--start` não pode ser posterior a `--end`.

## Exemplo de saída

Texto:

```
$ vendas-cli examples/sales_sample.csv
Product  | Units | Revenue
---------+-------+--------
Tênis    |     1 |  199.90
Calça    |     2 |  199.80
Camiseta |     4 |  199.60

Grand total: 599.30
Best seller (units): Camiseta (4 sold)
Best seller (revenue): Tênis (199.90)
```

JSON:

```
$ vendas-cli examples/sales_with_dates.csv --format json --start 2025-01-01 --end 2025-03-31
{
  "products": [
    {
      "product": "Tênis",
      "quantity": 1,
      "revenue": 199.9
    },
    {
      "product": "Calça",
      "quantity": 2,
      "revenue": 199.8
    },
    {
      "product": "Camiseta",
      "quantity": 4,
      "revenue": 199.6
    }
  ],
  "grand_total": 599.3,
  "best_seller_by_units": {
    "product": "Camiseta",
    "quantity": 4,
    "revenue": 199.6
  },
  "best_seller_by_revenue": {
    "product": "Tênis",
    "quantity": 1,
    "revenue": 199.9
  }
}
```

O relatório é escrito na saída padrão e os logs na saída de erro, então é possível redirecionar apenas o relatório:

```bash
vendas-cli vendas.csv --format json > relatorio.json
```

## Formato do CSV

### Arquivo

- **Codificação:** UTF-8 (com ou sem BOM), Windows-1252 ou Latin-1, detectada automaticamente.
- **Delimitador:** `;`, `,` ou tabulação, detectado a partir do cabeçalho.
- **Linhas em branco** são ignoradas.

### Colunas

O nome da coluna é comparado sem diferenciar maiúsculas, acentos e espaços, e a ordem das colunas não importa. Colunas extras são ignoradas. São aceitos nomes em português e em inglês.

| Campo | Obrigatório | Nomes aceitos |
| --- | --- | --- |
| Produto | Sim | `produto`, `product`, `item`, `nome_produto` |
| Quantidade | Sim | `quantidade`, `quantity`, `qtd`, `qtde`, `qty` |
| Preço unitário | Sim | `preco_unitario`, `unit_price`, `preco`, `price`, `valor_unitario` |
| Data | Não | `data`, `date`, `data_venda`, `data_da_venda`, `sale_date` |

Exemplo:

```
data;produto;quantidade;preço unitário
2025-03-01;Mouse;2;50,00
01/03/2025;Teclado;1;150,00
```

### Valores

- **Quantidade:** número inteiro não negativo (`3` e `3.0` são aceitos).
- **Preço:** número não negativo, com ou sem o prefixo `R$`. Aceita `1234.50`, `10,5` e `1.234,50`.
- **Datas:** `AAAA-MM-DD`, `AAAA/MM/DD`, `AAAA.MM.DD`, `DD/MM/AAAA`, `DD-MM-AAAA`, `DD.MM.AAAA`, `DD/MM/AA`, `MM/DD/AAAA` e `MM-DD-AAAA`. Uma parte de horário é ignorada. Quando o formato é ambíguo (por exemplo `01/02/2025`), o dia vem primeiro.
- **Produtos** com a mesma grafia, sem diferenciar maiúsculas de minúsculas, são somados.

### Linhas inválidas

Uma linha inválida (produto vazio, quantidade ou preço inválidos) é ignorada, e um único aviso informa quantas foram ignoradas. Use `-v` para ver o motivo e o número de cada uma.

## Filtro por data

- Sem `--start` e `--end`, todas as vendas são consideradas.
- Se **nenhuma** venda tiver data reconhecida, o filtro é ignorado, todas as vendas são mantidas e um aviso é exibido.
- Se **algumas** vendas não tiverem data, elas ficam de fora do período e um aviso informa quantas.
- Se nenhuma venda estiver no período, o relatório vem vazio, com um aviso.

## Produto mais vendido

O enunciado não define o critério, então o relatório mostra os dois: o produto com mais **unidades** vendidas (desempate pela maior receita e depois pelo nome) e o de maior **receita**.

## Códigos de saída

| Código | Significado |
| --- | --- |
| `0` | Sucesso. |
| `1` | Erro de execução: arquivo inexistente ou ilegível, colunas obrigatórias ausentes ou nenhuma venda válida. |
| `2` | Erro de uso: argumentos inválidos. |

## Logs

Os logs vão para a saída de erro. O nível padrão é INFO, `-v` ativa DEBUG e `-q` mostra só avisos e erros. As cores aparecem apenas em terminais e podem ser desligadas com a variável de ambiente `NO_COLOR`.

## Desenvolvimento

```bash
python -m pip install -e ".[dev]"

ruff check .
ruff format --check .
basedpyright
pytest --cov
```

Os testes exigem cobertura mínima de 80%, configurada no `pyproject.toml`. A configuração do `pytest` está em `pytest.ini`.

Também é possível rodar os testes no Docker:

```bash
docker build --target test -t sales-cli:test .
docker run --rm sales-cli:test
```

O workflow de CI (`.github/workflows/ci.yml`) executa lint, formatação e verificação de tipos, e os testes com cobertura nas versões 3.10 a 3.14 do Python, em todo pull request e em todo push na `main`.

## Estrutura do projeto

```
src/sales_cli/
    __main__.py   argumentos, fluxo principal e códigos de saída
    parser.py     leitura e validação do CSV
    core.py       modelo de venda, totais por produto e filtro de datas
    output.py     saída em texto e JSON
    utils.py      logging, normalização de texto, números e datas
tests/            testes unitários e de ponta a ponta
examples/         CSVs de exemplo
docs/             decisões de projeto
Dockerfile        imagem de execução e de testes
pyproject.toml    metadados, dependências e configuração das ferramentas
pytest.ini        configuração do pytest
```

## Decisões de projeto

As decisões de arquitetura e seus motivos estão registradas em [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md).

## Autor

Augusto Moreira Magalhães