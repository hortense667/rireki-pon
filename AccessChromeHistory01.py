#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) 2025 Satoshi Endo
#
#1）Chromeの履歴を取得してURLリストとする。
#    Chromeの拡張機能「Quick Chrome History Export」を使用するとよい。
#   遡る期間と形式（CSV）を指定して書き出した結果をURL_LIST_CSVに設定。
#2）Pythonの実行環境をあらかじめ用意してください。
#    またコードを参照して必要なライブラリをインストールしてください。
#3）以下のようにして実行。
#    > python AccessChromeHistory01.py {URL_LIST_CSVで指定したファイル名}
#4）ヘッドレスでの実行。
#    HEADLESSにWebを自動的に開きながら（False）、Webは開かず（True）。
#5）自動ログインしたいサイトがある場合はcookie情報を与える。
#    Chromeの拡張機能の「Cookie Editor」でjsonで書き出しておき、
#    以下コードを参照に適切に書き換えて実行。
#
import os
import json
import csv
import time
import re
import socket
from urllib.parse import urlparse
import tldextract

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

# ==== 設定 ====
PROFILE_DIR           = os.path.expanduser('~/selenium_profile3')
FACEBOOK_COOKIES_FILE = 'facebook.json'
TWITTER_COOKIES_FILE  = 'x.json'
MITTR_COOKIES_FILE  = 'mittr.json'
WIRED_COOKIES_FILE  = 'wired.json'
URL_LIST_CSV          = 'history_20250529_ienoHP.csv'
PROCESSED_URLS_FILE   = 'processed_urls4.txt'
OUTPUT_TXT            = 'output_results4.txt'
HEADLESS             = False
# タイムアウト設定（秒）
PAGE_LOAD_TIMEOUT    = 30
WAIT_TIMEOUT         = 10
# 除外するドメインリスト（正規化されたドメイン名のみを列挙）
excluded_domains = ['google.com', 'workspace.google.com','googleadservices.com', 'youtube.com', 'amazon.com', 'dropbox.com', 'yodobashi.com', 'merukari.com', 'rakuten.co.jp', 'slack.com', 'chatwork.com', 'ebay.com', 'ndl.go.jp', 'chatgpt.com', 'perplexity.ai', 'claude.ai']
# ==================

def setup_driver():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # ページ読み込みタイムアウトを30秒に設定
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    return driver

def load_cookies(driver, cookie_file, domain_url):
    if not os.path.exists(cookie_file):
        print(f"[WARN] Cookie ファイルが見つかりません: {cookie_file}")
        return False
    
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
    except Exception as e:
        print(f"[ERROR] Cookie ファイル読み込みエラー {cookie_file}: {e}")
        return False
    
    print(f"[INFO] Cookie設定開始: {domain_url} ({len(cookies)}個)")
    
    try:
        driver.get(domain_url)
        time.sleep(2)  # ページ読み込み待機
    except TimeoutException:
        print(f"[WARN] Cookie設定用ページの読み込みがタイムアウト: {domain_url}")
        # タイムアウトしてもCookie設定は続行
    
    success_count = 0
    for c in cookies:
        try:
            # Cookieの必要な情報を保持しつつ、問題のあるフィールドを調整
            cookie_dict = {
                'name': c.get('name'),
                'value': c.get('value'),
                'path': c.get('path', '/'),
            }
            
            # domainの処理を改善
            if 'domain' in c and c['domain']:
                # .facebook.com -> facebook.com に正規化
                domain = c['domain'].lstrip('.')
                cookie_dict['domain'] = domain
            
            # 有効期限があれば設定（但し、セッションCookieは除く）
            if 'expirationDate' in c:
                cookie_dict['expiry'] = int(c['expirationDate'])
            
            # secure フラグの設定
            if c.get('secure', False):
                cookie_dict['secure'] = True
                
            # httpOnly フラグの設定  
            if c.get('httpOnly', False):
                cookie_dict['httpOnly'] = True
            
            driver.add_cookie(cookie_dict)
            success_count += 1
            
        except Exception as e:
            print(f"[WARN] Cookie追加失敗 '{c.get('name')}': {e}")
            continue
    
    print(f"[INFO] Cookie設定完了: {success_count}/{len(cookies)}個成功")
    
    try:
        driver.refresh()
        time.sleep(3)  # リフレッシュ後の待機時間を延長
    except TimeoutException:
        print(f"[WARN] Cookie設定後のページ更新がタイムアウト: {domain_url}")
    
    return success_count > 0

def check_facebook_login(driver):
    """Facebookのログイン状態を確認"""
    try:
        # ログイン状態の確認要素を複数パターンで試す
        login_indicators = [
            "//div[@aria-label='アカウント']",  # プロフィールメニュー
            "//div[@data-click='profile_icon']",  # プロフィールアイコン
            "//a[contains(@href, '/me/')]",  # 自分のプロフィールリンク
            "//*[contains(text(), 'ホーム')]",  # ホームリンク（日本語）
            "//*[contains(text(), 'Home')]"  # ホームリンク（英語）
        ]
        
        for indicator in login_indicators:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, indicator))
                )
                if element:
                    print("[SUCCESS] Facebook ログイン確認済み")
                    return True
            except TimeoutException:
                continue
        
        # ログインフォームが表示されているかチェック
        try:
            login_form = driver.find_element(By.ID, "email")
            if login_form:
                print("[WARN] Facebook ログインフォームが表示されています - ログインが必要")
                return False
        except:
            pass
            
        print("[WARN] Facebook ログイン状態を確認できませんでした")
        return False
        
    except Exception as e:
        print(f"[ERROR] Facebook ログイン確認エラー: {e}")
        return False

def check_twitter_login(driver):
    """X(Twitter)のログイン状態を確認"""
    try:
        login_indicators = [
            "//div[@data-testid='SideNav_AccountSwitcher_Button']",  # アカウント切り替えボタン
            "//a[@data-testid='AppTabBar_Home_Link']",  # ホームリンク
            "//div[@data-testid='primaryColumn']"  # メインカラム
        ]
        
        for indicator in login_indicators:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, indicator))
                )
                if element:
                    print("[SUCCESS] X(Twitter) ログイン確認済み")
                    return True
            except TimeoutException:
                continue
                
        print("[WARN] X(Twitter) ログイン状態を確認できませんでした")
        return False
        
    except Exception as e:
        print(f"[ERROR] X(Twitter) ログイン確認エラー: {e}")
        return False

# 正規化されたドメインを抽出する関数
def get_domain(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"

def read_url_list(csv_file, excluded_domains):
    urls = []
    with open(csv_file, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url','').strip()
            domain = get_domain(url)  # 正規化されたドメインを取得
            if domain in excluded_domains: continue
            if not url: continue
            dt = f"{row.get('date','').strip()} {row.get('time','').strip()}"
            urls.append((url, dt))
    print(f"読み込んだ URL 件数: {len(urls)}")
    for i,(u,d) in enumerate(urls[:5],1):
        print(f"#{i}: {u} / {d}")
    print(" …")
    return urls

def read_processed(file_path):
    if not os.path.exists(file_path): return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_processed(file_path, url):
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

def write_output(txt_file, url, date, text):
    with open(txt_file, 'a', newline='', encoding='utf-8') as file:
        file.write(f"URL: {url}\n")
        file.write(f"Access Date: {date}\n")  # アクセス日付を追加
        file.write(f"{text}\n")
        file.write("\n" + "="*80 + "\n")

def is_reachable(url):
    """DNS 解決できなければスキップ"""
    try:
        h = urlparse(url).hostname
        if not h: return False
        socket.getaddrinfo(h, None, 0, socket.SOCK_STREAM)
        return True
    except Exception:
        return False

def get_text_selenium(driver, url):
    # フォーマットチェック
    if not re.match(r'^https?://', url):
        print(f"[SKIP] フォーマット不正: {url}")
        return ''
    if not is_reachable(url):
        print(f"[SKIP] DNS 解決失敗: {url}")
        return ''

    total_start_time = time.time()
    
    try:
        print(f"[INFO] ページ読み込み開始 (最大{PAGE_LOAD_TIMEOUT}秒): {url}")
        start_time = time.time()
        
        # ページ読み込み（30秒タイムアウト）
        driver.get(url)
        
        load_time = time.time() - start_time
        print(f"[INFO] ページ読み込み完了 ({load_time:.1f}秒): {url}")
        
        # 投稿本文が入る <article> がレンダリングされるまで最大 5 秒待つ（短縮）
        print(f"[INFO] article要素検出中...")
        try:
            WebDriverWait(driver, 5).until(
               EC.presence_of_element_located((By.TAG_NAME, 'article'))
            )
            print(f"[INFO] article要素検出完了")
        except TimeoutException:
            # 万一タイムアウトしても body だけは返す
            print(f"[WARN] article要素の検出タイムアウト (5秒): {url}")
            pass
        
        # 無限スクロール対応：一度ページ最下部までスクロール（タイムアウト付き）
        print(f"[INFO] スクロール処理中...")
        try:
            # JavaScript実行にもタイムアウトを設ける
            driver.set_script_timeout(5)  # スクリプト実行タイムアウト5秒
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # 待機時間を短縮（2秒→1秒）
            print(f"[INFO] スクロール処理完了")
        except Exception as e:
            print(f"[WARN] スクロール処理エラー: {url} → {e}")
        
        # テキスト取得（タイムアウト付き）
        print(f"[INFO] テキスト取得中...")
        try:
            # テキスト取得にもタイムアウトを設ける
            driver.set_script_timeout(10)  # テキスト取得用スクリプトタイムアウト
            text = driver.find_element(By.TAG_NAME, 'body').text
            
            total_time = time.time() - total_start_time
            print(f"[SUCCESS] テキスト取得完了 ({len(text)}文字, 総時間{total_time:.1f}秒): {url}")
            return text
        except Exception as e:
            print(f"[ERROR] テキスト取得エラー: {url} → {e}")
            return ''
            
    except TimeoutException:
        elapsed = time.time() - total_start_time
        print(f"[TIMEOUT] ページ読み込みタイムアウト ({elapsed:.1f}秒): {url}")
        # タイムアウト時でも現在のページからテキストを取得を試みる
        try:
            print(f"[INFO] タイムアウト後の緊急テキスト取得試行...")
            text = driver.find_element(By.TAG_NAME, 'body').text
            if text:
                print(f"[PARTIAL] タイムアウト後に部分的なテキスト取得 ({len(text)}文字): {url}")
                return text
        except Exception:
            pass
        return ''
    except WebDriverException as e:
        elapsed = time.time() - total_start_time
        print(f"[WARN] WebDriver エラー ({elapsed:.1f}秒経過): {url} → {e.msg if hasattr(e,'msg') else e}")
        return ''
    except Exception as e:
        elapsed = time.time() - total_start_time
        print(f"[ERROR] 想定外エラー ({elapsed:.1f}秒経過): {url} → {e}")
        return ''
    finally:
        # 処理が長時間かかっている場合の強制終了チェック
        total_elapsed = time.time() - total_start_time
        if total_elapsed > PAGE_LOAD_TIMEOUT + 10:  # ページ読み込みタイムアウト + 10秒
            print(f"[FORCE_STOP] 処理時間が長すぎるため強制終了 ({total_elapsed:.1f}秒): {url}")
            try:
                # 新しいページを読み込んで現在の処理をリセット
                driver.get("about:blank")
                time.sleep(1)
            except:
                pass

def main():
    driver = setup_driver()
    
    # Cookie設定とログイン確認
    print("\n=== Cookie設定とログイン確認 ===")
    
    # Facebook
    if load_cookies(driver, FACEBOOK_COOKIES_FILE, 'https://www.facebook.com'):
        check_facebook_login(driver)
    
    # X(Twitter) 
    if load_cookies(driver, TWITTER_COOKIES_FILE, 'https://x.com'):
        check_twitter_login(driver)
    
    # その他のサイト
    load_cookies(driver, MITTR_COOKIES_FILE, 'https://www.technologyreview.jp')
    load_cookies(driver, WIRED_COOKIES_FILE, 'https://wired.jp')
    
    print("=== Cookie設定完了 ===\n")

    url_list = read_url_list(URL_LIST_CSV, excluded_domains)
    processed = read_processed(PROCESSED_URLS_FILE)

    total = len(url_list)
    for idx, (url, date) in enumerate(url_list, start=1):
        print(f"[INFO] {idx}/{total} → {url}")
        if url in processed:
            print(f"[SKIP] 処理済み: {url}")
            continue
        
        # 各URL処理に制限時間を設ける
        url_start_time = time.time()
        MAX_URL_PROCESS_TIME = 60  # 1つのURLあたり最大60秒
        
        try:
            text = get_text_selenium(driver, url)
            if text:
                write_output(OUTPUT_TXT, url, date, text)
                save_processed(PROCESSED_URLS_FILE, url)
                processed.add(url)
        except Exception as e:
            print(f"[ERROR] URL処理中にエラー: {url} → {e}")
        
        # 処理時間チェック
        url_elapsed = time.time() - url_start_time
        if url_elapsed > MAX_URL_PROCESS_TIME:
            print(f"[WARN] URL処理時間が制限を超過 ({url_elapsed:.1f}秒): {url}")
            # ドライバーをリセット
            try:
                driver.get("about:blank")
                time.sleep(1)
            except:
                pass
        
        time.sleep(1)

    driver.quit()

if __name__ == '__main__':
    main()
    
