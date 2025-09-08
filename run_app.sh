#!/bin/bash

# 郵便番号検索アプリの起動スクリプト

echo "🚀 郵便番号検索アプリを起動します..."

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境の有効化
echo "🔧 仮想環境を有効化しています..."
source venv/bin/activate

# 依存関係のインストール
echo "📥 必要なパッケージをインストールしています..."
pip install -r requirements.txt

# Streamlitアプリの起動
echo "🌐 ブラウザでアプリが開きます..."
echo "終了するには Ctrl+C を押してください"
streamlit run app.py
