# (| |) reviau

*[English](README.md) · Português (Brasil)*

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
revisão dos segmentos que métodos de detecção como **template matching**,
**busca vetorial** (*vector search*) e **classificadores personalizados** em
validação encontram em gravações de campo, por exemplo as do monitoramento
acústico passivo. Seu uso, contudo, não se restringe a esses métodos, e a
ferramenta aceita qualquer conjunto de clipes, independentemente de como tenha
sido produzido, inclusive exemplos recortados manualmente. A pasta de segmentos
pode ser **local** ou **remota, via SSH**, e a interface pode ser
disponibilizada para **outra máquina** numa rede local ou numa rede Tailscale. A
interface está disponível em **Português (Brasil)** e **Inglês**.

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

**Com uv ou pip.** O reviau está publicado no PyPI e requer o Python 3.10 ou
posterior:

```bash
uv tool install reviau   # como ferramenta de linha de comando isolada
pip install reviau       # ou com pip, no ambiente atual
```

[Instalação](docs/pt-BR/installation.md) descreve o que o instalador faz, a
atualização e a desinstalação.

## Início Rápido

```bash
reviau --lang pt-BR                                   # iniciar e abrir uma pasta pelo navegador
reviau ~/segmentos --lang pt-BR                       # abrir uma pasta local na inicialização
reviau ssh://usuario@servidor/dados/segmentos --lang pt-BR   # segmentos num servidor, via SSH
reviau ~/segmentos --lang pt-BR --annotations         # com tabela de anotações
```

O comando exibe o endereço a ser aberto e abre o navegador nele. Por padrão, a
pasta do clipe é o seu rótulo, e o nome é lido como
`[ponto]_[AAAAMMDD]_[HHMMSS]_[início]_[fim]_*`; ambos podem ser alterados por
pasta no botão **⚙**. No navegador, <kbd>T</kbd>, <kbd>F</kbd> e <kbd>U</kbd>
registram correto, incorreto e incerto, <kbd>1</kbd>…<kbd>9</kbd> acrescentam
rótulos, e <kbd>Espaço</kbd> reproduz o clipe. `reviau --help` lista todas as
opções.

## Documentação

| Página | Conteúdo |
|---|---|
| [Instalação](docs/pt-BR/installation.md) | O instalador, uv e pip, atualização e desinstalação |
| [Como um Segmento É Lido](docs/pt-BR/segments.md) | O rótulo a partir da pasta, o nível do rótulo, o padrão de nome padrão |
| [Revisão no Navegador](docs/pt-BR/reviewing.md) | Abertura de uma pasta, os controles, como o resultado é determinado, atalhos de teclado |
| [A Pasta reviau](docs/pt-BR/reviau-folder.md) | A lista de rótulos, onde o clipe revisado é arquivado, `--output`, o registro da revisão, a tabela de anotações |
| [Configurações de Leitura](docs/pt-BR/reading-settings.md) | Modelos de nome por pasta, expressões regulares, a origem do rótulo, a predefinição de busca vetorial |
| [Revisão via SSH](docs/pt-BR/ssh.md) | Pastas remotas, autenticação, o que é gravado na máquina remota |
| [Execução num Servidor](docs/pt-BR/server.md) | Disponibilização da interface para outra máquina, o token de acesso, Tailscale e túneis SSH |
| [Opções da Linha de Comando](docs/pt-BR/cli.md) | Exemplos e todas as opções |
| [Desenvolvimento](docs/pt-BR/development.md) | Trabalho no próprio reviau, testes e integração contínua |

## Licença

MIT; consulte [LICENSE](LICENSE).
