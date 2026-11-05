# Design Decisions — Sales Report CLI

> Registro das decisões de projeto, em português. Código, logs e README estão em inglês (ver D-01).
> Cada etapa (branch) adiciona uma linha em "Registro por etapa" e, quando há decisão nova,
> uma entrada em "Decisões".

## 1. Visão geral

CLI `vendas-cli` que lê um CSV de vendas e gera relatório por produto
(total vendido, valor total, produto mais vendido), em texto ou JSON,
com filtro opcional por intervalo de datas.

Premissas adicionais adotadas, além do enunciado:
- somente biblioteca padrão em runtime (zero dependências);
- logging claro, em inglês, sem poluir a saída;
- datas dinâmicas: aceita vários formatos e também CSV sem coluna de data.

## 2. Decisões

### D-01 — Idioma
- **Decisão:** código, logs, mensagens de erro e README em inglês; este documento em português.
- **Motivo:** inglês é o padrão para código e logs (busca em ferramentas de log, times
  mistos). O registro de decisões é em português para facilitar a leitura e a discussão,
  já que o enunciado do desafio está em português.
- **Exceções:** o nome do executável (D-08) e os cabeçalhos do CSV de exemplo.

### D-02 — Layout `src/`
- **Decisão:** `src/sales_cli/` em vez de pacote na raiz do repositório.
- **Motivo:** convenção recomendada pela PyPA; separa o código instalável do restante
  (testes, exemplos, configurações) e impede que `import sales_cli` funcione por acidente
  a partir da raiz sem instalar o pacote ou configurar o path.
- **Trade-off:** o `pythonpath = src` do `pytest.ini` (D-05) é um atalho de conveniência,
  então os testes importam direto de `src/`. A validação do empacotamento fica a cargo do
  `pip install`, que falha se o `pyproject.toml` ou o pacote estiverem errados.
- **Alternativa:** layout plano (mais simples, mas esconde erros de empacotamento).

### D-03 — Módulos
- **Decisão:** os 3 módulos do desafio (`parser`, `core`, `output`) + 1 extra (`utils`).
  O ponto de entrada fica em `__main__.py`.
- **Motivo:** `__main__.py` é a convenção do Python para pacote executável
  (`python -m sales_cli`) e o script `vendas-cli` aponta para ele. Contém o `argparse` e
  só orquestra os outros módulos; não tem regra de negócio.
- **Responsabilidades:**
  - `parser`: lê e valida o CSV;
  - `core`: cálculos e filtros;
  - `output`: formatação (texto e JSON);
  - `utils`: helpers genéricos (tty, cores, logging, parse de número e data).

### D-04 — Zero dependências em runtime
- **Decisão:** `dependencies = []`; somente `csv`, `argparse`, `logging`, `decimal` e `json`.
- **Motivo:** o enunciado pede biblioteca padrão para leitura de CSV, CLI e logging. Estendi
  a regra a todo o runtime para manter a instalação leve e reduzir a superfície de
  manutenção e segurança.
- **Exceção consciente:** `pytest` e `pytest-cov` somente em `[dev]`. O enunciado exige 80%
  de cobertura e, para medir, é necessário o coverage.

### D-05 — Configuração de testes
- **Decisão:** `pytest.ini` dedicado com `pythonpath = src`; cobertura configurada no
  `pyproject.toml` (`fail_under = 80`).
- **Motivo:** o enunciado pede um arquivo de configuração de testes (`pytest.ini` ou
  similar). O `pythonpath = src` faz o `pytest` funcionar logo após o clone. O limite de 80%
  só vale com `pytest --cov`, então `pytest` puro não quebra sem o plugin instalado.
- **Pasta `tests/`:** na etapa 0 ela foi versionada com um `.gitkeep` (o Git não rastreia pastas
  vazias). O arquivo foi removido na etapa 1, quando a pasta ganhou testes reais.

### D-06 — Versão única
- **Decisão:** `__version__` em `__init__.py`; o `pyproject.toml` lê de lá (`dynamic`).
- **Motivo:** uma única fonte da verdade, sem versões divergentes.

### D-07 — Python mínimo
- **Decisão:** `requires-python >= 3.10`.
- **Motivo:** o 3.9 já saiu de suporte e o código usa a sintaxe `X | None` (3.10+) nas
  anotações de tipo.

### D-08 — Nomes: comando em português, resto em inglês
- **Decisão:** executável `vendas-cli` (exigido pelo enunciado); pacote `sales_cli`,
  projeto e repositório `sales-cli`.
- **Motivo:** o desafio fixa o nome do comando; o nome do pacote é livre e segue a regra de
  inglês (D-01). O mapeamento está em `[project.scripts]` no `pyproject.toml`.
- **Cabeçalhos do CSV:** continuam em português no arquivo de exemplo (é o dado de entrada do
  desafio); o parser também aceita equivalentes em inglês.

### D-09 — Logging
- **Decisão:** logger do pacote (`sales_cli`) configurado por `utils.setup_logging`, com saída
  em **stderr** e nível padrão INFO. Mensagens em inglês.
- **Motivo:** stdout fica reservado ao relatório, então `vendas-cli ... --format json | jq`
  funciona sem logs misturados. INFO mostra o essencial (arquivo lido, linhas, filtros);
  detalhes linha a linha ficam em DEBUG para não poluir.
- **Formato:** uma linha só, `HH:MM:SS | NÍVEL | mensagem`.
- **Cores:** só quando a saída é um terminal e a variável `NO_COLOR` não está definida
  (https://no-color.org). DEBUG é apagado, WARNING amarelo, ERROR e CRITICAL vermelhos; INFO
  fica sem cor. Feito com constantes ANSI em `utils.py`, sem `colorama` ou `rich`.
- **Trade-off:** consoles muito antigos do Windows podem não interpretar ANSI. Aceito para
  manter zero dependências.
- **Detalhe técnico:** `setup_logging` pode ser chamada mais de uma vez (limpa os handlers do
  logger do pacote antes de adicionar o seu) e desliga `propagate`, para o log não sair
  duplicado se alguém configurar o root logger.

### D-10 — Parse numérico com `Decimal`
- **Decisão:** `utils.parse_decimal` aceita formato brasileiro e inglês e devolve `Decimal`.
- **Regras:**
  - com `,` e `.` juntos, o **último** é o separador decimal (`1.234,56` e `1,234.56`);
  - só `,` ou só `.` é separador decimal (`49,9` e `49.9`);
  - o prefixo `R$` é ignorado;
  - `NaN` e `Infinity` são rejeitados; qualquer valor inválido gera `ValueError`.
- **Motivo:** CSVs brasileiros usam vírgula decimal com frequência. `Decimal` evita o erro de
  ponto flutuante em dinheiro (com `float`, `49.9 * 3` dá `149.70000000000002`).
- **Limitações conhecidas:** `1,234` é lido como 1,234 (decimal), não 1234, e separador de
  milhar repetido (`1.234.567`) é rejeitado. As regras são simples e determinísticas.

### D-11 — Datas
- **Decisão:** `utils.parse_date` tenta, em ordem, uma lista de formatos com
  `datetime.strptime` e devolve `date` (ou `None` se nenhum servir).
- **Formatos:**
  - ano primeiro: `2025-01-31`, `2025/01/31`, `2025.01.31`;
  - dia/mês/ano: `31/01/2025`, `31-01-2025`, `31.01.2025` e `05/01/25` (ano de 2 dígitos);
  - mês/dia/ano (`01/31/2025`, `01-31-2025`), usado só quando dia/mês é impossível.
- **Ambiguidade:** `03/04/2025` é lido como 3 de abril. A ordem dia/mês vem antes da mês/dia
  (convenção brasileira).
- **Hora:** o texto é cortado no primeiro espaço (e o `T` do ISO vira espaço), então
  `2025-01-31 10:30` e `2025-01-31T10:30:00Z` viram `2025-01-31`. O filtro é por dia.
- **Fora do escopo:** meses por extenso, timestamp Unix e número serial do Excel. Valores assim
  são tratados como "sem data" (e geram aviso mais adiante), sem derrubar o programa.
- **Alternativas descartadas:** regex e bibliotecas de terceiros (`dateutil`): mais código para
  manter e explicar, ou dependência extra.
- **Aviso DTZ007 do ruff:** a regra reclama de `strptime` sem fuso. É ignorada no projeto
  porque guardamos só a data de calendário (`.date()`), que não tem fuso.

### D-12 — Normalização de textos (cabeçalhos do CSV)
- **Decisão:** `utils.normalize_text` transforma um texto em uma chave simples:
  `"Preço Unitário (R$)"` vira `"preco_unitario_r"`.
- **Como funciona:** `strip_accents` decompõe cada letra acentuada em letra base + marca de
  acento (`unicodedata.normalize("NFKD", ...)`) e descarta as marcas; depois vêm `lower()` e
  uma regex que troca qualquer sequência fora de `[a-z0-9]` por um único `_`.
- **Motivo:** o cabeçalho pode vir como `Preço`, `preco` ou `PREÇO`. Com a chave padronizada, o
  parser compara com os nomes esperados sem depender de acento ou maiúsculas.

### D-13 — Tipagem completa, ferramentas e código sem comentários
- **Decisão:** todo o código, inclusive os testes, é tipado: argumentos, retornos, fixtures,
  constantes, atributos e variáveis locais. Constantes usam `Final`. Só ficam sem anotação o que
  a sintaxe do Python não permite anotar (variáveis de `for` e de comprehension, `as` e `_`) e
  as reatribuições. O código não tem comentários nem docstrings.
- **Motivo:** o enunciado pede tipagem estática. Nomes e tipos expressam a intenção; as regras de
  comportamento não óbvias (logging, números, datas, normalização) estão documentadas neste
  arquivo, nas decisões D-09 a D-12.
- **Verificador de tipos:** basedpyright, apontando para o ambiente `.venv`, com a regra
  `reportImplicitOverride` desligada. O `typing.override` só existe no Python 3.12+; usá-lo
  exigiria `typing_extensions` (dependência extra, contra o D-04) ou subir o mínimo para 3.12
  (contra o D-07).

## D-14 Integração contínua

O projeto usa GitHub Actions (`.github/workflows/ci.yml`) para validar cada alteração antes de ela chegar à `main`. O workflow roda em todo pull request com destino à `main` e em todo push na `main`.

O push na `main` só ocorre pelo merge de um PR, já que o push direto é bloqueado. O run após o merge valida o resultado real da integração e alimenta o badge de status do README.

O workflow tem dois jobs:

- **Lint and types:** `ruff check`, `ruff format --check` e `basedpyright`.
- **Tests:** `pytest --cov` em Python 3.10, 3.11, 3.12, 3.13 e 3.14, com `fail-fast` desativado para que uma falha em uma versão não esconda o resultado das outras.

A matriz cobre da versão mínima suportada (3.10, conforme D-07) até a mais recente. O limite de cobertura de 80% fica no `pyproject.toml` (`fail_under`), então o mesmo critério vale localmente e no CI.

O job de tipos cria uma `.venv` antes de rodar o basedpyright, porque o `pyproject.toml` aponta para esse caminho (`venvPath` e `venv`). Assim a configuração é a mesma no ambiente local e no runner.

CD (publicação ou deploy) está fora do escopo do desafio.

## D-15 Fluxo de branches e proteção da main

O trabalho é feito em branches curtas, uma por etapa, com nomes no padrão `tipo/descricao` (`feat/`, `ci/`, `docs/`, `chore/`, `build/`). A integração é feita por pull request.

O ruleset `protect-main` impede push direto, force push e exclusão da `main`. Ele exige PR, permite apenas merge commit e exige que os seis checks do CI passem, com a branch atualizada em relação à `main`. Os checks obrigatórios usam os nomes dos jobs do workflow. Se um job for renomeado, a lista no ruleset deve ser atualizada.

As mensagens de commit seguem Conventional Commits, em inglês.

## 3. Registro por etapa

| Etapa | Branch | Resumo |
|---|---|---|
| 0 | chore/project-scaffold | Estrutura, pyproject, pytest.ini, docs/DESIGN_DECISIONS.md |
| 1 | feat/utils-helpers | utils.py (tty, cores, logging, normalização, parse de número e data), testes e tipagem completa |