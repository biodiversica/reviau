# A Pasta reviau

*[English](../en/reviau-folder.md) · Português (Brasil)*

Tudo o que uma revisão grava é mantido numa única pasta, **`reviau/`**, dentro da
pasta de segmentos:

```
segmentos/
├── PONTO_A/BOAALB/clipe.wav      ← clipes pendentes de revisão
└── reviau/
    ├── correct/                  ← clipes revisados, por resultado
    ├── incorrect/
    ├── uncertain/
    ├── reviews.csv               ← o registro da revisão
    ├── labels.txt                ← a lista de rótulos
    ├── settings.json             ← as configurações de leitura
    └── annotations.csv           ← a tabela de anotações, com --annotations
```

Assim, o conjunto em revisão nunca se mistura com os resultados: a única
alteração feita nele é a retirada dos clipes revisados, e a exclusão de `reviau/`
remove tudo o que o reviau gravou. A pasta `reviau/` é excluída da lista de
pendentes, e todas as demais pastas do conjunto são revisadas, qualquer que seja
o seu nome. `--output` coloca essa pasta em outro local; consulte
[Gravação em Outro Local](#gravação-em-outro-local).

## A Lista de Rótulos

Os botões de rótulo provêm de uma lista armazenada em **`labels.txt`**, na pasta
`reviau/`, com um rótulo por linha. Na primeira vez que um conjunto é aberto,
a lista é formada pelos rótulos que o conjunto já utiliza, e o arquivo é gravado
quando o primeiro segmento é revisado. A partir de então, o arquivo constitui a
lista, que pode ser editada pela interface ou manualmente (linhas em branco e
linhas iniciadas por `#` são ignoradas).

A lista nunca é ampliada automaticamente: um novo exame da pasta que encontre uma
pasta nova não acrescenta o seu nome à lista. A remoção de rótulos da lista
também é segura, uma vez que o rótulo do próprio clipe sempre aparece como botão,
conste ou não da lista, e um nome digitado no campo é acrescentado à lista e
selecionado para o segmento em exibição.

`--labels-file` armazena a lista em outro local. Um caminho relativo é resolvido
dentro da pasta `reviau/`; um caminho absoluto, como `~/classes.txt`, fornece a
mesma lista a todas as pastas abertas.

## Onde o Clipe Revisado É Arquivado

Um clipe revisado é arquivado na pasta `reviau/`, sob o seu **resultado**,
seguido do caminho que tinha, incluindo a pasta do rótulo **previsto**. Cada
pasta responde, portanto, a uma única pergunta: `incorrect/PONTO_A/BOAALB/`
contém exatamente os clipes que o modelo rotulou incorretamente como BOAALB, de
modo que o número de arquivos em cada pasta fornece a precisão daquela classe.
Os rótulos identificados durante a revisão são incluídos no fim do nome do
arquivo, o que permite ler a árvore de pastas sem consultar o registro:

```
PONTO_A/BOAALB/clipe.wav
   ├── ✔ Correto                   →  reviau/correct/PONTO_A/BOAALB/clipe_BOAALB.wav
   ├── ✔ Correto, + PHYLUT         →  reviau/correct/PONTO_A/BOAALB/clipe_BOAALB_PHYLUT.wav
   ├── ✘ Incorreto, TURDRU         →  reviau/incorrect/PONTO_A/BOAALB/clipe_TURDRU.wav
   ├── ✘ Incorreto, TURDRU+PHYLUT  →  reviau/incorrect/PONTO_A/BOAALB/clipe_TURDRU_PHYLUT.wav
   ├── ✘ Incorreto, nenhum         →  reviau/incorrect/PONTO_A/BOAALB/clipe.wav
   └── ? Incerto                   →  reviau/uncertain/PONTO_A/BOAALB/clipe.wav
```

- O nome do arquivo **recebe os rótulos que o clipe comprovadamente contém**. Um
  clipe correto recebe a previsão confirmada, seguida de qualquer rótulo
  acrescentado; um clipe incorreto recebe os rótulos que descrevem o que ele de
  fato contém. Os rótulos acrescentados seguem a ordem em que foram selecionados,
  com espaços escritos como `_` (`chuva forte` passa a `_chuva_forte`), e o nome
  original é mantido integralmente antes deles. Um Incorreto sem nenhum rótulo da
  lista, e todo segmento marcado como Incerto, mantêm o nome inalterado.
- Quando o rótulo é lido do nome do arquivo, a previsão já faz parte do nome e
  não é acrescentada uma segunda vez.
- Com nível do rótulo acima de 0, as pastas *abaixo* do rótulo **não** são recriadas:
  `BOAALB/PONTO_A/20240115/clipe.wav` corrigido para TURDRU passa a
  `incorrect/BOAALB/clipe_TURDRU.wav`, com uma pasta por rótulo previsto contendo
  diretamente os clipes.
- Um clipe que chegou **sem rótulo** não tem previsão a avaliar. Ele é arquivado
  em `labelled/`, mantendo as pastas em que estava, e todos os rótulos atribuídos
  são acrescentados ao seu nome.
- Um nome já existente recebe o sufixo `_2`, `_3`, …; um arquivo revisado nunca é
  sobrescrito.
- A pasta de onde o clipe foi retirado é **removida quando o seu último clipe é
  arquivado**, juntamente com as pastas superiores que fiquem vazias, de modo que
  a árvore de segmentos pendentes diminui à medida que a revisão avança. Uma pasta
  que ainda contenha qualquer item, seja um clipe pendente ou outro arquivo, é
  preservada, e a pasta de segmentos em si nunca é removida.
- Clipes já arquivados em `reviau/` são excluídos da lista de pendentes, de modo
  que a revisão pode ser distribuída em várias sessões.

As pastas de veredito são sempre `correct/`, `incorrect/`, `uncertain/` e
`labelled/`, e o registro da revisão sempre grava esses nomes de resultado,
qualquer que seja o idioma da interface. Os dados gravados por uma revisão,
portanto, nunca dependem do idioma em que ela foi realizada.

## Gravação em Outro Local

`--output` (ou `-o`) substitui a pasta `reviau/` por uma pasta escolhida pelo
revisor, por exemplo em outro disco. As pastas de veredito, o registro da
revisão, a lista de rótulos, as configurações de leitura e a tabela de anotações
são todos gravados nela:

```bash
reviau /dados/segmentos --output /dados/revisados
```

Um caminho relativo é resolvido a partir da pasta de segmentos (`-o revisados`
corresponde a `/dados/segmentos/revisados/`), um caminho absoluto é utilizado tal
como informado, e, via SSH, o caminho refere-se à máquina remota. Para retomar
uma revisão, deve-se informar novamente o mesmo `--output`: é nessa pasta que são
feitas as contagens de segmentos já revisados, e os clipes já gravados nela nunca
retornam à lista de pendentes. Como a opção se aplica a todas as pastas abertas
durante a sessão, um `--output` absoluto destina-se à revisão de um único
conjunto; as pastas abertas com ele compartilham uma única pasta de resultados.

## O Registro da Revisão

Cada revisão acrescenta uma linha a **`reviews.csv`**, na pasta `reviau/`. O
registro é sempre gravado e constitui o histórico da revisão:

| Coluna | Conteúdo |
| --- | --- |
| `reviewed_at` | Data e hora da revisão, com o fuso horário |
| `source`, `destination` | O local original do clipe, relativo à pasta de segmentos, e o novo local, relativo à pasta `reviau/` |
| `predicted`, `score` | O rótulo com que o clipe chegou e a pontuação indicada no seu nome |
| `outcome` | `correct`, `incorrect`, `uncertain` ou `labelled` |
| `labels` | Os rótulos identificados pelo revisor no clipe, separados por `;`; vazio quando o clipe não contém nenhum rótulo da lista |
| `added` | Os rótulos além da previsão: a correção ou uma espécie adicional |
| `site`, `recording`, `start_time`, `end_time` | Como na tabela de anotações descrita abaixo |

A precisão de cada classe é `correct / (correct + incorrect)`, agrupada por
`predicted`; a comparação entre `predicted` e `labels` nas linhas incorretas
fornece a confusão entre classes. Se o registro não puder ser gravado, o clipe é
devolvido ao local original e a revisão é recusada, de modo que um clipe nunca é
arquivado sem a linha correspondente.

## A Tabela de Anotações

Com `--annotations`, cada rótulo que um segmento **comprovadamente contém** é
acrescentado a `annotations.csv`, na pasta `reviau/`, com as colunas
`site, file, label, start_time, end_time`, com uma linha por rótulo; assim, um
segmento com duas espécies gera duas linhas. Uma previsão rejeitada nunca consta
da tabela, tampouco segmentos marcados como incertos ou sem nenhum rótulo da
lista. Os tempos indicam a posição do clipe na gravação da qual foi recortado;
são lidos do seu nome e ampliados até a duração real do clipe, de modo que
eventual margem (padding) seja incluída.

`file` identifica essa gravação de origem. Como o nome de um clipe raramente
identifica a gravação da qual foi recortado, a gravação é procurada num arquivo
opcional `segment_sources.csv` (`segment,recording`), na pasta de segmentos. Na
ausência desse arquivo, a coluna permanece vazia e a interface informa o fato
abaixo dos botões.

As linhas são gravadas à medida que cada segmento é revisado, e uma tabela
existente é complementada, de modo que revisões distribuídas em várias sessões se
acumulam na mesma tabela. `--annotations-path` grava a tabela em outro local.
