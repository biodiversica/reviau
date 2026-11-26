# Execução num Servidor

*[English](../en/server.md) · Português (Brasil)*

A interface é uma página web comum; assim, a ferramenta pode ser executada na
máquina que armazena o áudio e utilizada a partir de qualquer outra:

```bash
reviau /dados/segmentos --host 0.0.0.0 --port 8765 --no-open
```

Com `--host 0.0.0.0`, o comando exibe também o endereço que as outras máquinas
devem utilizar.

## Token de Acesso

Quando um endereço diferente do loopback é utilizado, um **token de acesso** é
gerado e incluído no endereço exibido; após a abertura desse endereço, o token é
armazenado num cookie. `--token meusegredo` define o token explicitamente, e
`--no-auth` disponibiliza a interface sem token.

O token impede o acesso casual, mas não oferece criptografia (TLS). Quem o
possuir pode abrir e revisar (e, portanto, mover clipes de) qualquer pasta que o
revisor consiga ler, além de listar os nomes das pastas daquela máquina. O token
deve, portanto, ser tratado como uma senha, e o uso de `--no-auth` deve ser
evitado em redes compartilhadas.

## Redes Não Confiáveis

Em redes não confiáveis, recomenda-se o Tailscale (vinculando ao endereço do
Tailscale, ou a `0.0.0.0` numa máquina acessível apenas pela tailnet) ou um
túnel SSH:

```bash
# no servidor
reviau /dados/segmentos --port 8765 --no-open
# no computador local
ssh -N -L 8765:127.0.0.1:8765 usuario@servidor   # em seguida, abrir http://127.0.0.1:8765
```

## Um Revisor por Vez

A ferramenta atende a um revisor por vez. A lista de pendentes, a posição atual e
a pasta aberta são mantidas pelo servidor; assim, dois navegadores conectados à
mesma instância controlam a mesma sessão, e uma pasta aberta num deles é aberta
em ambos.
