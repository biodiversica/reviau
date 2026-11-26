# Revisão no Navegador

*[English](../en/reviewing.md) · Português (Brasil)*

## Abertura de uma Pasta

A **caixa de pasta**, no topo da página, indica qual pasta de segmentos está em
revisão. Ao digitar outro caminho e pressionar <kbd>Enter</kbd>, ou ao selecionar
uma pasta em **Procurar…**, essa pasta é aberta no lugar da atual, sem que o
comando precise ser reiniciado. Quando o comando é iniciado sem a pasta
`SEGMENTOS`, a página exibe apenas a caixa de pasta.

- A caixa de pasta aceita os mesmos caminhos da linha de comando: uma pasta
  local, um caminho iniciado por `~/` ou `ssh://usuario@host/caminho` para uma
  pasta remota, acessada com as configurações SSH da linha de comando
  (`--ssh-key`, `~/.ssh/config`, o agente SSH etc.); consulte [SSH](ssh.md).
- Toda pasta aberta recebe as opções com que o comando foi iniciado, como
  `--output`, `--labels-file` e `--annotations`. A forma de leitura dos nomes é
  uma configuração da própria pasta; consulte
  [Configurações de Leitura](reading-settings.md).
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

## Controles

| Controle | Função |
| --- | --- |
| **Botões de rótulo** | Rótulos de qualquer *outro* conteúdo do clipe, ou do que o clipe efetivamente contém. Cada segmento começa sem rótulo selecionado; um clique seleciona o rótulo, e um novo clique desfaz a seleção. O botão do rótulo previsto é identificado como **◆ previsto** e não pode ser selecionado: a previsão é avaliada com Correto ou Incorreto. <kbd>1</kbd>…<kbd>9</kbd> selecionam os nove primeiros rótulos. |
| **✔ Correto** | A previsão está correta. O segmento é salvo com a previsão e com qualquer rótulo selecionado, por exemplo uma segunda espécie vocalizando ao mesmo tempo. O botão indica o que será salvo: *✔ Correto + PHYLUT*. |
| **✘ Incorreto** | A previsão está incorreta. O segmento é salvo com os rótulos selecionados, que descrevem o que o clipe efetivamente contém, ou, se nenhum estiver selecionado, como sem nenhum rótulo da lista. O botão indica o caso: *✘ Incorreto → TURDRU* ou *✘ Incorreto · nenhum rótulo da lista*. |
| **? Incerto** | Não é possível avaliar o clipe. Ele é arquivado em `uncertain/` e excluído das contagens de corretos e incorretos e da tabela de anotações. |
| **← Anterior / Próximo →** | Navega entre os segmentos sem registrar decisão. |
| **Tipo / Mínimo (Hz) / Máximo (Hz) / Limite inferior (dB)** | Redesenham o espectrograma imediatamente, em eixo de frequência mel, linear ou logarítmico. O reprodutor de áudio não é afetado, de modo que a reprodução continua enquanto a visualização é alterada. A visualização é armazenada no navegador. |
| **✎** | Edita a lista de rótulos: cada botão exibe um **×** que o remove, e o campo abaixo adiciona um novo rótulo. As alterações são salvas no arquivo da [lista de rótulos](reviau-folder.md#a-lista-de-rótulos) (por padrão, `reviau/labels.txt`). |
| **⚙** | Abre as [configurações de leitura](reading-settings.md) da pasta: padrão de nome, formato de data e hora, origem do rótulo e nível do rótulo. |
| **⟳** | Reexamina a pasta, por exemplo após a inclusão de novos segmentos. |
| **Idioma** | Alterna a interface entre Português e Inglês. |
| **◐ / ☀ / ☾** | Tema: padrão do sistema, claro ou escuro; cada clique seleciona o seguinte. O tema selecionado é armazenado no navegador. O espectrograma mantém suas cores nos dois temas. |

## Como o Resultado É Determinado

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

O destino de cada clipe revisado, e o que é registrado sobre ele, estão descritos
em [A Pasta reviau](reviau-folder.md).

## Atalhos de Teclado

| Tecla | Ação |
| --- | --- |
| <kbd>←</kbd> / <kbd>→</kbd> | Segmento anterior / seguinte |
| <kbd>T</kbd> | Correto |
| <kbd>F</kbd> | Incorreto |
| <kbd>U</kbd> | Incerto |
| <kbd>1</kbd>…<kbd>9</kbd> | Marcam ou desmarcam os nove primeiros rótulos |
| <kbd>Espaço</kbd> | Reproduz ou pausa o áudio |
