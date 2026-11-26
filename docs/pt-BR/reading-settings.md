# Configurações de Leitura

*[English](../en/reading-settings.md) · Português (Brasil)*

A forma como os nomes de arquivo e as pastas de um conjunto são lidos
([Como um Segmento É Lido](segments.md)) é uma característica do conjunto; por
isso, é definida por pasta, no botão **⚙** ao lado da caixa de pasta, e não na
linha de comando. As configurações são salvas em **`settings.json`**, na
[pasta `reviau/`](reviau-folder.md), de modo que a pasta é reaberta com as suas
próprias configurações em qualquer máquina e em qualquer navegador. Assim como a
lista de rótulos, o arquivo é gravado apenas quando as configurações são
aplicadas, e nunca quando a pasta é simplesmente aberta.

| Configuração | Função |
| --- | --- |
| **Padrão de nome** | Como os nomes de arquivo são lidos: o padrão *padrão*, a predefinição *busca vetorial*, ou um modelo ou expressão regular personalizados, descritos abaixo |
| **Formato de data e hora** | O formato `strptime` da data e da hora capturadas (por padrão, `%Y%m%d%H%M%S`) |
| **Origem do rótulo** | *Automática* (o nome do arquivo quando o padrão captura um rótulo; caso contrário, a pasta), *Pasta*, *Nome do arquivo* ou *Nenhuma* |
| **Nível do rótulo** | O nível da pasta que carrega o rótulo, contado a partir da pasta de segmentos: 0 é a pasta que contém o clipe, e 1 é a primeira pasta abaixo da pasta de segmentos |

Durante a edição das configurações, uma **pré-visualização** indica quantos dos
nomes pendentes o padrão reconhece e o que ele lê dos primeiros: rótulo, ponto,
data, janela e pontuação. Configurações que não podem ser utilizadas, como um modelo
com um campo desconhecido, são informadas com o motivo, e **Aplicar** permanece
indisponível até que sejam corrigidas. A aplicação das configurações as salva e
reabre a pasta com elas.

Nomes que não correspondem ao padrão podem ainda assim ser revisados; a interface
exibe menos informações sobre eles, e nenhuma que não possa ler com segurança.
Quando uma pasta é aberta, um aviso abaixo da caixa de pasta informa os nomes que
o padrão não reconhece.

## Elaboração de um Modelo

A forma mais simples de padrão personalizado consiste em **escrever o nome, com
as partes identificadas entre colchetes**. Todo o texto fora dos colchetes é
comparado literalmente. Para nomes como
`PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873.wav`:

```
[site]_YYYYMMDDTHHMMSS_REC_[start_time]_[end_time]_[label]_[score]
```

| No modelo | Corresponde a |
| --- | --- |
| `[site]`, `[label]` | texto livre, que pode conter sublinhados |
| `YYYYMMDD`, `HHMMSS` | a data e a hora, escritas como indicado ou como `[date]` e `[time]` |
| `[datetime]` | a data e a hora em conjunto, em qualquer formato, descrito pelo formato de data e hora |
| `[start_time]`, `[end_time]` | a janela do clipe na gravação, em segundos |
| `[score]` | um valor de similaridade ou de confiança |
| `[extra]` | qualquer texto restante, exibido na interface como *Outros* |
| `*` | qualquer texto, que não é capturado |
| qualquer outro texto | ele próprio, literalmente |

Todos os campos são opcionais, mas o modelo deve corresponder ao nome **inteiro**.
Uma correspondência parcial preencheria a interface com informações lidas das
partes erradas do nome e, por isso, é tratada como ausência de correspondência.
Um campo desconhecido, como o erro de digitação `[speceis]`, é recusado, em vez
de ser ignorado.

## Elaboração de uma Expressão Regular

Para nomes que nenhum modelo consegue descrever, o padrão personalizado também
aceita **qualquer expressão regular com grupos nomeados**: `site`, `date`, `time`,
`datetime`, `start`, `end`, `label`, `score` e `extra`. Todos são opcionais, e a
expressão é aplicada ao nome do arquivo sem a extensão. Para nomes como
`BOAALB-pontoA-202401150530.wav`, com o rótulo primeiro e um carimbo de data e
hora de 12 dígitos:

```
^(?P<label>[A-Z]+)-(?P<site>\w+)-(?P<datetime>\d{12})$
```

com o formato de data e hora `%Y%m%d%H%M`.

## Origem do Rótulo

Com a origem *Automática*, um padrão que captura um grupo `label` lê o rótulo do
nome do arquivo, e qualquer outro padrão o lê da pasta. Quando o rótulo é lido do
nome do arquivo, o clipe é arquivado diretamente sob o resultado e o rótulo
previsto, por exemplo `incorrect/BOAALB/clipe_TURDRU.wav`.

Para manter as pastas, a origem *Pasta* deve ser selecionada explicitamente. Para
segmentos organizados como `[rótulo]/[ponto]_AAAAMMDD/clipe.wav`, a origem *Pasta*
com nível do rótulo 1 lê o rótulo da pasta superior e mantém a pasta do ponto
abaixo dela, enquanto o ponto, os horários e a pontuação continuam a ser lidos do
nome do arquivo.

## A Predefinição de Busca Vetorial

A predefinição *busca vetorial* lê nomes no formato
`PONTO_AAAAMMDD_HHMMSS_INÍCIO-FIMs_PONTUAÇÃO_RÓTULO.wav`, gravados pelos notebooks
de busca vetorial bioacústica, com o **rótulo e a pontuação de similaridade no
nome**.

Como o rótulo faz parte do nome, os clipes são arquivados diretamente sob o
resultado e o rótulo previsto (`correct/BOAALB/`, `incorrect/BOAALB/`), e os
rótulos acrescentados são incluídos no fim do nome, como nos demais casos: um
segmento chamado `..._0.873_BOAALB.wav` e corrigido para TURDRU passa a
`incorrect/BOAALB/..._0.873_BOAALB_TURDRU.wav`. Um segmento confirmado como
BOAALB mantém o nome, `correct/BOAALB/..._0.873_BOAALB.wav`, pois a previsão já
está no seu fim. A pontuação é exibida ao lado do rótulo na interface e também
consta do registro.
