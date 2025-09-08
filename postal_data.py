import requests
import json
import streamlit as st
from typing import Optional, Dict, Any

class PostalCodeService:
    """郵便番号から住所情報を取得するサービス"""
    
    def __init__(self):
        self.base_url = "https://zipcloud.ibsnet.co.jp/api/search"
    
    @st.cache_data
    def get_address_by_postal_code(_self, postal_code: str) -> Optional[Dict[str, Any]]:
        """
        郵便番号から住所情報を取得
        
        Args:
            postal_code (str): 郵便番号（ハイフンあり・なし両対応）
        
        Returns:
            Dict[str, Any]: 住所情報、見つからない場合はNone
        """
        # ハイフンを除去
        clean_postal_code = postal_code.replace("-", "").replace("−", "")
        
        # 郵便番号の形式チェック（7桁の数字）
        if not clean_postal_code.isdigit() or len(clean_postal_code) != 7:
            return None
        
        try:
            # APIリクエスト
            params = {"zipcode": clean_postal_code}
            response = requests.get(_self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == 200 and data.get("results"):
                # 最初の結果を返す
                result = data["results"][0]
                return {
                    "postal_code": f"{clean_postal_code[:3]}-{clean_postal_code[3:]}",
                    "prefecture": result.get("address1", ""),
                    "city": result.get("address2", ""),
                    "town": result.get("address3", ""),
                    "full_address": f"{result.get('address1', '')}{result.get('address2', '')}{result.get('address3', '')}",
                    "prefecture_kana": result.get("kana1", ""),
                    "city_kana": result.get("kana2", ""),
                    "town_kana": result.get("kana3", "")
                }
            else:
                return None
                
        except requests.RequestException as e:
            st.error(f"通信エラーが発生しました: {e}")
            return None
        except json.JSONDecodeError:
            st.error("レスポンスの解析に失敗しました")
            return None
        except Exception as e:
            st.error(f"予期しないエラーが発生しました: {e}")
            return None
    
    @st.cache_data
    def search_postal_code_by_address(_self, address: str) -> Optional[list]:
        """
        住所から郵便番号を検索（部分一致）
        
        Args:
            address (str): 検索したい住所
        
        Returns:
            list: 該当する郵便番号と住所のリスト、見つからない場合はNone
        """
        if not address or len(address.strip()) < 2:
            return None
        
        try:
            # 住所検索用のエンドポイント（複数の結果を取得）
            # zipcloud APIは住所からの検索に対応していないため、
            # 都道府県名から検索して部分一致で絞り込む方式を採用
            
            # 都道府県のリストで検索
            prefectures = [
                "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
                "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
                "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
                "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
                "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
                "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
                "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
            ]
            
            # 入力住所に含まれる都道府県を特定
            target_prefecture = None
            for pref in prefectures:
                if pref in address:
                    target_prefecture = pref
                    break
            
            if not target_prefecture:
                # 都道府県が明確でない場合、全国検索は困難なのでエラーを返す
                return None
            
            # この実装では、実際の住所逆引きAPIが限られているため、
            # サンプルデータまたは代替実装を提供
            return _self._search_address_sample(address, target_prefecture)
                
        except Exception as e:
            st.error(f"住所検索でエラーが発生しました: {e}")
            return None
    
    def _search_address_sample(self, address: str, prefecture: str) -> list:
        """
        サンプル住所データでの検索（実装例）
        実際の運用では、より詳細な住所データベースや専用APIを使用
        """
        # サンプルデータ（一部の主要地域）
        sample_data = {
            "東京都": [
                {"postal_code": "100-0001", "address": "東京都千代田区千代田"},
                {"postal_code": "100-0004", "address": "東京都千代田区大手町"},
                {"postal_code": "100-0005", "address": "東京都千代田区丸の内"},
                {"postal_code": "100-0006", "address": "東京都千代田区有楽町"},
                {"postal_code": "100-0011", "address": "東京都千代田区内幸町"},
                {"postal_code": "100-0013", "address": "東京都千代田区霞が関"},
                {"postal_code": "100-0014", "address": "東京都千代田区永田町"},
                {"postal_code": "105-0001", "address": "東京都港区虎ノ門"},
                {"postal_code": "105-0003", "address": "東京都港区西新橋"},
                {"postal_code": "105-0004", "address": "東京都港区新橋"},
                {"postal_code": "106-0032", "address": "東京都港区六本木"},
                {"postal_code": "107-0052", "address": "東京都港区赤坂"},
                {"postal_code": "150-0001", "address": "東京都渋谷区神宮前"},
                {"postal_code": "150-0002", "address": "東京都渋谷区渋谷"},
                {"postal_code": "160-0022", "address": "東京都新宿区新宿"},
                {"postal_code": "170-0013", "address": "東京都豊島区東池袋"},
            ],
            "大阪府": [
                {"postal_code": "530-0001", "address": "大阪府大阪市北区梅田"},
                {"postal_code": "540-0008", "address": "大阪府大阪市中央区大手前"},
                {"postal_code": "542-0076", "address": "大阪府大阪市中央区難波"},
                {"postal_code": "556-0011", "address": "大阪府大阪市浪速区難波中"},
            ],
            "神奈川県": [
                {"postal_code": "220-0011", "address": "神奈川県横浜市西区高島"},
                {"postal_code": "220-0012", "address": "神奈川県横浜市西区みなとみらい"},
                {"postal_code": "231-0023", "address": "神奈川県横浜市中区山下町"},
            ]
        }
        
        results = []
        if prefecture in sample_data:
            for item in sample_data[prefecture]:
                # 部分一致で検索
                if any(part in item["address"] for part in address.split() if len(part) > 1):
                    results.append({
                        "postal_code": item["postal_code"],
                        "full_address": item["address"],
                        "match_score": self._calculate_match_score(address, item["address"])
                    })
        
        # マッチスコアでソート
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:10] if results else None  # 最大10件まで
    
    def _calculate_match_score(self, query: str, target: str) -> float:
        """住所のマッチスコアを計算"""
        query_parts = set(query.replace(" ", "").replace("　", ""))
        target_parts = set(target.replace(" ", "").replace("　", ""))
        
        if not query_parts:
            return 0.0
        
        intersection = query_parts.intersection(target_parts)
        return len(intersection) / len(query_parts)

    def format_postal_code(self, postal_code: str) -> str:
        """
        郵便番号をXXX-XXXX形式にフォーマット
        
        Args:
            postal_code (str): 入力された郵便番号
        
        Returns:
            str: フォーマット済み郵便番号
        """
        clean_code = postal_code.replace("-", "").replace("−", "")
        if len(clean_code) == 7 and clean_code.isdigit():
            return f"{clean_code[:3]}-{clean_code[3:]}"
        return postal_code
