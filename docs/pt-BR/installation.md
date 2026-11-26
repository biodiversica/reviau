# Instalação

*[English](../en/installation.md) · Português (Brasil)*

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

Para trabalhar no próprio reviau, consulte [Desenvolvimento](development.md).
