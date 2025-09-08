"""
設定管理モジュール

データソースの選択や設定を管理します。
"""

import streamlit as st

# オプショナルインポート（デプロイ時には使用されない）
try:
    from postal_database import setup_postal_database
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False


def show_settings_page():
    """設定ページの表示"""
    st.title("⚙️ アプリケーション設定")
    
    st.markdown("---")
    
    # データソース設定
    st.subheader("🔍 住所検索のデータソース")
    
    data_source = st.radio(
        "住所から郵便番号を検索する際のデータソースを選択してください:",
        [
            "サンプルデータ（軽量、主要地域のみ）",
            "HeartRails API（無料、全国対応、要インターネット）",
            "ローカルデータベース（高速、全国対応、要セットアップ）"
        ],
        key="data_source_selection"
    )
    
    # 選択されたデータソースに応じた説明と設定
    if data_source.startswith("サンプルデータ"):
        st.info("""
        **サンプルデータモード**
        - 軽量で高速
        - 東京都、大阪府、神奈川県の主要地域のみ対応
        - オフラインで動作
        - 初期設定で利用可能
        """)
        
        st.session_state.search_mode = "sample"
    
    elif data_source.startswith("HeartRails API"):
        st.info("""
        **HeartRails API モード**
        - 無料で利用可能
        - 全国の住所に対応
        - インターネット接続が必要
        - API制限あり（過度な利用は控えめに）
        """)
        
        st.warning("⚠️ 外部APIを使用するため、応答速度はネットワーク状況に依存します。")
        
        # API設定
        with st.expander("🔧 API設定"):
            timeout = st.slider("タイムアウト時間（秒）", 5, 30, 10)
            st.session_state.api_timeout = timeout
            
            if st.button("🧪 API接続テスト"):
                test_api_connection()
        
        st.session_state.search_mode = "api"
    
    elif data_source.startswith("ローカルデータベース"):
        st.info("""
        **ローカルデータベースモード**
        - 日本郵便の公式データを使用
        - 全国の住所に完全対応
        - 高速検索
        - オフラインで動作
        - 初回セットアップが必要（約20MB）
        """)
        
        # データベースセットアップ（利用可能な場合のみ）
        if HAS_DATABASE:
            db = setup_postal_database()
            
            if db:
                st.session_state.search_mode = "database"
                st.session_state.postal_db = db
            else:
                st.session_state.search_mode = "sample"
                st.warning("データベースが利用できないため、サンプルデータモードに戻ります。")
        else:
            st.warning("データベース機能は利用できません（pandas未インストール）。")
            st.session_state.search_mode = "api"
    
    st.markdown("---")
    
    # その他の設定
    st.subheader("🎨 表示設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_results = st.slider("最大表示件数", 5, 20, 10)
        st.session_state.max_results = max_results
    
    with col2:
        show_match_score = st.checkbox("マッチ度を表示", value=True)
        st.session_state.show_match_score = show_match_score
    
    # キャッシュ設定
    st.subheader("💾 キャッシュ設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 検索キャッシュをクリア"):
            st.cache_data.clear()
            st.success("キャッシュをクリアしました")
    
    with col2:
        cache_info = st.empty()
        cache_info.info("キャッシュにより検索結果が高速化されます")


def test_api_connection():
    """API接続テスト"""
    try:
        import requests
        response = requests.get("https://geoapi.heartrails.com/api/json?method=searchByGeoLocation&area=東京都千代田区", timeout=10)
        if response.status_code == 200:
            st.success("✅ API接続に成功しました")
        else:
            st.error(f"❌ API接続に失敗しました (ステータス: {response.status_code})")
    except Exception as e:
        st.error(f"❌ API接続エラー: {e}")


def get_search_mode():
    """現在の検索モードを取得"""
    return st.session_state.get("search_mode", "sample")


def show_data_source_info():
    """現在のデータソース情報を表示"""
    mode = get_search_mode()
    
    if mode == "sample":
        st.sidebar.info("📊 データソース: サンプルデータ")
    elif mode == "api":
        st.sidebar.info("🌐 データソース: HeartRails API")
    elif mode == "database":
        st.sidebar.success("🗄️ データソース: ローカルDB")
    
    st.sidebar.markdown("設定を変更するには、サイドバーの⚙️設定ページへ")
