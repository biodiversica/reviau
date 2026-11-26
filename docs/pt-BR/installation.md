# Instalação

*[English](../en/installation.md) · Português (Brasil)*

**Sem Python.** O instalador configura tudo o que é necessário e adiciona o
comando `reviau` e um atalho **reviau** que abre a interface. Executá-lo
novamente atualiza a instalação.

No Windows, abra o PowerShell e execute:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex"
```

No macOS e no Linux, abra um terminal e execute:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
```

O instalador primeiro lista o que vai fazer e pede confirmação antes de alterar
qualquer coisa. Em seguida, realiza as seguintes etapas:

1. Instala o [uv](https://docs.astral.sh/uv/) em `~/.local/bin`, caso ainda não
   esteja presente. O uv obtém o seu próprio Python, de modo que nenhuma
   instalação prévia é necessária, e qualquer instalação existente do Python
   permanece inalterada.
2. Executa `uv tool install --python 3.12 reviau`, que instala a ferramenta num
   ambiente isolado e adiciona `reviau` ao PATH. O comando fica disponível nos
   terminais abertos após a instalação.
3. Adiciona um atalho **reviau**, com o logotipo `(| |)` como ícone: um atalho
   na Área de Trabalho e no menu Iniciar no Windows, `reviau.command` na Mesa do
   macOS e uma entrada no menu de aplicativos no Linux. O atalho executa
   `reviau` na pasta pessoal, sem pasta de segmentos aberta, de modo que a
   pasta é escolhida no navegador (consulte
   [Abertura de uma Pasta](reviewing.md#abertura-de-uma-pasta)). Ele também
   abre uma janela de terminal ao lado do navegador. Essa janela executa a
   interface, e fechá-la (ou pressionar Ctrl+C) a encerra.

Duas variáveis de ambiente alteram o comportamento do instalador:
`REVIAU_PACKAGE` (o que instalar, por exemplo uma versão específica, como
`reviau==0.1.0`) e `REVIAU_YES=1`, que dispensa a confirmação, para instalar
ou desinstalar a partir de um script.

**Desinstalação.** Execute o instalador novamente com `REVIAU_UNINSTALL`
definida. Ele lista o que vai remover e pede confirmação antes. No Windows,
feche primeiro a janela do reviau e, em seguida, execute no PowerShell:

```powershell
$env:REVIAU_UNINSTALL=1; irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex
```

No macOS e no Linux:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | REVIAU_UNINSTALL=1 sh
```

Isso remove o reviau, o seu atalho e o ícone do atalho. Os segmentos, e as
pastas `reviau/` que guardam as suas revisões, nunca são removidos. Um simples
`uv tool uninstall reviau` remove apenas o programa, deixando um atalho que não
funciona mais: apague-o manualmente (no Windows, **reviau** na Área de Trabalho
e no menu Iniciar).

**O que a desinstalação mantém.** O ambiente do próprio reviau, com todos os
pacotes Python instalados para ele, é removido, juntamente com o comando
`reviau`. Aquilo com que ele foi instalado permanece, pois o desinstalador não
tem como saber se outro programa o utiliza:

| Mantido | Onde | Motivo |
|---|---|---|
| uv | `~/.local/bin/uv` e `uvx` (`.exe` no Windows) | Outros programas podem utilizá-lo. |
| Python 3.12 | `uv python dir` | O Python do próprio uv, que outras ferramentas do uv podem utilizar. Se um Python 3.12 já estava instalado, o uv o utilizou e não baixou nenhum. |
| Cache de downloads do uv | `uv cache dir` | Compartilhado por tudo o que o uv instala. Guarda os pacotes baixados, que para o reviau somam várias centenas de MB, sendo llvmlite e scipy os maiores. |
| Segmentos e as suas pastas `reviau/` | | As revisões nunca são removidas. |
| Preferências da interface | O navegador | Idioma, tema, visualização do espectrograma e pastas recentes ficam guardados no navegador, que os apaga junto com os dados do site. |

Se nenhum outro programa da máquina utiliza o uv, o restante pode ser removido
manualmente após a desinstalação:

```bash
uv cache clean                # todos os pacotes baixados
uv python uninstall 3.12      # o Python do uv, se ele baixou um
```

e, por fim, o próprio uv, apagando `uv` e `uvx` de `~/.local/bin`.

**Com uv ou pip.** O reviau está publicado no PyPI e requer o Python 3.10 ou
posterior:

```bash
uv tool install reviau   # como ferramenta de linha de comando isolada
pip install reviau       # ou com pip, no ambiente atual
```

`uv tool upgrade reviau` atualiza e `uv tool uninstall reviau` desinstala. A
ferramenta também pode ser executada uma única vez, sem instalação permanente,
com `uvx reviau /caminho/dos/segmentos`. Instalado dessa forma, o reviau não
adiciona atalho.

As bibliotecas de áudio (librosa e soundfile) dependem da `libsndfile`, que já
está incluída nos seus wheels para Linux, macOS e Windows.

Para trabalhar no próprio reviau, consulte [Desenvolvimento](development.md).
