@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Para guardar os navegadores fora do C:, defina antes: set PLAYWRIGHT_BROWSERS_PATH=D:\caminho
if not exist ".venv" (
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
  python -m playwright install firefox
) else (
  call .venv\Scripts\activate
)
python extrator_certidoes.py %*
pause
