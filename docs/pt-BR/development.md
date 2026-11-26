# Desenvolvimento

*[English](../en/development.md) · Português (Brasil)*

```bash
git clone https://github.com/biodiversica/reviau
cd reviau
uv sync               # instala o projeto e as ferramentas de desenvolvimento
uv run ruff check .   # lint
uv run pytest         # testes
uv run reviau /caminho/dos/segmentos
```

## Testes e Integração Contínua

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

## Documentação

A documentação fica em [`docs/`](../README.md), com uma página por assunto em
inglês e em português, sob o mesmo nome de arquivo. Uma alteração num idioma
deve ser feita no outro no mesmo commit.
