# プロジェクトルート(ここ)に.venv環境を作る
Set-Location $PSScriptRoot
python -m venv .venv
.\.venv\Scripts\activate.ps1
python -m pip install -U pip
pip install -U -r requirements.txt
