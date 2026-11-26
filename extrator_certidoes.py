"""Abre os portais das certidões de regularidade de um CNPJ, preenche o que
dá para preencher e organiza os PDFs que forem salvos em cada etapa."""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

PASTA_SAIDA = Path("certidoes")
PASTA_PERFIL = Path("perfil_navegador")


def so_numeros(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def cnpj_valido(cnpj: str) -> bool:
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def digito(base: str, pesos: list[int]) -> str:
        resto = sum(int(n) * p for n, p in zip(base, pesos)) % 11
        return "0" if resto < 2 else str(11 - resto)

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = digito(cnpj[:12], pesos1)
    d2 = digito(cnpj[:12] + d1, [6] + pesos1)
    return cnpj[12:] == d1 + d2


def fgts(pagina, cnpj):
    pagina.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf")
    pagina.locator("select[id='mainForm:tipoEstabelecimento']").select_option("1")
    pagina.fill("input[id='mainForm:txtInscricao1']", cnpj)
    pagina.click("input[id='mainForm:btnConsultar']")
    return "Gere o PDF do CRF e salve."


def trabalhista(pagina, cnpj):
    pagina.goto("https://cndt-certidao.tst.jus.br/inicio.faces")
    pagina.click("input[value='Emitir Certidão']")
    return f"Digite o CNPJ {cnpj}, resolva o captcha e salve o PDF."


def cartao_cnpj(pagina, cnpj):
    pagina.goto("https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/cnpjreva_solicitacao.asp")
    pagina.wait_for_selector("input.form-control")
    pagina.fill("input.form-control", cnpj)
    return "Resolva o captcha, consulte e salve o PDF."


def federal(pagina, cnpj):
    pagina.goto("https://servicos.receitafederal.gov.br/servico/certidoes/#/home")
    pagina.wait_for_selector("a[href='#/home/cnpj']")
    pagina.click("a[href='#/home/cnpj']")
    return f"Preencha o CNPJ {cnpj}, emita a certidão e salve o PDF."


ETAPAS = [
    ("fgts", "CRF do FGTS (Caixa)", fgts),
    ("trabalhista", "CNDT (TST)", trabalhista),
    ("cartao-cnpj", "Cartão CNPJ (Receita)", cartao_cnpj),
    ("federal", "CND Federal (Receita/PGFN)", federal),
]


def pdfs_em(pasta: Path) -> set[Path]:
    return set(pasta.glob("*.pdf"))


def renomear_novos(antes: set[Path], pasta: Path, cnpj: str, sufixo: str) -> list[Path]:
    novos = sorted(pdfs_em(pasta) - antes, key=lambda p: p.stat().st_mtime)
    renomeados = []
    for i, arquivo in enumerate(novos, start=1):
        extra = f"-{i}" if len(novos) > 1 else ""
        destino = pasta / f"{cnpj}_{sufixo}{extra}_{date.today():%Y-%m-%d}.pdf"
        arquivo.replace(destino)
        renomeados.append(destino)
    return renomeados


def executar(cnpj: str, escolhidas: list[str]):
    pasta = (PASTA_SAIDA / cnpj).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    print(f"CNPJ {cnpj} | PDFs em: {pasta}\n")

    resumo = []
    with sync_playwright() as p:
        # Perfil persistente: os portais lembram cookies e o download cai direto na pasta.
        contexto = p.firefox.launch_persistent_context(
            user_data_dir=str(PASTA_PERFIL.resolve()),
            headless=False,
            downloads_path=str(pasta),
            accept_downloads=True,
        )
        pagina = contexto.pages[0]
        etapas = [e for e in ETAPAS if e[0] in escolhidas]
        try:
            for n, (sufixo, nome, abrir) in enumerate(etapas, start=1):
                print(f"[{n}/{len(etapas)}] {nome}")
                antes = pdfs_em(pasta)
                try:
                    instrucao = abrir(pagina, cnpj)
                except Exception as erro:
                    # Portal fora do ar ou com layout novo: segue para a próxima em vez de abortar tudo.
                    print(f"   não consegui abrir automaticamente ({erro.__class__.__name__}). Faça manualmente.")
                    instrucao = "Conclua no navegador e salve o PDF."
                print(f"   {instrucao} Depois clique em 'Resume' no inspetor.")
                pagina.pause()
                salvos = renomear_novos(antes, pasta, cnpj, sufixo)
                resumo.append((nome, salvos))
        finally:
            contexto.close()

    print("\nResumo")
    for nome, salvos in resumo:
        status = ", ".join(s.name for s in salvos) if salvos else "nenhum PDF salvo na pasta"
        print(f" - {nome}: {status}")


def main():
    parser = argparse.ArgumentParser(description="Assistente para emitir certidões de regularidade de um CNPJ.")
    parser.add_argument("cnpj", nargs="?", help="CNPJ, com ou sem pontuação")
    parser.add_argument(
        "--so",
        nargs="+",
        choices=[e[0] for e in ETAPAS],
        default=[e[0] for e in ETAPAS],
        help="emitir só algumas certidões",
    )
    args = parser.parse_args()

    cnpj = so_numeros(args.cnpj or input("CNPJ: "))
    if not cnpj_valido(cnpj):
        sys.exit(f"CNPJ inválido: {cnpj}")

    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        print(f"Navegadores do Playwright em: {os.environ['PLAYWRIGHT_BROWSERS_PATH']}")

    executar(cnpj, args.so)


if __name__ == "__main__":
    main()
