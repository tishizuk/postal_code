import streamlit as st
import re
from postal_data import PostalCodeService

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
    
    # 使い方の説明
    st.markdown("---")
    with st.expander("💡 使い方"):
        st.markdown("""
        **📮 郵便番号 → 住所検索:**
        - 郵便番号は7桁の数字で入力してください
        - ハイフン（-）があってもなくても検索できます
        - 例: `100-0001` または `1000001`
        
        **🏠 住所 → 郵便番号検索:**
        - 都道府県名を含む住所を入力してください
        - 部分一致で検索します
        - 例: `東京都千代田区丸の内` や `大阪市北区梅田`
        
        **🔍 検索について:**
        - 日本郵便の郵便番号データを使用しています
        - インターネット接続が必要です
        - 住所検索は主要地域のサンプルデータを使用
        
        **📋 結果の活用:**
        - 検索結果はコピーしやすい形式で表示されます
        - ふりがな情報も確認できます（郵便番号検索）
        """)
    
    # フッター
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #888; font-size: 12px;">郵便番号データ提供: zipcloud API | 住所検索: サンプルデータ</p>', 
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
            placeholder="例: 東京都千代田区丸の内 または 大阪市北区梅田",
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
                results = postal_service.search_postal_code_by_address(address)
            
            if results:
                display_postal_results(results)
            else:
                display_error(
                    "該当する郵便番号が見つかりませんでした", 
                    "都道府県名を含む住所を入力してください。\n現在は主要地域のみ対応しています。"
                )
        elif address:
            display_error("入力が短すぎます", "2文字以上の住所を入力してください。")

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
