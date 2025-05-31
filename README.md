# rireki-pon
Extract text from previously visited sites based on your Chrome history.

## 使い方

1. Chromeの履歴を取得してURLリストとする。
    Chromeの拡張機能「Quick Chrome History Export」を使用するとよい。
    遡る期間と形式（CSV）を指定して書き出した結果をURL_LIST_CSVに設定。
2. Pythonの実行環境をあらかじめ用意してください。
    またコードを参照して必要なライブラリをインストールしてください。
3. 以下のようにして実行。
    > python AccessChromeHistory.py
4. ヘッドレスでの実行。
    HEADLESSにWebを自動的に開きながら（False）、Webは開かず（True）。
5. 自動ログインしたいサイトがある場合はcookie情報を与える。
    Chromeの拡張機能の「Cookie Editor」でjsonで書き出しておき、
    コードを参照に適切に書き換えて実行。

