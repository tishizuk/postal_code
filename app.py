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
</style>
""", unsafe_allow_html=True)

def main():
    # ヘッダー
    st.markdown('<h1 class="main-header">📮 郵便番号検索アプリ</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">郵便番号を入力して住所を検索しましょう</p>', unsafe_allow_html=True)
    
    # サービスのインスタンス化
    postal_service = PostalCodeService()
    
    # 入力フォーム
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 郵便番号を入力してください")
        postal_code = st.text_input(
            "",
            placeholder="例: 100-0001 または 1000001",
            help="7桁の郵便番号を入力してください（ハイフンあり・なし両対応）",
            key="postal_input",
            max_chars=8
        )
        
        search_button = st.button("🔍 検索", use_container_width=True, type="primary")
    
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
                    # 検索結果の表示
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
                    
                else:
                    # 見つからない場合
                    st.markdown('<div class="error-message">', unsafe_allow_html=True)
                    st.markdown("### ❌ 該当する住所が見つかりませんでした")
                    st.markdown("入力された郵便番号を確認してください。")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                # 入力形式エラー
                st.markdown('<div class="error-message">', unsafe_allow_html=True)
                st.markdown("### ⚠️ 入力形式エラー")
                st.markdown("郵便番号は7桁の数字で入力してください。")
                st.markdown("**例:** 100-0001, 1000001")
                st.markdown('</div>', unsafe_allow_html=True)
    
    # 使い方の説明
    st.markdown("---")
    with st.expander("💡 使い方"):
        st.markdown("""
        **📝 入力方法:**
        - 郵便番号は7桁の数字で入力してください
        - ハイフン（-）があってもなくても検索できます
        - 例: `100-0001` または `1000001`
        
        **🔍 検索について:**
        - 日本郵便の郵便番号データを使用しています
        - インターネット接続が必要です
        - 存在しない郵便番号の場合はエラーメッセージが表示されます
        
        **📋 結果の活用:**
        - 検索結果はコピーしやすい形式で表示されます
        - ふりがな情報も確認できます
        """)
    
    # フッター
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #888; font-size: 12px;">郵便番号データ提供: zipcloud API</p>', 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
