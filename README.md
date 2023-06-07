# Flask+uWSGI+NginxでAPIをちゃんと配置する話

OpenAIのせいで「Flask + uWSGI + Nginx で API を書こう」みたいな要件が出てきました (主にAPI KEY 隠しと embedding のせい)。

ここでは

- Ubuntu 22.04 LTS でサーバ立てて
- ホスト起動時に uWSGI が上がって
- フロントは Nginx
- Python や uWSGI はディストリ版を使う (Python:3.10.6, uWSGI:2.0.20)
- モジュール類は [venv](https://docs.python.org/ja/3.10/library/venv.html) で
- エンドポイントは
  - 開発時は <http://127.0.0.1:5000/> (Flaskのデフォルト)
  - デプロイ時は <https://ホスト名/api/v1/>
- デプロイ時のディレクトリ(プロジェクトディレクトリ)は `/opt/myapi` とする

という、多分にポピュラーな構成で API を立ててみたいと思います。

## サンプルで立てるAPI概要

サンプルで立てるAPI概要は以下のようなものです:

Flask の app.py (抜粋)

```python
def get_current_time_with_date_and_timezone():
    return str(datetime.now(timezone.utc))

@app.route("/now")
def now():
    return {"result": "OK", "now": get_current_time_with_date_and_timezone()}
```

これに対して

```bash
curl http://127.0.0.1:5000/now
```

と呼ぶと

```json
{"now":"2023-06-07 04:15:26.067860+00:00","result":"OK"}
```

のようなJSONが帰ってきます。

## デプロイ先のホストを作る

FQDNでアクセスできるUbuntu 22.04 LTSのホストを用意します。
Azureだと動的IPでもVMに簡単にFQDNがふれるのでオススメです(しかもFQDN代はタダです)。

以下のようなコマンドを実行して、ホストを設定します。

```bash
# PythonとPython開発系入れる
sudo apt install build-essential python3-dev python3-venv python3-pip -y

# nginxとuWSGI入れる
sudo apt install nginx-full uwsgi uwsgi-dev uwsgi-plugin-python3 -y
# ここで http://ホストのFQDN/ でNginxの初期ページが見えることを確認

# certbotでTSL化
snap refresh
snap install --classic certbot
ln -s /snap/bin/certbot /usr/bin/certbot
certbot --nginx
## あなたのメールアドレスを入力
## yを入力
## yを入力
## ホストのFQDNを入力
# ここで SSL Labs <https://www.ssllabs.com/ssltest/> でテストする。

# カレントユーザをwww-dataグループに追加する
sudo usermod -aG www-data "$USER"

# プロジェクトディレクトリ作る
sudo install -m 2750 -o "$USER" -g www-data -d /opt/myapi
# HOMEにリンク作っておく (オプション)
ln -s /opt/myapi ~/
```

あとは
`/opt/myapi` にこのサンプルプロジェクトを置いてください
(いま読んでるこのファイルが `/opt/myapi/README.md` になるように配置してください)。

## 仮想環境(venv)を作る

まず開発でもデプロイでも
プロジェクトディレクトリの .venv/ 以下に Pythonの仮想環境を作ります。

プロジェクトディレクトリで以下のスクリプトを実行してください。

```bash
# デプロイ先でLinuxでbashの場合
./set_venv_here.sh
# または Windowsで開発していて、PowerShellの場合
.\set_venv_here.ps1
````

スクリプトが何をしているかをざっくり箇条書きにすると

- .venv/ 以下に仮想環境を作る
- 仮想環境に入る
- 仮想環境のpipモジュールだけ最新にしておく
- requirements.txt に書かれたモジュールを仮想環境にインストールする

となります。

## uWSGIに登録 & 起動する

詳しいコメントが、このプロジェクトの `wsgi.ini` に書かれているので、参照してください。キモは:

- moduleのところ
- logtoとsocket, pidを書かないところ

だと思います。

appの登録は
Debian, Ubuntu 特有の xxx-available/xxx-enabled 式になってます。
Nginx や Apache でおなじみの方式ですね。

```bash
sudo ln -s /opt/myapi/wsgi.ini /etc/uwsgi/apps-available/myapi.ini
sudo ln -s /etc/uwsgi/apps-available/myapi.ini /etc/uwsgi/apps-enabled/
```

つづいて uWSGIサーバを再起動します。

```bash
sudo systemctl restart uwsgi
```

ログは
`/var/log/uwsgi/app/{app名}.log`
に出力されます(logrotateもする) ので確認してください。
`/etc/uwsgi/apps-enabled/` の .iniの名前部分がapp名になります。

そしてUNIXソケットとPIDファイルは
`/var/run/uwsgi/app/{app名}/` に生成されます。
これらは次のステップで使用します。

他、uWSGI全体の設定は
`/usr/share/uwsgi/conf/default.ini`
です。チューニングが必要な場合は参考にしてください。

## フロントにNginxを置く

- certbotの設定
- /opt/myapiへの配置
- uWSGIに登録 & 起動後

が完了したら

`/etc/nginx/sites-available/default` の

```config
server {
 # SSL configuration
 ...
}
```

のセクションに

```config
  location ~ ^/api/v1/(.*)$ {
    include uwsgi_params;
    uwsgi_param SCRIPT_NAME /api/v1;
    uwsgi_param PATH_INFO /$1;
    uwsgi_pass unix:///run/uwsgi/app/myapi/socket;
  }
```

を書き、nginxを再起動しましょう。

参考: [nginx + uwsgi でアプリケーションをサブディレクトリで動かす設定 - Qiita](https://qiita.com/methane/items/e0949a37c112eedf2b74)

```bash
# まずシンタックスチェックをしてから...
sudo nginx -t
# Nginx再起動 
sudo systemctl restart nginx
```

これで `curl https://ホストのFQDN名/api/v1/now` で JSONが帰ってくれば作業完了です。

## その他

これだけ書いておいてなんですけど、
いまだったら Flask よりは FastAPI のほうがいいと思います。
