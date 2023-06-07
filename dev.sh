#!/bin/sh
# 開発用にFlaskでapp.pyを立ち上げる。ホットリロードする
# venv環境に入ってること前提
cd $(dirname $0)
FLASK_ENV="development"
FLASK_APP="app.py:app"  # デフォルト値で本来不要だが説明用
flask run --debugger --reload
