#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Flaskで書いたサンプルAPIサーバー
"""
import os
from datetime import datetime, timezone

from flask import Flask

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False  # UTF-8をそのまま返す

FLASK_ENV = os.getenv("FLASK_ENV", None)

if FLASK_ENV == "development":
    from flask_cors import CORS

    CORS(app, resources={r"/*": {"origins": "*"}})  # 開発時スペシャル


def get_current_time_with_date_and_timezone():
    """
    Returns the current time with date and timezone.

    Returns:
        str: Current time with date and timezone.
    """
    return str(datetime.now(timezone.utc))


@app.route("/now")
def now():
    """
    Returns the current time with date and timezone as a JSON response.

    Returns:
        dict: JSON response containing the result status and the current time with date and timezone.
    """
    return {"result": "OK", "now": get_current_time_with_date_and_timezone()}


if __name__ == "__main__":
    app.run()
