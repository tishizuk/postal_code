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
        住所から郵便番号を検索（APIのみ使用）
        
        Args:
            address (str): 検索したい住所
        
        Returns:
            list: 該当する郵便番号と住所のリスト、見つからない場合はNone
        """
        if not address or len(address.strip()) < 2:
            return None
        
        try:
            # HeartRails Geo APIを使用（APIのみ）
            results = _self._search_with_heartrails_api(address)
            if results:
                return results
            
            # zipcloud APIでの逆引き検索を試行
            return _self._search_with_zipcloud_reverse(address)
                
        except Exception as e:
            st.error(f"住所検索でエラーが発生しました: {e}")
            return None

    def _search_with_heartrails_api(self, address: str) -> Optional[list]:
        """
        HeartRails Geo APIを使用した住所検索
        """
        try:
            st.info("🔍 HeartRails Geo APIで検索中...")
            
            # HeartRails Geo APIエンドポイント
            api_url = "https://geoapi.heartrails.com/api/json"
            params = {
                "method": "searchByGeoLocation",
                "area": address
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("response") and data["response"].get("location"):
                    return self._process_api_response(data, address)
            
            return None
            
        except Exception:
            return None
    
    def _search_with_zipcloud_reverse(self, address: str) -> Optional[list]:
        """
        zipcloud APIを使用した逆引き検索
        郵便番号を推測してAPIで確認する方式
        """
        try:
            st.info("🔍 zipcloud APIで検索中...")
            
            # 住所から都道府県と市区町村を抽出
            prefecture, city = self._extract_prefecture_city(address)
            
            if not prefecture or not city:
                st.warning("都道府県または市区町村が特定できませんでした")
                return None
            
            # 郵便番号パターンを推測
            postal_patterns = self._get_postal_patterns_extended(prefecture, city)
            
            results = []
            checked_count = 0
            max_check = min(50, len(postal_patterns))  # 最大50件まで確認
            
            # 進捗表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pattern in enumerate(postal_patterns[:max_check]):
                # 進捗更新
                progress = (i + 1) / max_check
                progress_bar.progress(progress)
                status_text.text(f"郵便番号確認中: {pattern[:3]}-{pattern[3:]} ({i+1}/{max_check})")
                
                try:
                    # zipcloud APIで郵便番号を確認
                    response = requests.get(
                        self.base_url,
                        params={"zipcode": pattern},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        checked_count += 1
                        
                        if data.get("status") == 200 and data.get("results"):
                            for result in data["results"]:
                                full_address = f"{result.get('address1', '')}{result.get('address2', '')}{result.get('address3', '')}"
                                
                                # 住所マッチング
                                match_score = self._calculate_simple_match_score(address, full_address)
                                
                                if match_score > 0.7:  # 70%以上の一致
                                    results.append({
                                        "postal_code": f"{pattern[:3]}-{pattern[3:]}",
                                        "full_address": full_address,
                                        "match_score": match_score,
                                        "source": "zipcloud API"
                                    })
                        
                except requests.RequestException:
                    continue
            
            # 進捗バーをクリア
            progress_bar.empty()
            status_text.empty()
            
            if results:
                st.success(f"✅ {len(results)}件の郵便番号が見つかりました！")
                results.sort(key=lambda x: x["match_score"], reverse=True)
                return results[:10]  # 上位10件
            else:
                st.warning(f"⚠️ {checked_count}件の郵便番号を確認しましたが、該当する住所が見つかりませんでした。")
                return None
                
        except Exception as e:
            st.error(f"検索エラー: {e}")
            return None
    
    def _process_api_response(self, data: dict, original_address: str) -> Optional[list]:
        """API レスポンスの処理"""
        results = []
        locations = data["response"]["location"]
        
        if not isinstance(locations, list):
            locations = [locations]
        
        for location in locations[:10]:
            postal_code = location.get("postal")
            if postal_code:
                formatted_postal = f"{postal_code[:3]}-{postal_code[3:]}" if len(postal_code) == 7 else postal_code
                full_address = f"{location.get('prefecture', '')}{location.get('city', '')}{location.get('town', '')}"
                
                results.append({
                    "postal_code": formatted_postal,
                    "full_address": full_address,
                    "match_score": self._calculate_simple_match_score(original_address, full_address),
                    "source": "HeartRails Geo API"
                })
        
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results if results else None
    
    def _calculate_simple_match_score(self, query: str, target: str) -> float:
        """シンプルなマッチングスコア計算"""
        if not query or not target:
            return 0.0
        
        query_clean = query.replace(" ", "").replace("　", "")
        target_clean = target.replace(" ", "").replace("　", "")
        
        # 完全一致
        if query_clean == target_clean:
            return 1.0
        
        # 部分一致
        if query_clean in target_clean:
            return 0.95
        
        if target_clean in query_clean:
            return 0.9
        
        # 文字の共通度
        query_chars = set(query_clean)
        target_chars = set(target_clean)
        
        if not query_chars:
            return 0.0
        
        common_chars = query_chars.intersection(target_chars)
        return len(common_chars) / len(query_chars)
    
    def _extract_prefecture_city(self, address: str) -> tuple:
        """住所から都道府県と市区町村を抽出"""
        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
        ]
        
        prefecture = None
        city = None
        
        for pref in prefectures:
            if pref in address:
                prefecture = pref
                remaining = address[address.find(pref) + len(pref):].strip()
                
                # 市区町村名を抽出
                for suffix in ["市", "区", "町", "村"]:
                    if suffix in remaining:
                        end_pos = remaining.find(suffix) + len(suffix)
                        city = remaining[:end_pos]
                        break
                
                if not city and remaining:
                    city = remaining.split()[0] if remaining.split() else remaining[:6]
                
                break
        
        return prefecture, city

    def _get_postal_patterns_extended(self, prefecture: str, city: str) -> list:
        """拡張された郵便番号パターン生成"""
        # 都道府県別の郵便番号範囲（実際のデータに基づく）
        prefecture_ranges = {
            "埼玉県": {
                "熊谷市": ["360", "361"],
                "さいたま市": ["330", "331", "336", "337", "338"],
                "川口市": ["332", "333"],
                "川越市": ["350"],
                "所沢市": ["359"],
            },
            "千葉県": {
                "千葉市": ["260", "261", "262", "263", "264", "265", "266"],
                "市川市": ["272"],
                "船橋市": ["273", "274"],
                "松戸市": ["270", "271"],
            },
            "東京都": {
                "千代田区": ["100", "101", "102"],
                "中央区": ["103", "104"],
                "港区": ["105", "106", "107", "108"],
                "新宿区": ["160", "161", "162", "163", "169"],
                "渋谷区": ["150", "151"],
            },
            "大阪府": {
                "大阪市": ["530", "531", "532", "533", "534", "535", "540", "541", "542", "543", "544", "545", "546", "547", "550", "551", "552", "553", "554", "556", "557", "558", "559"],
                "堺市": ["590", "591", "592", "593", "594", "599"],
            },
        }
        
        patterns = []
        
        if prefecture in prefecture_ranges and city in prefecture_ranges[prefecture]:
            # 該当する郵便番号範囲を取得
            ranges = prefecture_ranges[prefecture][city]
            for range_prefix in ranges:
                for i in range(10000):  # 0000-9999
                    patterns.append(f"{range_prefix}{i:04d}")
        else:
            # デフォルトパターン（推測）
            default_range = f"{hash(prefecture + city) % 900 + 100:03d}"
            for i in range(10000):
                patterns.append(f"{default_range}{i:04d}")
        
        return patterns

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
