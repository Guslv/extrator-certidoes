# Extrator de certidões

Em toda contratação pública é preciso juntar as certidões de regularidade do fornecedor: FGTS, débitos trabalhistas, cartão CNPJ e débitos federais. São quatro portais diferentes, cada um com seu formulário e quase sempre um captcha no meio.

Este script abre os quatro portais em sequência num Firefox controlado pelo Playwright, já com o CNPJ preenchido onde o site permite. Quando aparece um captcha, ele pausa e espera você terminar. Ao final, os PDFs ficam numa pasta por CNPJ, com nome padronizado:

```
certidoes/11222333000181/
├── 11222333000181_fgts_2026-11-26.pdf
├── 11222333000181_trabalhista_2026-11-26.pdf
├── 11222333000181_cartao-cnpj_2026-11-26.pdf
└── 11222333000181_federal_2026-11-26.pdf
```

Ele é assistido de propósito. Os captchas existem para impedir emissão automática, e a ideia aqui é cortar o trabalho repetitivo (abrir, navegar, digitar, renomear), não contornar essa proteção.

## Como usar

No Windows, o `executar.bat` cria o ambiente na primeira vez e depois só roda:

```
executar.bat 11.222.333/0001-81
```

Em outros sistemas:

```
pip install -r requirements.txt
python -m playwright install firefox
python extrator_certidoes.py 11.222.333/0001-81
```

Para emitir só algumas: `python extrator_certidoes.py 11222333000181 --so fgts federal`

Em cada etapa o terminal diz o que falta fazer no navegador. Depois de salvar o PDF, clique em **Resume** no inspetor do Playwright para seguir para a próxima. No fim aparece um resumo do que foi salvo.

## Detalhes

- O CNPJ é validado pelos dígitos verificadores antes de abrir qualquer site.
- Se um portal estiver fora do ar ou mudar o layout, o script avisa e segue para o próximo em vez de parar tudo.
- O perfil do navegador fica em `perfil_navegador/`, então os portais lembram os cookies de uma execução para a outra.
- Para guardar os navegadores do Playwright em outro disco, defina `PLAYWRIGHT_BROWSERS_PATH` antes de rodar.

Os seletores de cada site ficam numa função própria (`fgts`, `trabalhista`, `cartao_cnpj`, `federal`). Quando um portal muda, é só ajustar ali.
