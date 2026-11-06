**English** | [Português](README.pt-BR.md)

# sales-cli

[![CI](https://github.com/AugustoMagalhaes/desafio-relatorio-vendas-avancado/actions/workflows/ci.yml/badge.svg)](https://github.com/AugustoMagalhaes/desafio-relatorio-vendas-avancado/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/AugustoMagalhaes/desafio-relatorio-vendas-avancado/graph/badge.svg)](https://codecov.io/gh/AugustoMagalhaes/desafio-relatorio-vendas-avancado)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![basedpyright - checked](https://img.shields.io/badge/basedpyright-checked-42b983)](https://docs.basedpyright.com)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

A command-line tool that reads a sales CSV file and produces a report with the total per product, the total value of all sales and the best-selling product, as a formatted text table or JSON, with an optional date range filter.

The package is named `sales-cli` and the installed command is `vendas-cli`.

## Features

- CSV reading with the standard library only (`csv`, `argparse`, `logging`), with no runtime dependencies.
- Total sales per product, grand total and best-selling product.
- Date range filter (`--start` and `--end`).
- Output as a text table or JSON (`--format text|json`).
- Tolerance for variations in input files: encoding, delimiter, column names, date formats and number formats.
- Clear logs on the error stream, kept separate from the report.

## Requirements

Python 3.10 or later. There are no runtime dependencies.

## Installation

### With a virtual environment

```bash
git clone https://github.com/AugustoMagalhaes/desafio-relatorio-vendas-avancado.git
cd desafio-relatorio-vendas-avancado

python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

On Windows, activate the environment with `.venv\Scripts\activate`.

For development (tests, lint and type checking), use an editable install with the development dependencies:

```bash
python -m pip install -e ".[dev]"
```

### With Docker

```bash
docker build -t sales-cli .
```

## Usage

```bash
vendas-cli sales.csv --format text
vendas-cli sales.csv --format json --start 2025-01-01 --end 2025-03-31
```

With Docker, the CSV is read from a volume mounted at `/data`:

```bash
docker run --rm -v "$PWD:/data:ro" sales-cli sales.csv --format json
```

With no arguments, the image prints the help. To get colored logs inside the container, add `-t` to `docker run`.

The package can also be run as a module, without the installed command:

```bash
python -m sales_cli sales.csv
```

### Options

| Option | Description |
| --- | --- |
| `path` | Path to the CSV file (required). |
| `-f`, `--format {text,json}` | Output format. Default: `text`. |
| `--start DATE` | Only include sales on or after this date (inclusive). |
| `--end DATE` | Only include sales on or before this date (inclusive). |
| `-v`, `--verbose` | Show debug messages. |
| `-q`, `--quiet` | Show only warnings and errors. |
| `--version` | Show the version. |
| `-h`, `--help` | Show the help. |

`--verbose` and `--quiet` cannot be used together, and `--start` cannot be later than `--end`.

## Example output

Text:

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

The report is written to standard output and the logs to standard error, so you can redirect only the report:

```bash
vendas-cli sales.csv --format json > report.json
```

## CSV format

### File

- **Encoding:** UTF-8 (with or without BOM), Windows-1252 or Latin-1, detected automatically.
- **Delimiter:** `;`, `,` or tab, detected from the header line.
- **Blank lines** are ignored.

### Columns

Column names are matched ignoring case, accents and spacing, and column order does not matter. Extra columns are ignored. Both Portuguese and English names are accepted.

| Field | Required | Accepted names |
| --- | --- | --- |
| Product | Yes | `produto`, `product`, `item`, `nome_produto` |
| Quantity | Yes | `quantidade`, `quantity`, `qtd`, `qtde`, `qty` |
| Unit price | Yes | `preco_unitario`, `unit_price`, `preco`, `price`, `valor_unitario` |
| Date | No | `data`, `date`, `data_venda`, `data_da_venda`, `sale_date` |

Example:

```
data;produto;quantidade;preço unitário
2025-03-01;Mouse;2;50,00
01/03/2025;Teclado;1;150,00
```

### Values

- **Quantity:** a non-negative whole number up to 1,000,000,000 (`3` and `3.0` are accepted).
- **Price:** a non-negative number up to 1,000,000,000, with or without the `R$` prefix. Accepts `1234.50`, `10,5` and `1.234,50`.
- **Dates:** `YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY.MM.DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, `DD/MM/YY`, `MM/DD/YYYY` and `MM-DD-YYYY`. A time part is ignored. When the format is ambiguous (for example `01/02/2025`), the day comes first.
- **Products** spelled the same way, ignoring case, are added together.

### Invalid rows

An invalid row (empty product, or invalid quantity or price) is skipped, and a single warning reports how many were skipped. Use `-v` to see the reason and the number of each one.

## Date filter

- Without `--start` and `--end`, all sales are included.
- If **no** sale has a recognized date, the filter is ignored, all sales are kept and a warning is shown.
- If **some** sales have no date, they are left out of the period and a warning reports how many.
- If no sale falls within the period, the report is empty, with a warning.

## Best-selling product

The challenge statement does not define the criterion, so the report shows both: the product with the most **units** sold (ties broken by higher revenue and then by name) and the product with the highest **revenue**.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Runtime error: missing or unreadable file, missing required columns or no valid sales. |
| `2` | Usage error: invalid arguments. |

## Logging

Logs go to standard error. The default level is INFO, `-v` enables DEBUG and `-q` shows only warnings and errors. Colors are used only on terminals and can be turned off with the `NO_COLOR` environment variable.

## Development

```bash
python -m pip install -e ".[dev]"

ruff check .
ruff format --check .
basedpyright
pytest --cov
```

Tests require at least 80% coverage, configured in `pyproject.toml`. The `pytest` configuration is in `pytest.ini`.

Tests can also be run in Docker:

```bash
docker build --target test -t sales-cli:test .
docker run --rm sales-cli:test
```

The CI workflow (`.github/workflows/ci.yml`) runs lint, formatting and type checks, and the tests with coverage on Python 3.10 to 3.14, on every pull request and every push to `main`.

## Project structure

```
src/sales_cli/
    __main__.py   arguments, main flow and exit codes
    parser.py     CSV reading and validation
    core.py       sale model, per-product totals and date filter
    output.py     text and JSON output
    utils.py      logging, text normalization, number and date parsing
tests/            unit and end-to-end tests
examples/         sample CSV files
docs/             design decisions
Dockerfile        runtime and test images
pyproject.toml    metadata, dependencies and tool configuration
pytest.ini        pytest configuration
```

## Design decisions

Architecture decisions and their rationale are recorded in [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md) (in Portuguese).

## Author

Augusto Moreira Magalhães