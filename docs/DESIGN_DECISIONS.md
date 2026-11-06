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

## D-16 Modelo de venda

Cada linha válida do CSV é representada por um `Sale` (`core.py`), com `sale_date`, `product`, `quantity` e `unit_price`.

**Por que `dataclass`.** Gera `__init__`, `__repr__` e `__eq__` a partir dos campos tipados, sem código repetitivo, e faz parte da biblioteca padrão, o que respeita a decisão de zero dependências (D-04). Alternativas descartadas: dicionário (sem tipagem por campo e sujeito a erro de chave), classe comum (exigiria escrever os métodos à mão) e `NamedTuple` (também é imutável, mas se comporta como tupla: pode ser iterado, indexado e comparado com tuplas, o que não faz sentido para uma venda).

**Por que `frozen=True`.** A venda é criada uma vez pelo parser e depois apenas lida pelo core e pela saída. Tornar o objeto imutável impede que alguma etapa altere o dado por engano e facilita o raciocínio sobre o fluxo. Como efeito colateral, o objeto passa a ser hashável.

**Por que `slots=True`.** Evita o dicionário interno por instância, o que reduz o uso de memória quando o CSV tem muitas linhas, e impede a criação acidental de atributos novos (por exemplo, por erro de digitação em uma atribuição). O parâmetro está disponível desde o Python 3.10, versão mínima do projeto (D-07).

**Campos.** `sale_date` aceita `None` para suportar CSVs sem coluna de data e linhas sem data (D-11). `quantity` é `int` e `unit_price` é `Decimal` (D-10). O total da venda é uma propriedade calculada, sem arredondamento; a quantização para duas casas decimais acontece apenas na saída.

**Localização.** O modelo fica no módulo `core`, que é quem consome as vendas para calcular totais e o produto mais vendido. O `parser` apenas importa o tipo, o que evita dependência circular entre os módulos.

## D-17 Leitura do arquivo CSV

O arquivo é lido como bytes e decodificado pela primeira codificação que funcionar, na ordem `utf-8-sig`, `cp1252` e `latin-1`. O `utf-8-sig` aceita UTF-8 com ou sem BOM. O `cp1252` cobre arquivos exportados por programas no Windows. O `latin-1` fica por último porque mapeia todos os valores de byte e, portanto, nunca falha, o que garante que a leitura sempre produza um texto. Os dois arquivos de exemplo do repositório usam codificações diferentes (Latin-1 e UTF-8) e são cobertos por essa ordem.

O delimitador é detectado na primeira linha não vazia, escolhendo entre `;`, `,` e tabulação aquele que aparece mais vezes. Sem nenhum candidato, o padrão é a vírgula. A abordagem é simples e previsível, e suficiente porque o cabeçalho não contém números com vírgula decimal.

O arquivo inteiro é lido em memória. Para o volume esperado de um relatório de vendas isso é adequado e mantém o código simples. A codificação usada é registrada em nível DEBUG.

Arquivo inexistente levanta `FileNotFoundError`, tratado na camada de entrada (CLI).

## D-18 Colunas e validação de linhas

As colunas são identificadas pelo nome do cabeçalho, normalizado com `normalize_text` (D-12), e comparado com uma lista de aliases em português e inglês (por exemplo, `produto` e `product`, `quantidade`, `qtd` e `quantity`, `preco_unitario` e `price`). Assim a ordem das colunas e diferenças de maiúsculas, acentos e espaços não importam. Colunas extras são ignoradas.

Produto, quantidade e preço unitário são obrigatórios; a ausência de qualquer um levanta `ParseError` com a lista do que falta. A data é opcional (D-11).

A leitura usa `csv.reader` e as colunas são mapeadas para índices. O `csv.DictReader` foi evitado porque seus valores são tipados como `str | Any`, o que enfraquece a tipagem estática.

Regras de validação por linha: o produto não pode ser vazio; a quantidade deve ser um número inteiro não negativo (`3` e `3.0` são aceitos, `1.5` e `-1` não); o preço unitário deve ser um `Decimal` não negativo. Uma linha inválida levanta `ValueError`, e o tratamento (ignorar a linha e registrar o motivo) fica a cargo de quem lê o arquivo completo.

Uma data vazia ou em formato não reconhecido resulta em `sale_date=None`, sem invalidar a linha. O texto não reconhecido é registrado em nível DEBUG.

Limitação conhecida: um valor como `1.000` ou `1,000`, com um único separador e três casas, é interpretado como decimal (1,000), não como milhar. Valores com os dois separadores (`1.234,50`) são interpretados corretamente (D-10).

## D-19 Leitura completa e tratamento de linhas inválidas

`parse_sales` lê o arquivo, detecta o delimitador, mapeia as colunas e converte cada linha em `Sale`, devolvendo a lista de vendas.

O arquivo é lido com `io.StringIO(text, newline="")`, conforme recomendado pela documentação do módulo `csv`, para que campos entre aspas contendo o delimitador ou quebras de linha sejam interpretados corretamente. Linhas em branco, ou com todas as células vazias, são ignoradas sem aviso.

Uma linha inválida não interrompe a leitura: ela é ignorada e contada. Ao final, é emitido um único WARNING com o total de linhas ignoradas, para não poluir a saída em arquivos grandes. O motivo de cada linha, com o seu número, é registrado em nível DEBUG e fica visível com `-v`. O número da linha refere-se à posição no arquivo, contando o cabeçalho e as linhas em branco, e não considera quebras de linha dentro de campos entre aspas.

São erros fatais (`ParseError`): arquivo sem dados, cabeçalho sem as colunas obrigatórias e arquivo sem nenhuma venda válida. Nesses casos não há relatório útil a produzir, e a camada de entrada converte o erro em mensagem clara e código de saída 1. Um resumo com a quantidade de vendas lidas é registrado em nível INFO.

## D-20 Agregação por produto

`summarize` (`core.py`) recebe as vendas e devolve um `Report` com os totais por produto (`ProductTotal`), o total geral e os produtos mais vendidos por quantidade e por receita. As estruturas são dataclasses imutáveis, pelos mesmos motivos da D-16.

Produtos são agrupados sem diferenciar maiúsculas de minúsculas (`casefold`), de modo que `Mouse` e `mouse` contam como o mesmo item; o nome exibido é o da primeira ocorrência. Acentos e pontuação não são normalizados nesse ponto, para manter a regra simples e previsível.

O enunciado não define "produto mais vendido". Foi adotado o produto com maior quantidade de unidades, com desempate pela maior receita e, persistindo o empate, pelo nome em ordem alfabética, de forma que o resultado seja sempre determinístico. A receita também é calculada, e o produto de maior receita é informado separadamente, pois os dois critérios podem apontar produtos diferentes.

Os produtos são ordenados por receita decrescente e, em empate, por nome. Os valores não são arredondados no `core`; o arredondamento para duas casas ocorre apenas na saída (D-10).

Quando não há vendas, o `Report` tem lista vazia, total zero e os dois campos de melhor vendedor como `None`.

## D-21 Filtro por período

`filter_by_date` (`core.py`) recebe as vendas e os limites opcionais de início e fim. Os limites são inclusivos e podem ser usados isoladamente. Sem nenhum limite, as vendas são devolvidas sem alteração e sem registro em log. A ordem original é preservada.

Como os CSVs podem não ter datas, ou ter datas em formato não reconhecido (D-11), o comportamento nesses casos é explícito:

- Se nenhuma venda tem data reconhecida, o filtro é ignorado, todas as vendas são mantidas e é emitido um WARNING. Aplicar o filtro nesse caso produziria um relatório vazio por um motivo que o usuário provavelmente não pretendia.
- Se apenas algumas vendas não têm data, elas são excluídas do período, pois não é possível saber se pertenceriam a ele, e um único WARNING informa quantas foram excluídas.
- Se nenhuma venda cai no período, o resultado é vazio e um WARNING é emitido.

Os avisos usam o nível WARNING, exibido em amarelo no terminal (D-09). A validação de que o início não é posterior ao fim é feita na camada de entrada (CLI), junto com a leitura dos argumentos.

## D-22 Saída em texto

`format_text` (`output.py`) gera a tabela de produtos, o total geral e os produtos mais vendidos por quantidade e por receita. A função apenas devolve uma `str`; quem imprime é a camada de entrada, o que mantém o módulo de saída testável sem capturar stdout.

O arredondamento para duas casas decimais acontece somente no módulo de saída (D-10), com `quantize` e `ROUND_HALF_UP`, o arredondamento comercial usual. O modo é explícito porque a formatação de `Decimal` do Python usa por padrão o arredondamento "half even", que arredonda 0,125 para 0,12. Os valores no `core` permanecem exatos.

A tabela é ASCII, com a largura de cada coluna calculada pelo conteúdo, produto alinhado à esquerda e números à direita. Os valores são impressos sem símbolo de moeda nem separador de milhar, para que a saída não dependa de localidade e possa ser lida por outras ferramentas. Os rótulos estão em inglês, seguindo a D-01.

Sem vendas, a saída é a mensagem `No sales to report.`

## D-23 Saída em JSON

`format_json` (`output.py`) devolve o relatório como uma `str` JSON indentada com dois espaços, com as chaves `products`, `grand_total`, `best_seller_by_units` e `best_seller_by_revenue`. Cada produto tem `product`, `quantity` e `revenue`. Como na saída em texto, a função só devolve a string; a impressão é responsabilidade da camada de entrada.

Os valores monetários são números JSON, e não strings, para que quem consome possa somá-los e ordená-los sem conversão. Como o módulo `json` não serializa `Decimal`, o valor é arredondado a duas casas com a mesma função usada no texto (D-22) e só então convertido para `float`. Como o valor já está arredondado, a conversão não introduz diferença visível nos valores esperados de um relatório de vendas.

Sem vendas, `products` é uma lista vazia, `grand_total` é `0.0` e os campos de melhor vendedor são `null`.

Caracteres não ASCII são escapados (`\u00e2`), que é o comportamento padrão do `json`. Como o JSON se destina a ser lido por programas, o escape evita problemas de codificação em terminais e pipes.

O relatório vai para a saída padrão e os logs vão para a saída de erro (D-09), de modo que a saída JSON possa ser redirecionada ou encadeada com outras ferramentas sem ser contaminada por mensagens.

## D-24 Argumentos da linha de comando

O `__main__.py` é o ponto de entrada do comando `vendas-cli` e concentra o `argparse`, a única camada que lida com argumentos e códigos de saída. Os módulos `parser`, `core` e `output` não conhecem a CLI.

Os argumentos são: o caminho do CSV (obrigatório), `-f/--format` (`text` ou `json`, padrão `text`), `--start` e `--end` (opcionais, inclusivos), `-v/--verbose`, `-q/--quiet` e `--version`.

As datas de `--start` e `--end` passam pela mesma função `parse_date` usada na leitura do CSV (D-11), de modo que aceitam os mesmos formatos (por exemplo, `2025-01-31` e `31/01/2025`). Uma data inválida é rejeitada pelo próprio `argparse`.

Os atributos de um `argparse.Namespace` comum são do tipo `Any`, o que anula a verificação estática. Por isso a classe `Arguments` herda de `Namespace` e declara cada atributo com tipo e valor inicial no `__init__`; o `argparse` sobrescreve esses valores com os da linha de comando. O resto do código usa os argumentos com tipos conhecidos.

Erros de uso terminam com o código de saída 2, padrão do `argparse`: formato desconhecido, data inválida, `--start` posterior a `--end` e uso simultâneo de `--verbose` e `--quiet`. A segunda e a terceira regras são validadas após a leitura, com `parser.error`, para produzirem a mesma mensagem de uso e o mesmo código de saída dos demais erros.

## D-25 Fluxo principal, saída padrão e códigos de saída

`main` (`__main__.py`) orquestra as camadas: lê os argumentos, configura o logging, lê o CSV, aplica o filtro de datas, calcula o relatório e o imprime em texto ou JSON. A função recebe a lista de argumentos como parâmetro e devolve o código de saída, o que a torna testável sem processos externos; o bloco `if __name__ == "__main__"` apenas encaminha o retorno para `SystemExit`. Esse mesmo `main` é o ponto de entrada do comando instalado (D-02).

O relatório é escrito na saída padrão e todos os logs na saída de erro (D-09), de modo que a saída possa ser redirecionada, por exemplo `vendas-cli vendas.csv -f json > saida.json`, sem mensagens misturadas.

Níveis de log: INFO por padrão, DEBUG com `-v` e WARNING com `-q`. O modo silencioso ainda exibe avisos e erros, que indicam problemas reais nos dados ou na execução.

Códigos de saída: 0 em caso de sucesso, 1 para erros de execução e 2 para erros de uso, padrão do `argparse` (D-24). São tratados como erro de execução: arquivo inexistente, arquivo ilegível (por exemplo, um diretório ou falta de permissão), cabeçalho sem colunas obrigatórias e arquivo sem nenhuma venda válida. Em todos os casos o programa registra uma mensagem de erro curta, sem traceback. Um período sem vendas não é erro: o relatório vazio é impresso, com aviso, e o código de saída é 0.

O logger do CLI se chama `sales_cli.cli`, e não `__name__`, porque ao executar `python -m sales_cli` o nome do módulo é `__main__`, que não pertence ao pacote `sales_cli` e portanto não herdaria o handler configurado em `setup_logging`.

Os testes cobrem o fluxo chamando `main` diretamente e, para validar o comando de ponta a ponta (separação entre saída padrão e de erro e códigos de saída reais), executando `python -m sales_cli` em um subprocesso.

## D-26 Docker

O uso com Docker é opcional; o projeto funciona sem ele, com ambiente virtual nativo (D-02).

O `Dockerfile` tem três estágios. O `base` define a imagem `python:3.12-slim`, escolhida por estar no meio da faixa de versões suportadas (3.10 a 3.14, D-07), e as variáveis de ambiente comuns. O `test` instala o pacote com as dependências de desenvolvimento e executa o `pytest` com cobertura. O `runtime` instala somente o pacote, sem dependências de desenvolvimento, e é o último estágio, de modo que `docker build .` produz a imagem final e o estágio de teste só é construído quando solicitado com `--target test`.

A imagem final executa como usuário sem privilégios (`app`) e define `vendas-cli` como `ENTRYPOINT`, de modo que ela se comporta como o próprio comando. O diretório de trabalho é `/data`, destinado a receber o CSV por montagem de volume, por exemplo `docker run --rm -v "$PWD:/data:ro" sales-cli vendas.csv`. Sem argumentos, a imagem exibe a ajuda.

O estágio de teste executa apenas o `pytest`. As verificações de estilo e de tipos ficam no CI (D-14), porque a configuração do basedpyright referencia o ambiente virtual local (`.venv`), que não existe no contêiner. O estágio executa os testes ao rodar o contêiner (`CMD`), e não durante o build.

Não há camada separada para o cache de dependências, pois o projeto não tem dependências de execução (D-04). O `.dockerignore` mantém fora do contexto de build o histórico do Git, ambientes virtuais, caches, documentação e exemplos, o que reduz o contexto enviado ao Docker e evita copiar arquivos locais para a imagem.

## D-27 README

O README está em dois arquivos: `README.md`, em inglês, e `README.pt-BR.md`, em português, com um link para o outro no topo de cada um. O inglês é o principal porque o código, os logs, as mensagens da CLI e a ajuda estão em inglês (D-01) e o README é a primeira página que o leitor vê; o `pyproject.toml` também o usa como descrição do pacote. A versão em português atende ao enunciado do desafio e deve ser mantida em sincronia com a principal sempre que o comportamento documentado mudar. Este documento permanece em português.

Os dois arquivos documentam os dois caminhos de instalação e uso: ambiente virtual e Docker (D-26). Descrevem também o formato de CSV aceito (codificações, delimitadores, nomes de colunas, formatos de data e de número), o comportamento do filtro de datas, os códigos de saída e o fluxo de desenvolvimento, para que o comportamento descrito em decisões anteriores possa ser consultado sem ler o código.

Os exemplos de saída foram copiados de execuções reais dos CSVs do diretório `examples`, e não escritos à mão, para que o README reflita o comportamento do programa. O badge de status do CI aponta para o workflow da `main` (D-14).

O topo de cada README exibe badges de status (CI, cobertura, versão mínima do Python e ferramentas de qualidade); o de versão do Python é estático e deve ser atualizado junto com o `requires-python` do `pyproject.toml` (D-07).

## D-28 Relatório de cobertura

O CI envia o relatório de cobertura ao Codecov, que alimenta o badge de cobertura do README. O upload usa o token guardado como segredo do repositório (`CODECOV_TOKEN`) e é feito por uma única versão do Python (3.12), para que a matriz de versões (D-14) não produza relatórios duplicados do mesmo código.

O envio é configurado com `fail_ci_if_error: false`: uma indisponibilidade do serviço externo não reprova o CI. O critério mínimo de cobertura continua sendo aplicado pelo próprio `pytest` (`fail_under` de 80% no `pyproject.toml`, D-05), de modo que o Codecov serve para visibilidade e não como barreira de merge.

## D-29 Limite de valores

Quantidade e preço unitário têm um limite máximo de 1.000.000.000 (`MAX_AMOUNT`, em `parser.py`). Uma linha com valor acima do limite é tratada como inválida, no mesmo mecanismo da D-19: é ignorada, entra no aviso único com a contagem e o motivo aparece com `-v`.

A regra existe porque `Decimal` aceita expoentes arbitrariamente grandes (por exemplo `1e30`), mas o arredondamento para duas casas (D-22) usa a precisão padrão de 28 dígitos e levanta `decimal.InvalidOperation` quando o resultado não cabe. Sem o limite, uma única linha com um valor desse tipo derrubava o programa com traceback, apenas na hora de imprimir. Com o limite de 10^9 por campo, o total de uma linha é no máximo 10^18, o que mantém a soma de dezenas de milhões de linhas dentro da precisão.

A validação de sinal e de limite ficam na mesma função (`check_amount`), usada tanto para a quantidade quanto para o preço.

## D-30 CSV malformado

O módulo `csv` levanta `csv.Error` quando o arquivo não pode ser interpretado, por exemplo quando uma célula excede o limite de 131072 caracteres. `parse_sales` converte esse erro em `ParseError` com o nome do arquivo e o motivo, de modo que ele segue o mesmo caminho dos demais erros fatais de arquivo (D-19 e D-25): mensagem curta, sem traceback, e código de saída 1.

## 3. Registro por etapa

| Etapa | Branch | Resumo |
|---|---|---|
| 0 | chore/project-scaffold | Estrutura, pyproject, pytest.ini, docs/DESIGN_DECISIONS.md |
| 1 | feat/utils-helpers | utils.py (tty, cores, logging, normalização, parse de número e data), testes e tipagem completa |
| 2 | ci/github-actions | Workflow de CI (lint, formatação, tipos e testes em Python 3.10 a 3.14), ruleset da `main` com checks obrigatórios, D-14 e D-15 |
| 3 | feat/csv-parser | Modelo `Sale`, leitura com fallback de codificação, detecção de delimitador, aliases de colunas PT/EN, validação de linhas e `parse_sales` |
| 4 | feat/core-and-date-filter | Totais por produto, total geral, mais vendido por unidades e por receita, filtro por período com avisos |
| 5 | feat/output-formatters | Saída em texto (tabela ASCII) e em JSON, arredondamento comercial apenas na saída |
| 6 | feat/cli-entrypoint | Argumentos do `argparse`, função `main`, relatório na saída padrão e logs na de erro, códigos de saída 0, 1 e 2 |
| 7 | build/docker-support | `Dockerfile` multi-estágio (`base`, `test`, `runtime`), usuário sem root e `.dockerignore` |
| 7.1 | fix/json-non-ascii | JSON com caracteres não ASCII legíveis, em vez de escapados |
| 8 | docs/readme | README em inglês e português, badges de status, relatório de cobertura no Codecov |