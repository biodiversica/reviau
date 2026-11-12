# (| reviau |)

[← English](README.md)

O reviau é uma ferramenta que disponibiliza uma
**interface no navegador para a revisão de uma pasta de segmentos de áudio**.
Cada clipe é apresentado como espectrograma, acompanhado das informações
fornecidas pela sua pasta e pelo nome do seu arquivo. O revisor ouve o clipe e
registra **o que ele contém**; a avaliação do rótulo com que o clipe chegou, como
**correto** ou **incorreto**, decorre dessa resposta. Os clipes revisados são
movidos para `correct/`, `incorrect/` ou `uncertain/`, cada revisão é registrada
em `reviews.csv` (previsão, resultado e os rótulos efetivamente identificados), e
os rótulos confirmados podem também ser gravados numa tabela de anotações. Tudo
isso é mantido numa única pasta, **`reviau/`**, dentro da pasta de segmentos, e
nada é gravado ao lado dos próprios clipes.

O reviau foi desenvolvido inicialmente para **análises bioacústicas**, para a
revisão dos segmentos que métodos de detecção como **template matching**, **busca vetorial** (*vector search*) e **classificadores
personalizados** em validação encontram em gravações de campo, por exemplo as
do monitoramento acústico passivo. Seu uso, contudo, não se restringe a esses
métodos, e a ferramenta aceita qualquer conjunto de clipes, independentemente
de como tenha sido produzido, inclusive exemplos recortados manualmente. A
pasta de segmentos pode ser **local** ou **remota, via SSH**, e a interface pode
ser disponibilizada para **outra máquina** numa rede local ou numa rede
Tailscale. A interface está disponível em **Português (Brasil)** e **Inglês**.

---

## Como um segmento é lido

As informações de um segmento provêm de duas fontes independentes, ambas
configuráveis.

**A pasta fornece o rótulo.** Um conjunto em revisão costuma ser organizado com
uma pasta por classe, de modo que a pasta em que o clipe se encontra é o rótulo
que ele carrega:

```
segmentos/
├── PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1.wav   → rótulo BOAALB
├── PONTO_A/PHYLUT/PONTO_A_20240115_061500_3.5_8.5_det2.wav     → rótulo PHYLUT
└── chuva/POCA_20240116_200000_5.0_10.0_det4.wav                → rótulo chuva
```

As pastas acima do rótulo são preservadas: `2024/campo/PONTO_A/BOAALB/` rotula o
clipe como `BOAALB` e mantém as três pastas acima dele. Um clipe situado
diretamente na pasta de segmentos não tem rótulo.

**Conjuntos com a pasta da classe no topo.** Alguns conjuntos são organizados de
forma inversa, com os pontos *dentro* de cada pasta de classe. Nesse caso, o
**nível do rótulo**, nas [configurações de leitura](#configurações-de-leitura),
indica qual nível carrega o rótulo, contado a partir da pasta de segmentos. As pastas abaixo desse nível são lidas, mas não mantidas: não são
oferecidas como rótulos, e o clipe revisado é arquivado apenas sob o seu rótulo,
uma vez que o ponto e a data já constam no nome do arquivo.

```
segmentos/                             # nível do rótulo 1
├── BOAALB/PONTO_A/20240115/clipe.wav  → rótulo BOAALB; as duas pastas abaixo não são mantidas
├── BOAALB/POCA/clipe.wav              → rótulo BOAALB
└── PHYLUT/clipe.wav                   → rótulo PHYLUT (menos profundo que o nível, ainda rotulado)
```

**O nome do arquivo fornece as demais informações.** Por padrão, o nome é lido
como

```
[ponto]_[AAAAMMDD]_[HHMMSS]_[início]_[fim]_*
      PONTO_A_20240115_053000_12.0_17.0_det1.wav
```

- O ponto pode conter sublinhados; a leitura é ancorada na data e na hora.
- `início` e `fim` indicam a posição do clipe, em segundos, na gravação da qual
  ele foi recortado. As duas formas são aceitas: `12.0_17.0` e `12.0-17.0s`.
- `_*` corresponde a qualquer texto restante, exibido na interface como *Outros*.
- Todas as partes após o ponto são opcionais, e **um nome que não corresponda a
  nenhuma parte do padrão pode ainda assim ser revisado**; a interface apenas
  exibe menos informações sobre ele.

Conjuntos nomeados segundo outra convenção podem ser descritos nas
[configurações de leitura](#configurações-de-leitura).

---

## Instalação

**Sem Python.** O instalador configura tudo o que é necessário e adiciona o
comando `reviau`. Executá-lo novamente atualiza a instalação.

No Windows, abra o PowerShell e execute:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | iex"
```

No macOS e no Linux, abra um terminal e execute:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
```

O instalador realiza as seguintes etapas:

1. Instala o [uv](https://docs.astral.sh/uv/) em `~/.local/bin`, caso ainda não
   esteja presente. O uv obtém o seu próprio Python, de modo que nenhuma
   instalação prévia é necessária, e qualquer instalação existente do Python
   permanece inalterada.
2. Executa `uv tool install --python 3.12 reviau`, que instala a ferramenta num
   ambiente isolado e adiciona `reviau` ao PATH.

O comando fica disponível nos terminais abertos após a instalação. A variável de
ambiente `REVIAU_PACKAGE` altera o que o instalador instala (por exemplo, uma
versão específica, como `reviau==0.1.0`). Para desinstalar, execute
`uv tool uninstall reviau`.

**Com uv ou pip.** O reviau está publicado no PyPI e requer o Python 3.10 ou
posterior:

```bash
uv tool install reviau   # como ferramenta de linha de comando isolada
pip install reviau       # ou com pip, no ambiente atual
```

`uv tool upgrade reviau` atualiza a ferramenta. Ela também pode ser executada
uma única vez, sem instalação permanente, com `uvx reviau /caminho/dos/segmentos`.

As bibliotecas de áudio (librosa e soundfile) dependem da `libsndfile`, que já
está incluída nos seus wheels para Linux, macOS e Windows.

---

## Uso

```bash
# Iniciar sem pasta e abrir uma pelo navegador
reviau --lang pt-BR

# Abrir uma pasta local na inicialização, com a interface nesta máquina
reviau ~/segmentos --lang pt-BR

# Uma lista de rótulos compartilhada por todas as pastas e tabela de anotações
reviau ~/segmentos --lang pt-BR --labels-file ~/classes.txt --annotations

# Segmentos num servidor, revisados a partir de outro computador
reviau ssh://usuario@servidor/dados/segmentos --lang pt-BR

# Disponibilizar a interface para a rede (rede local, Tailscale, …)
reviau /dados/segmentos --host 0.0.0.0 --port 8765
```

O comando exibe um resumo e o endereço a ser aberto. Com `--host 0.0.0.0`, exibe
também o endereço que as outras máquinas devem utilizar.

### Abertura de uma pasta

A **caixa de pasta**, no topo da página, indica qual pasta de segmentos está em
revisão. Ao digitar outro caminho e pressionar <kbd>Enter</kbd>, ou ao selecionar
uma pasta em **Procurar…**, essa pasta é aberta no lugar da atual, sem que o
comando precise ser reiniciado. Quando o comando é iniciado sem a pasta
`SEGMENTOS`, a página exibe apenas a caixa de pasta.

- A caixa de pasta aceita os mesmos caminhos da linha de comando: uma pasta
  local, um caminho iniciado por `~/` ou `ssh://usuario@host/caminho` para uma
  pasta remota, acessada com as configurações SSH da linha de comando
  (`--ssh-key`, `~/.ssh/config`, o agente SSH etc.).
- Toda pasta aberta recebe as opções com que o comando foi iniciado, como
  `--output`, `--labels-file` e `--annotations`. A forma de leitura dos nomes é
  uma configuração da própria pasta; consulte
  [Configurações de leitura](#configurações-de-leitura).
- **A abertura de uma pasta não grava nada nela.** A pasta `reviau/` é criada
  quando o primeiro segmento é revisado; assim, uma pasta aberta por engano, por
  erro de digitação ou um nível acima do pretendido, permanece inalterada.
- Uma pasta `reviau/` que contém os resultados de uma revisão não pode ser aberta
  como pasta de segmentos, pois os seus clipes revisados seriam oferecidos para
  revisão uma segunda vez; deve-se abrir a pasta que a contém.
- Uma pasta que não pode ser aberta é recusada com a respectiva explicação, e a
  revisão em andamento não é afetada.
- **Procurar…** lista as pastas da máquina em que o revisor é executado, que é a
  máquina que lê os clipes; quando a interface é disponibilizada para outro
  computador, essa não é a máquina do navegador. Pastas que contêm clipes são
  marcadas com ♪. Pastas remotas `ssh://` não podem ser navegadas e devem ser
  digitadas.
- As pastas abertas recentemente são sugeridas durante a digitação. Esse
  histórico é armazenado no navegador.
- Quando o padrão de nome reconhece apenas parte dos nomes da pasta recém-aberta,
  um aviso abaixo da caixa de pasta informa o fato, com um nome que não foi
  reconhecido.

### No navegador

| Controle | Função |
| --- | --- |
| **Botões de rótulo** | Rótulos de qualquer *outro* conteúdo do clipe, ou do que o clipe efetivamente contém. Cada segmento começa sem rótulo selecionado; um clique seleciona o rótulo, e um novo clique desfaz a seleção. O botão do rótulo previsto é identificado como **◆ previsto** e não pode ser selecionado: a previsão é avaliada com Correto ou Incorreto. <kbd>1</kbd>…<kbd>9</kbd> selecionam os nove primeiros rótulos. |
| **✔ Correto** | A previsão está correta. O segmento é salvo com a previsão e com qualquer rótulo selecionado, por exemplo uma segunda espécie vocalizando ao mesmo tempo. O botão indica o que será salvo: *✔ Correto + PHYLUT*. |
| **✘ Incorreto** | A previsão está incorreta. O segmento é salvo com os rótulos selecionados, que descrevem o que o clipe efetivamente contém, ou, se nenhum estiver selecionado, como sem nenhum rótulo da lista. O botão indica o caso: *✘ Incorreto → TURDRU* ou *✘ Incorreto · nenhum rótulo da lista*. |
| **? Incerto** | Não é possível avaliar o clipe. Ele é arquivado em `uncertain/` e excluído das contagens de corretos e incorretos e da tabela de anotações. |
| **← Anterior / Próximo →** | Navega entre os segmentos sem registrar decisão. |
| **Tipo / Mínimo (Hz) / Máximo (Hz) / Limite inferior (dB)** | Redesenham o espectrograma imediatamente, em eixo de frequência mel, linear ou logarítmico. O reprodutor de áudio não é afetado, de modo que a reprodução continua enquanto a visualização é alterada. A visualização é armazenada no navegador. |
| **✎** | Edita a lista de rótulos: cada botão exibe um **×** que o remove, e o campo abaixo adiciona um novo rótulo. As alterações são salvas no arquivo da lista de rótulos (por padrão, `reviau/labels.txt`). |
| **⚙** | Abre as [configurações de leitura](#configurações-de-leitura) da pasta: padrão de nome, formato de data e hora, origem do rótulo e nível do rótulo. |
| **⟳** | Reexamina a pasta, por exemplo após a inclusão de novos segmentos. |
| **Idioma** | Alterna a interface entre Português e Inglês. |
| **◐ / ☀ / ☾** | Tema: padrão do sistema, claro ou escuro; cada clique seleciona o seguinte. O tema selecionado é armazenado no navegador. O espectrograma mantém suas cores nos dois temas. |

A previsão é a pergunta, e Correto ou Incorreto é a resposta; os botões de rótulo
apenas acrescentam o que mais houver no clipe. Nenhum rótulo vem selecionado de
antemão, de modo que um segmento rejeitado sem outra seleção é salvo como sem
nenhum rótulo da lista, e nunca com um rótulo herdado do clipe anterior. Quando o
segmento não tem previsão a avaliar, um único botão **✔ Salvar** grava os rótulos
selecionados. O servidor determina o resultado a partir dos rótulos recebidos,
segundo uma única regra:

| Rótulos salvos | Resultado |
| --- | --- |
| a previsão | correto |
| a previsão e outros rótulos | correto (os demais rótulos são registrados como *added*) |
| apenas outros rótulos | incorreto; o clipe contém esses rótulos |
| nenhum | incorreto; o clipe não contém nenhum rótulo da lista |
| qualquer um, com Incerto | incerto |

Após a revisão, o clipe é retirado da lista e o próximo é exibido
automaticamente.

Um segmento pode receber vários rótulos, por exemplo quando duas espécies
vocalizam ao mesmo tempo. Esse é o comportamento padrão; `--no-multi-label`
limita cada segmento a um único rótulo.

Atalhos de teclado: <kbd>←</kbd> e <kbd>→</kbd> navegam entre os segmentos;
<kbd>T</kbd>, <kbd>F</kbd> e <kbd>U</kbd> registram correto, incorreto e incerto;
<kbd>1</kbd>…<kbd>9</kbd> marcam ou desmarcam os nove primeiros rótulos;
<kbd>Espaço</kbd> reproduz ou pausa o áudio.

### A pasta reviau

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
[Gravação em outro local](#onde-o-clipe-revisado-é-arquivado).

### A lista de rótulos

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

### Onde o clipe revisado é arquivado

Um clipe revisado é arquivado na pasta `reviau/`, sob o seu **resultado**,
seguido do caminho que tinha, incluindo a pasta do rótulo **previsto**. Cada pasta responde, portanto, a
uma única pergunta: `incorrect/PONTO_A/BOAALB/` contém exatamente os clipes que o
modelo rotulou incorretamente como BOAALB, de modo que o número de arquivos em
cada pasta fornece a precisão daquela classe. Os rótulos acrescentados durante a
revisão são incluídos no fim do nome do arquivo, o que permite ler a árvore de
pastas sem consultar o registro:

```
PONTO_A/BOAALB/clipe.wav
   ├── ✔ Correto                   →  reviau/correct/PONTO_A/BOAALB/clipe.wav
   ├── ✔ Correto, + PHYLUT         →  reviau/correct/PONTO_A/BOAALB/clipe_PHYLUT.wav
   ├── ✘ Incorreto, TURDRU         →  reviau/incorrect/PONTO_A/BOAALB/clipe_TURDRU.wav
   ├── ✘ Incorreto, TURDRU+PHYLUT  →  reviau/incorrect/PONTO_A/BOAALB/clipe_TURDRU_PHYLUT.wav
   ├── ✘ Incorreto, nenhum         →  reviau/incorrect/PONTO_A/BOAALB/clipe.wav
   └── ? Incerto                   →  reviau/uncertain/PONTO_A/BOAALB/clipe.wav
```

- O nome do arquivo **recebe cada rótulo acrescentado além da previsão**, na
  ordem em que foram selecionados, com espaços escritos como `_` (`chuva forte`
  passa a `_chuva_forte`). O nome original é mantido integralmente antes deles.
  Quando nenhum rótulo é acrescentado (um Correto simples, ou um Incorreto sem
  nenhum rótulo da lista), e para todo segmento marcado como Incerto, o nome
  permanece inalterado.
- Com nível do rótulo acima de 0, as pastas *abaixo* do rótulo **não** são recriadas:
  `BOAALB/PONTO_A/20240115/clipe.wav` corrigido para TURDRU passa a
  `incorrect/BOAALB/clipe_TURDRU.wav`, com uma pasta por rótulo previsto contendo
  diretamente os clipes.
- Um clipe que chegou **sem rótulo** não tem previsão a avaliar. Ele é arquivado
  em `labelled/`, mantendo as pastas em que estava, e todos os rótulos atribuídos
  são acrescentados ao seu nome.
- Os nomes das pastas são os mesmos em qualquer idioma da interface.
- Um nome já existente recebe o sufixo `_2`, `_3`, …; um arquivo revisado nunca é
  sobrescrito.
- A pasta de onde o clipe foi retirado é **removida quando o seu último clipe é
  arquivado**, juntamente com as pastas superiores que fiquem vazias, de modo que
  a árvore de segmentos pendentes diminui à medida que a revisão avança. Uma pasta
  que ainda contenha qualquer item, seja um clipe pendente ou outro arquivo, é
  preservada, e a pasta de segmentos em si nunca é removida.
- Clipes já arquivados em `reviau/` são excluídos da lista de pendentes, de modo
  que a revisão pode ser distribuída em várias sessões.

**Gravação em outro local.** `--output` (ou `-o`) substitui a pasta `reviau/`
por uma pasta escolhida pelo revisor, por exemplo em outro disco. As pastas de
veredito, o registro da revisão, a lista de rótulos, as configurações de leitura
e a tabela de anotações são todos gravados nela:

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

### O registro da revisão

Cada revisão acrescenta uma linha a **`reviews.csv`**, na pasta `reviau/`. O registro é sempre gravado e constitui o histórico da revisão:

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

### A tabela de anotações

Com `--annotations`, cada rótulo que um segmento **comprovadamente contém** é
acrescentado a `annotations.csv`, na pasta `reviau/`, com as colunas `site, file, label, start_time,
end_time`, com uma linha por rótulo; assim, um segmento com duas espécies gera
duas linhas. Uma previsão rejeitada nunca consta da tabela, tampouco segmentos
marcados como incertos ou sem nenhum rótulo da lista. Os tempos indicam a posição
do clipe na gravação da qual foi recortado; são lidos do seu nome e ampliados até
a duração real do clipe, de modo que eventual margem (padding) seja incluída.

`file` identifica essa gravação de origem. Como o nome de um clipe raramente
identifica a gravação da qual foi recortado, a gravação é procurada num arquivo
opcional `segment_sources.csv` (`segment,recording`), na pasta de segmentos. Na
ausência desse arquivo, a coluna permanece vazia e a interface informa o fato
abaixo dos botões.

As linhas são gravadas à medida que cada segmento é revisado, e uma tabela
existente é complementada, de modo que revisões distribuídas em várias sessões se
acumulam na mesma tabela.

---

## Configurações de leitura

A forma como os nomes de arquivo e as pastas de um conjunto são lidos é uma
característica do conjunto; por isso, é definida por pasta, no botão **⚙** ao
lado da caixa de pasta, e não na linha de comando. As configurações são salvas em
**`settings.json`**, na pasta `reviau/`, de modo que a pasta é reaberta com as
suas próprias configurações em qualquer máquina e em qualquer navegador. Assim
como a lista de rótulos, o arquivo é gravado apenas quando as configurações são
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

### Elaboração de um modelo

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

### Elaboração de uma expressão regular

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

### Origem do rótulo

Com a origem *Automática*, um padrão que captura um grupo `label` lê o rótulo do
nome do arquivo, e qualquer outro padrão o lê da pasta. Quando o rótulo é lido do
nome do arquivo, o clipe é arquivado diretamente sob o resultado e o rótulo
previsto, por exemplo `incorrect/BOAALB/clipe_TURDRU.wav`.

Para manter as pastas, a origem *Pasta* deve ser selecionada explicitamente. Para
segmentos organizados como `[rótulo]/[ponto]_AAAAMMDD/clipe.wav`, a origem *Pasta*
com nível do rótulo 1 lê o rótulo da pasta superior e mantém a pasta do ponto
abaixo dela, enquanto o ponto, os horários e a pontuação continuam a ser lidos do
nome do arquivo.

### A predefinição de busca vetorial

A predefinição *busca vetorial* lê nomes no formato
`PONTO_AAAAMMDD_HHMMSS_INÍCIO-FIMs_PONTUAÇÃO_RÓTULO.wav`, gravados pelos notebooks
de busca vetorial bioacústica, com o **rótulo e a pontuação de similaridade no
nome**.

Como o rótulo faz parte do nome, os clipes são arquivados diretamente sob o
resultado e o rótulo previsto (`correct/BOAALB/`, `incorrect/BOAALB/`), e os
rótulos acrescentados são incluídos no fim do nome, como nos demais casos: um
segmento chamado `..._0.873_BOAALB.wav` e corrigido para TURDRU passa a
`incorrect/BOAALB/..._0.873_BOAALB_TURDRU.wav`. A pontuação é exibida ao lado do
rótulo na interface e também consta do registro.

---

## Revisão de segmentos via SSH

Quando uma pasta remota é indicada, todas as operações são realizadas via SFTP: a
listagem da pasta, a leitura dos clipes, a movimentação para as pastas de
veredito e a gravação do registro e da tabela de anotações. Os clipes são
armazenados localmente em cache à medida que são abertos, de modo que o retorno a
um clipe anterior dispensa novo download.

```bash
reviau ssh://usuario@servidor:22/dados/segmentos
reviau servidor:/dados/segmentos           # endereço no estilo scp
reviau ssh://servidor/dados/segmentos --ssh-key ~/.ssh/id_campo
```

O usuário e a porta são informados no endereço (`ssh://usuario@host:porta/caminho`)
ou obtidos de `~/.ssh/config`, juntamente com apelidos de host e arquivos de
identidade, e um agente SSH em execução é utilizado. Quando não é possível usar
uma chave nem um agente, a senha é lida da variável de ambiente
`REVIAU_SSH_PASSWORD`; ela nunca é aceita na linha de comando, onde ficaria
registrada no histórico do terminal. Uma chave de host desconhecida é recusada,
salvo se `--accept-new-host-key` for informado.

Na máquina remota, nada é gravado fora da pasta `reviau/` (ou da pasta de
`--output`), e nenhum clipe é apagado: os clipes revisados são apenas movidos da
pasta de segmentos para ela.

---

## Execução num servidor

A interface é uma página web comum; assim, a ferramenta pode ser executada na
máquina que armazena o áudio e utilizada a partir de qualquer outra:

```bash
reviau /dados/segmentos --host 0.0.0.0 --port 8765 --no-open
```

Quando um endereço diferente do loopback é utilizado, um **token de acesso** é
gerado e incluído no endereço exibido; após a abertura desse endereço, o token é
armazenado num cookie. `--token meusegredo` define o token explicitamente, e
`--no-auth` disponibiliza a interface sem token.

O token impede o acesso casual, mas não oferece criptografia (TLS). Quem o
possuir pode abrir e revisar (e, portanto, mover clipes de) qualquer pasta que o
revisor consiga ler, além de listar os nomes das pastas daquela máquina. O token
deve, portanto, ser tratado como uma senha, e o uso de `--no-auth` deve ser
evitado em redes compartilhadas. Em redes não confiáveis, recomenda-se o
Tailscale (vinculando ao endereço do Tailscale, ou a `0.0.0.0` numa máquina
acessível apenas pela tailnet) ou um túnel SSH:

```bash
# no servidor
reviau /dados/segmentos --port 8765 --no-open
# no computador local
ssh -N -L 8765:127.0.0.1:8765 usuario@servidor   # em seguida, abrir http://127.0.0.1:8765
```

A ferramenta atende a um revisor por vez. A lista de pendentes, a posição atual e
a pasta aberta são mantidas pelo servidor; assim, dois navegadores conectados à
mesma instância controlam a mesma sessão, e uma pasta aberta num deles é aberta
em ambos.

---

## Opções

```
reviau [SEGMENTOS] [OPÇÕES]

  SEGMENTOS                     Pasta a abrir na inicialização: caminho local, ou
                                ssh://[usuário@]host[:porta]/caminho. Opcional; a
                                pasta pode ser aberta, e trocada, no navegador

  -l, --lang TEXT               Idioma inicial da interface: en, pt-BR  [padrão: en]
      --labels-file TEXT        Local da lista de rótulos, um rótulo por linha.
                                Caminhos relativos ficam dentro da pasta reviau; um
                                caminho absoluto compartilha uma lista entre as
                                pastas  [padrão: <saída>/labels.txt]
      --no-multi-label          Limita cada segmento a um rótulo (por padrão, um
                                segmento pode receber vários rótulos)
      --annotations             Grava também a tabela de rótulos confirmados
      --annotations-path TEXT   Local da tabela  [padrão: <saída>/annotations.csv]

  -o, --output TEXT             Pasta em que os segmentos revisados, o reviews.csv,
                                o labels.txt e o settings.json são gravados
                                [padrão: <SEGMENTOS>/reviau]

      --host TEXT               Endereço de vinculação  [padrão: 127.0.0.1]
  -p, --port INTEGER            Porta  [padrão: 8765]
      --token TEXT              Token de acesso da interface
      --no-auth                 Disponibiliza a interface sem token de acesso
      --open / --no-open        Abre o navegador na inicialização  [padrão: abre]

      --ssh-key TEXT            Arquivo de chave privada para conexões SSH
      --known-hosts TEXT        Arquivo known_hosts adicional a ser considerado
                                confiável
      --accept-new-host-key     Aceita uma chave de host SSH desconhecida
      --cache-dir TEXT          Local do cache dos clipes remotos
                                [padrão: uma pasta temporária]

      --version                 Exibe a versão e encerra

  Ambiente: REVIAU_SSH_PASSWORD  Senha SSH, quando não é possível usar chave ou agente
```

O padrão de nome, o formato de data e hora, a origem do rótulo e o nível do
rótulo são definidos por pasta nas
[configurações de leitura](#configurações-de-leitura), e a visualização do
espectrograma é definida na interface e armazenada no navegador.

### Pastas de veredito e idioma

As pastas de veredito são sempre `correct/`, `incorrect/`, `uncertain/` e
`labelled/`, e o registro da revisão sempre grava esses nomes de resultado,
qualquer que seja o idioma da interface. Os dados gravados por uma revisão,
portanto, nunca dependem do idioma em que ela foi realizada.

---

## Desenvolvimento

```bash
git clone https://github.com/biodiversica/reviau
cd reviau
uv sync               # instala o projeto e as ferramentas de desenvolvimento
uv run ruff check .   # lint
uv run pytest         # testes
uv run reviau /caminho/dos/segmentos
```

A suíte de testes abrange as regras de nome, o arquivamento dos clipes revisados,
a API HTTP, os textos da interface nos dois idiomas e uma revisão completa
conduzida por um servidor SFTP em processo. As funções auxiliares do cliente que
independem do DOM são testadas com Node.js, e esses testes são ignorados quando o
Node.js não está instalado. A integração contínua executa o lint e os testes no
Linux, no macOS e no Windows, e também executa os instaladores nos três sistemas
com o pacote gerado, seguidos de `scripts/smoke_test.py`, que revisa um clipe com
o comando instalado.

Antes de enviar as alterações (push), recomenda-se executar também a suíte tal
como a integração contínua a executa:

```bash
GITHUB_ACTIONS=true uv run pytest
```

O Rich colore a saída de ajuda do Typer sempre que detecta um terminal, o que
ocorre invariavelmente no GitHub Actions. Isso altera a saída renderizada o
suficiente para quebrar um teste que passa localmente.

### Publicação de uma versão

Defina a nova versão em `pyproject.toml` e em `src/reviau/__init__.py`, execute
`uv lock`, registre a alteração (commit) e, em seguida, crie e envie uma tag:

```bash
git tag v0.2.0 && git push origin v0.2.0
```

A tag aciona `.github/workflows/release.yml`. Os testes são executados nos três
sistemas, o pacote é enviado ao PyPI e uma versão **em rascunho** é criada no
GitHub, com os instaladores anexados e as notas de `.github/release-notes.md`.
Depois de redigidos os destaques, a versão deve ser publicada, pois os comandos
de instalação baixam a partir da versão *publicada* mais recente. A geração do
pacote falha se a tag não corresponder à versão de `pyproject.toml`, ou se essa
versão diferir da de `src/reviau/__init__.py`.

## Licença

MIT; consulte [LICENSE](LICENSE).
