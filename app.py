import streamlit as st
import re
import sys
import os

# パスの追加（Streamlit Cloud対応）
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from postal_data import PostalCodeService
    from settings import show_settings_page, get_search_mode, show_data_source_info
except ImportError as e:
    st.error(f"モジュールのインポートエラー: {e}")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="郵便番号検索アプリ",
    page_icon="📮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 30px;
    }
    .postal-input {
        font-size: 18px;
        text-align: center;
    }
    .address-result {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 20px 0;
    }
    .error-message {
        background-color: #ffe4e1;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff6b6b;
        margin: 20px 0;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0 0;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # サイドバーでページ選択
    st.sidebar.title("📮 郵便番号アプリ")
    page = st.sidebar.selectbox(
        "ページを選択:",
        ["🏠 検索", "⚙️ 設定", "📖 使い方"]
    )
    
    # 現在のデータソース情報を表示
    show_data_source_info()
    
    if page == "🏠 検索":
        show_search_page()
    elif page == "⚙️ 設定":
        show_settings_page()
    elif page == "📖 使い方":
        show_help_page()

def show_search_page():
    """検索ページの表示"""
    # ヘッダー
    st.markdown('<h1 class="main-header">📮 郵便番号・住所検索アプリ</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">郵便番号⇄住所の相互検索ができます</p>', unsafe_allow_html=True)
    
    # サービスのインスタンス化
    postal_service = PostalCodeService()
    
    # タブの作成
    tab1, tab2 = st.tabs(["📮 郵便番号 → 住所", "🏠 住所 → 郵便番号"])
    
    with tab1:
        st.markdown("### 郵便番号から住所を検索")
        postal_to_address_search(postal_service)
    
    with tab2:
        st.markdown("### 住所から郵便番号を検索")
        address_to_postal_search(postal_service)

def show_help_page():
    """使い方ページの表示"""
    st.title("📖 使い方・ヘルプ")
    
    # 基本的な使い方
    st.markdown("## 🔍 基本的な使い方")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### � 郵便番号 → 住所検索")
        st.markdown("""
        1. 「🏠 検索」ページを開く
        2. 「📮 郵便番号 → 住所」タブを選択
        3. 7桁の郵便番号を入力
        4. 🔍検索ボタンをクリック
        
        **入力例:**
        - `100-0001`
        - `1000001`
        """)
    
    with col2:
        st.markdown("### 🏠 住所 → 郵便番号検索")
        st.markdown("""
        1. 「🏠 検索」ページを開く
        2. 「🏠 住所 → 郵便番号」タブを選択
        3. 都道府県を含む住所を入力
        4. 🔍検索ボタンをクリック
        
        **入力例:**
        - `東京都千代田区丸の内`
        - `大阪市北区梅田`
        """)
    
    st.markdown("---")
    
    # データソースの説明
    st.markdown("## � データソースについて")
    
    st.markdown("### 選択可能なデータソース")
    
    with st.expander("🌐 HeartRails API"):
        st.markdown("""
        **概要:** 無料の住所検索APIを使用した全国対応版
        
        **メリット:**
        - 全国の住所に対応
        - 無料で利用可能
        - セットアップ不要
        
        **デメリット:**
        - インターネット接続が必要
        - API制限あり
        - ネットワーク状況により応答速度が変動
        
        **推奨用途:** 住所から郵便番号の検索
        """)
    
    with st.expander("� zipcloud API"):
        st.markdown("""
        **概要:** 郵便番号から住所への変換APIとシステム的逆引き検索
        
        **メリット:**
        - 日本郵便の公式データベースと連携
        - 全国対応
        - 高い精度
        - 逆引き検索対応
        
        **デメリット:**
        - インターネット接続が必要
        - 大量検索時の制限
        
        **推奨用途:** 郵便番号から住所、および住所から郵便番号の両方向検索
        """)
    
    st.markdown("---")
    
    # トラブルシューティング
    st.markdown("## 🛠️ トラブルシューティング")
    
    with st.expander("❓ よくある質問"):
        st.markdown("""
        **Q: 検索結果が表示されない**
        A: 以下をご確認ください：
        - 郵便番号は7桁で入力されているか
        - 住所に都道府県名が含まれているか
        - インターネット接続は正常か（API使用時）
        
        **Q: 住所検索の精度を上げるには？**
        A: より詳細な住所を入力してください。「東京都千代田区」より「東京都千代田区丸の内」の方が精度が高くなります。
        
        **Q: データベースの構築に失敗する**
        A: インターネット接続とディスク容量（約50MB）をご確認ください。
        """)
    
    # フッター
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #888; font-size: 12px;">データ提供: zipcloud API, HeartRails API, 日本郵便</p>', 
        unsafe_allow_html=True
    )

def postal_to_address_search(postal_service):
    """郵便番号から住所を検索するUI"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        postal_code = st.text_input(
            "郵便番号を入力",
            placeholder="例: 100-0001 または 1000001",
            help="7桁の郵便番号を入力してください（ハイフンあり・なし両対応）",
            key="postal_input",
            max_chars=8,
            label_visibility="collapsed"
        )
        
        search_button = st.button("🔍 検索", use_container_width=True, type="primary", key="postal_search")
    
    # 検索実行
    if search_button or postal_code:
        if postal_code:
            # 入力値の検証
            clean_postal_code = re.sub(r'[-−\s]', '', postal_code)
            
            if len(clean_postal_code) == 7 and clean_postal_code.isdigit():
                # 検索実行
                with st.spinner("住所を検索中..."):
                    result = postal_service.get_address_by_postal_code(postal_code)
                
                if result:
                    display_address_result(result)
                else:
                    display_error("該当する住所が見つかりませんでした", "入力された郵便番号を確認してください。")
            else:
                display_error("入力形式エラー", "郵便番号は7桁の数字で入力してください。\n**例:** 100-0001, 1000001")

def address_to_postal_search(postal_service):
    """住所から郵便番号を検索するUI"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        address = st.text_input(
            "住所を入力",
            placeholder="例: 千葉県千葉市中央区青葉町",
            help="都道府県名を含む住所を入力してください",
            key="address_input",
            max_chars=100,
            label_visibility="collapsed"
        )
        
        search_button = st.button("🔍 検索", use_container_width=True, type="primary", key="address_search")
    
    # 検索実行
    if search_button or address:
        if address and len(address.strip()) >= 2:
            with st.spinner("郵便番号を検索中..."):
                # APIのみで検索
                results = postal_service.search_postal_code_by_address(address)
            
            if results:
                display_postal_results(results)
            else:
                display_error_with_suggestions(address)
        elif address:
            display_error("入力が短すぎます", "2文字以上の住所を入力してください。")

def _extract_prefecture(address: str) -> str:
    """住所から都道府県を抽出"""
    prefectures = [
        "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
        "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
        "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
        "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
        "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
        "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
        "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
    ]
    
    for pref in prefectures:
        if pref in address:
            return pref
    return None

def display_error_with_suggestions(address: str):
    """エラーメッセージと提案を表示"""
    st.markdown('<div class="error-message">', unsafe_allow_html=True)
    st.markdown("### ❌ 該当する郵便番号が見つかりませんでした")
    
    # より具体的な提案
    pref = _extract_prefecture(address)
    if pref:
        st.markdown(f"""
        **{pref}の検索のために:**
        - より詳細な住所（区、町名など）を入力してください
        - 住所の表記を変えてみてください（例：「丁目」→「町」）
        - 全角・半角の違いがないか確認してください
        """)
    else:
        st.markdown("""
        **検索のコツ:**
        - 都道府県名を含めて入力してください
        - 例: `千葉県千葉市中央区青葉町`
        - より具体的な住所を入力してください
        """)
    
    # サンプル検索を提案
    st.markdown("### 💡 サンプル検索")
    sample_addresses = [
        "東京都千代田区",
        "大阪府大阪市北区", 
        "埼玉県熊谷市",
        "千葉県千葉市中央区"
    ]
    
    cols = st.columns(len(sample_addresses))
    for i, sample in enumerate(sample_addresses):
        with cols[i]:
            if st.button(f"📍 {sample}", key=f"sample_{i}"):
                st.session_state.address_input = sample
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_address_result(result):
    """住所検索結果の表示"""
    st.markdown('<div class="address-result">', unsafe_allow_html=True)
    st.markdown("### 📍 検索結果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**郵便番号:**")
        st.markdown(f"**{result['postal_code']}**")
        
        st.markdown("**都道府県:**")
        st.markdown(result['prefecture'])
        
        st.markdown("**市区町村:**")
        st.markdown(result['city'])
    
    with col2:
        st.markdown("**町域:**")
        st.markdown(result['town'] if result['town'] else "（該当なし）")
        
        st.markdown("**完全住所:**")
        st.markdown(f"**{result['full_address']}**")
    
    # ふりがな情報（折りたたみ可能）
    with st.expander("ふりがな情報を表示"):
        st.markdown(f"**都道府県（ふりがな）:** {result['prefecture_kana']}")
        st.markdown(f"**市区町村（ふりがな）:** {result['city_kana']}")
        if result['town_kana']:
            st.markdown(f"**町域（ふりがな）:** {result['town_kana']}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # コピー用のテキスト
    st.markdown("### 📋 コピー用")
    copy_text = result['full_address']
    st.code(copy_text, language=None)

def display_postal_results(results):
    """郵便番号検索結果の表示"""
    st.markdown('<div class="address-result">', unsafe_allow_html=True)
    st.markdown(f"### 📮 検索結果 ({len(results)}件)")
    
    for i, result in enumerate(results, 1):
        with st.expander(f"{i}. {result['postal_code']} - {result['full_address']}", expanded=(i==1)):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("**郵便番号:**")
                st.markdown(f"**{result['postal_code']}**")
                
                if 'match_score' in result:
                    st.markdown("**マッチ度:**")
                    score_percent = int(result['match_score'] * 100)
                    st.markdown(f"{score_percent}%")
            
            with col2:
                st.markdown("**住所:**")
                st.markdown(result['full_address'])
                
                # コピー用
                st.markdown("**コピー用:**")
                st.code(f"{result['postal_code']} {result['full_address']}", language=None)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_error(title, message):
    """エラーメッセージの表示"""
    st.markdown('<div class="error-message">', unsafe_allow_html=True)
    st.markdown(f"### ❌ {title}")
    st.markdown(message)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
