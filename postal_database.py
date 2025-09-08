"""
郵便番号データベースの構築と管理

このモジュールは日本郵便の公式CSVデータを使用して
住所→郵便番号の高速検索を可能にするデータベースを構築します。
"""

import sqlite3
import pandas as pd
import requests
import zipfile
import os
from typing import List, Dict, Optional
import streamlit as st


class PostalCodeDatabase:
    """郵便番号データベース管理クラス"""
    
    def __init__(self, db_path: str = "postal_codes.db"):
        self.db_path = db_path
        self.postal_csv_url = "https://www.post.japanpost.jp/zipcode/dl/kogaki/zip/ken_all.zip"
    
    def download_and_setup_database(self):
        """日本郵便データをダウンロードしてデータベースを構築"""
        print("📥 郵便番号データをダウンロード中...")
        
        # CSVファイルのダウンロード
        response = requests.get(self.postal_csv_url)
        
        # ZIPファイルを展開
        with open("ken_all.zip", "wb") as f:
            f.write(response.content)
        
        with zipfile.ZipFile("ken_all.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # CSVファイルを読み込み
        print("📊 データを処理中...")
        df = pd.read_csv(
            "KEN_ALL.CSV", 
            encoding="shift_jis",
            header=None,
            names=[
                "jis_code", "old_postal_code", "postal_code", "prefecture_kana",
                "city_kana", "town_kana", "prefecture", "city", "town",
                "flag1", "flag2", "flag3", "flag4", "flag5", "flag6"
            ]
        )
        
        # データベースの作成
        self.create_database(df)
        
        # 一時ファイルの削除
        os.remove("ken_all.zip")
        os.remove("KEN_ALL.CSV")
        
        print("✅ データベースの構築が完了しました")
    
    def create_database(self, df: pd.DataFrame):
        """SQLiteデータベースを作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # テーブルの作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postal_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                postal_code TEXT NOT NULL,
                prefecture TEXT NOT NULL,
                city TEXT NOT NULL,
                town TEXT,
                prefecture_kana TEXT,
                city_kana TEXT,
                town_kana TEXT,
                full_address TEXT NOT NULL
            )
        """)
        
        # インデックスの作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postal_code ON postal_codes(postal_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_full_address ON postal_codes(full_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prefecture ON postal_codes(prefecture)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON postal_codes(city)")
        
        # データの挿入
        for _, row in df.iterrows():
            postal_code = row['postal_code']
            prefecture = row['prefecture']
            city = row['city']
            town = row['town'] if pd.notna(row['town']) else ''
            full_address = f"{prefecture}{city}{town}"
            
            cursor.execute("""
                INSERT INTO postal_codes 
                (postal_code, prefecture, city, town, prefecture_kana, city_kana, town_kana, full_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                postal_code, prefecture, city, town,
                row['prefecture_kana'], row['city_kana'], row['town_kana'],
                full_address
            ))
        
        conn.commit()
        conn.close()
    
    def search_by_address(self, address: str, limit: int = 10) -> List[Dict]:
        """住所で郵便番号を検索"""
        if not os.path.exists(self.db_path):
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # LIKE検索で部分一致
        cursor.execute("""
            SELECT postal_code, prefecture, city, town, full_address
            FROM postal_codes
            WHERE full_address LIKE ?
            ORDER BY 
                CASE 
                    WHEN full_address = ? THEN 1
                    WHEN full_address LIKE ? THEN 2
                    ELSE 3
                END,
                LENGTH(full_address)
            LIMIT ?
        """, (f"%{address}%", address, f"{address}%", limit))
        
        results = []
        for row in cursor.fetchall():
            postal_code, prefecture, city, town, full_address = row
            formatted_postal = f"{postal_code[:3]}-{postal_code[3:]}"
            
            results.append({
                "postal_code": formatted_postal,
                "prefecture": prefecture,
                "city": city,
                "town": town,
                "full_address": full_address,
                "source": "ローカルDB"
            })
        
        conn.close()
        return results
    
    def get_database_info(self) -> Dict:
        """データベースの情報を取得"""
        if not os.path.exists(self.db_path):
            return {"exists": False}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM postal_codes")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT prefecture) FROM postal_codes")
        prefecture_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "exists": True,
            "total_records": total_count,
            "prefecture_count": prefecture_count,
            "file_size": os.path.getsize(self.db_path)
        }


# Streamlit用のセットアップ関数
def setup_postal_database():
    """Streamlitアプリ用のデータベースセットアップ"""
    db = PostalCodeDatabase()
    
    st.subheader("📊 郵便番号データベースの設定")
    
    db_info = db.get_database_info()
    
    if db_info["exists"]:
        st.success("✅ データベースが利用可能です")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総レコード数", f"{db_info['total_records']:,}")
        with col2:
            st.metric("都道府県数", db_info['prefecture_count'])
        with col3:
            file_size_mb = db_info['file_size'] / (1024 * 1024)
            st.metric("DB サイズ", f"{file_size_mb:.1f} MB")
        
        # データベース更新ボタン
        if st.button("🔄 データベースを更新"):
            with st.spinner("データベースを更新中..."):
                try:
                    db.download_and_setup_database()
                    st.success("データベースの更新が完了しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新中にエラーが発生しました: {e}")
    
    else:
        st.warning("⚠️ データベースが見つかりません")
        st.info("初回セットアップには数分かかります（約20MB のダウンロード）")
        
        if st.button("📥 データベースを構築"):
            with st.spinner("データベースを構築中..."):
                try:
                    db.download_and_setup_database()
                    st.success("データベースの構築が完了しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"構築中にエラーが発生しました: {e}")
    
    return db if db_info["exists"] else None
