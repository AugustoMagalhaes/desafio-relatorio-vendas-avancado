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

### D-06 — Versão única
- **Decisão:** `__version__` em `__init__.py`; o `pyproject.toml` lê de lá (`dynamic`).
- **Motivo:** uma única fonte da verdade, sem versões divergentes.

### D-07 — Python mínimo
- **Decisão:** `requires-python >= 3.10`.
- **Motivo:** o 3.9 já saiu de suporte e o 3.10+ traz sintaxe de tipos mais moderna e
  mensagens de erro melhores. Ficou como mínimo razoável, sem depender de recurso exclusivo
  de versão nova.

### D-08 — Nomes: comando em português, resto em inglês
- **Decisão:** executável `vendas-cli` (exigido pelo enunciado); pacote `sales_cli`,
  projeto e repositório `sales-cli`.
- **Motivo:** o desafio fixa o nome do comando; o nome do pacote é livre e segue a regra de
  inglês (D-01). O mapeamento está em `[project.scripts]` no `pyproject.toml`.
- **Cabeçalhos do CSV:** continuam em português no arquivo de exemplo (é o dado de entrada do
  desafio); o parser também aceita equivalentes em inglês.

## 3. Registro por etapa

| Etapa | Branch | Resumo |
|---|---|---|
| 0 | chore/project-scaffold | Estrutura, pyproject, pytest.ini, docs/DESIGN_DECISIONS.md |