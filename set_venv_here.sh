#!/bin/sh
# プロジェクトルート(ここ)に.venv環境を作る
cd $(dirname $0)
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
pip install -U -r requirements.txt

echo "Run the commands below:"
echo ". .venv/bin/activate"
