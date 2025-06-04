# rireki-pon
Extract text from previously visited sites based on your Chrome history.

## 動かすための準備

　まず、Pythonの実行環境を用意する必要がある（もちろんすでに用意されている人は飛ばしてください）。Windowsの場合、以下の手順で準備できる。

　1. Pythonのインストール
　 Python公式サイト（https://www.python.org/downloads/）から最新版をダウンロードしてインストール（Anacondaという便利なPythonのパッケージをまとめてインストールできるものもあるので、そちらを使ってもよい）。インストール時に「Add Python to PATH」にチェックを入れるのを忘れずに。

　2. 必要なライブラリのインストール
　コマンドプロンプトを開いて、以下のコマンドを実行する（他も必要に応じてインストールしてください）。

　> pip install selenium

## Chromeの拡張機能をインストール

　次に、Chromeの履歴を取得するための拡張機能をインストールする。

　1. Quick Chrome History Export
　Chrome Web StoreからQuick Chrome History Export（https://chrome.google.com/webstore/detail/quick-chrome-history-export/ocgccfelbchfdfplphnhagkdpicpbmjf）をインストール。この拡張機能は、Chromeの履歴をCSV形式でエクスポートできる。

 2. Cookie Editor（必要な場合）
　自動ログインが必要なサイトがある場合は、Cookie Editor（https://chromewebstore.google.com/detail/cookie-editor/ookdjilphngeeeghgngjabigmpepanpl?utm_source=ext_app_menu）をインストール。この拡張機能は、cookie情報をjson形式でエクスポートできる。

## 事前のコードの設定と書き換え

　１. 書き出しファイル名などの設定
　　コードの中の「==== 設定 ====」の部分に、実行結果を保存するファイル名（output_results.txt）は、実行ずみのURLを入れておくファイル（processed_urls.txt）などがあるので適切に書き換えてほしい。

　2. 開く必要のないサイトを設定
　　「除外するドメインリスト」には、Chromeの履歴にはあってもテキスト化したくないドメインを入れておく。私は、Google.comやSlack.comなどを指定している。

　3. 自動ログインのためのCookie情報設定
　　自動ログインが必要なサイトがある場合は、Cookie Editorでcookie情報をjson形式で書き出し、それをコードから読み込めばよい。ここは、コードの中の「==== 設定 ====」の部分と「Cookie設定とログイン確認」の部分で設定する。

## 使い方の手順

　1. Chromeの履歴をエクスポート
　Quick Chrome History Exportを開き、遡りたい期間を選択。形式はCSVを選び、ダウンロードする。

　2. コードの準備
　ダウンロードしたCSVファイルを、コード内のURL_LIST_CSVに設定する。

　3. 実行
　コマンドプロンプトで以下のコマンドを実行する。

　> python AccessChromeHistory.py

  4. ヘッドレスでの実行。
    HEADLESSにWebを自動的に開きながら（False）、Webは開かず（True）。

