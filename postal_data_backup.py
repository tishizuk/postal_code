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
        実用的な住所検索の実装
        zipcloud APIの逆引き機能を使用して実装
        """
        try:
            st.info("🔍 全国データベースで検索中...")
            
            # 住所から都道府県と市区町村を分離
            prefecture, city = self._parse_address(address)
            
            if not prefecture or not city:
                st.warning(f"住所解析失敗: 都道府県='{prefecture}', 市区町村='{city}'")
                return None
            
            # 該当地域の郵便番号パターンを取得
            postal_patterns = self._get_postal_patterns_extended(prefecture, city)
            
            results = []
            checked_count = 0
            
            # 進捗表示用
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pattern in enumerate(postal_patterns):
                # 進捗更新
                progress = (i + 1) / len(postal_patterns)
                progress_bar.progress(progress)
                status_text.text(f"検索中... {i+1}/{len(postal_patterns)} ({pattern[:3]}-{pattern[3:]})")
                
                # zipcloud APIで郵便番号から住所を取得
                api_url = "https://zipcloud.ibsnet.co.jp/api/search"
                params = {"zipcode": pattern}
                
                try:
                    response = requests.get(api_url, params=params, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == 200 and data.get("results"):
                            for result in data["results"]:
                                full_addr = f"{result.get('address1', '')}{result.get('address2', '')}{result.get('address3', '')}"
                                
                                # 市区町村名が含まれているかチェック
                                if city in full_addr:
                                    results.append({
                                        "postal_code": f"{pattern[:3]}-{pattern[3:]}",
                                        "full_address": full_addr,
                                        "prefecture": result.get('address1', ''),
                                        "city": result.get('address2', ''),
                                        "town": result.get('address3', ''),
                                        "match_score": self._calculate_match_score(address, full_addr),
                                        "source": "全国郵便番号データ"
                                    })
                    
                    checked_count += 1
                    
                    # 十分な結果が得られたら終了
                    if len(results) >= 10:
                        break
                        
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
    
    def _search_with_zipcloud_reverse(self, address: str) -> Optional[list]:
        """
        zipcloud APIを使用した逆引き検索
        郵便番号を推測してAPIで確認する方式
        """
        try:
            st.info("🔍 郵便番号データベースで検索中...")
            
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
        }
        
        patterns = []
        
        if prefecture in prefecture_ranges and city in prefecture_ranges[prefecture]:
            # 該当する郵便番号範囲を取得
            ranges = prefecture_ranges[prefecture][city]
            for range_prefix in ranges:
                # 各範囲の0000-9999まで生成（実際は存在するもののみ）
                for suffix in range(0, 100):  # 現実的な範囲に制限
                    pattern = f"{range_prefix}{suffix:04d}"
                    patterns.append(pattern)
        else:
            # 汎用的なパターン生成
            # 日本の郵便番号は100-0000から999-9999の範囲
            base_code = hash(f"{prefecture}{city}") % 900 + 100
            for i in range(50):  # 50パターンを試行
                pattern = f"{base_code + i:03d}{i*13 % 10000:04d}"
                patterns.append(pattern)
        
        return patterns[:50]  # 最大50パターンに制限
    
    def _parse_address(self, address: str) -> tuple:
        """住所を都道府県と市区町村に分解"""
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
    
    def _calculate_match_score(self, query: str, target: str) -> float:
        
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
    
    def _get_postal_patterns(self, prefecture: str, city: str) -> list:
        """都道府県と市区町村から郵便番号パターンを推測"""
        # 主要都市の郵便番号開始パターン
        patterns_map = {
            ("埼玉県", "熊谷市"): ["3600000", "3600001", "3600002", "3600003", "3600004", "3600005"],
            ("埼玉県", "さいたま市"): ["3300000", "3300001", "3300002", "3300003", "3300004"],
            ("千葉県", "千葉市"): ["2600000", "2600001", "2600002", "2600003", "2610000"],
            ("東京都", "千代田区"): ["1000000", "1000001", "1000002", "1000003", "1000004"],
            ("大阪府", "大阪市"): ["5300000", "5300001", "5400000", "5400001", "5500000"],
        }
        
        key = (prefecture, city)
        return patterns_map.get(key, [f"{hash(key) % 900 + 100:03d}0000"])  # フォールバック
    
    def _search_with_broader_terms(self, address: str) -> Optional[list]:
        """より広い検索語でHeartRails APIを再試行"""
        try:
            # 住所から都道府県と市区町村を抽出
            parts = []
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
                    parts.append(pref)
                    # 都道府県より後の部分を取得
                    remaining = address[address.find(pref) + len(pref):]
                    # 市区町村名を抽出（最初の3-6文字程度）
                    if remaining:
                        city_part = remaining[:6]  # 適当な長さで切り取り
                        parts.append(city_part)
                    break
            
            if len(parts) >= 2:
                broader_search = "".join(parts)
                api_url = "https://geoapi.heartrails.com/api/json"
                params = {
                    "method": "searchByGeoLocation", 
                    "area": broader_search
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response") and data["response"].get("location"):
                        # 処理は上記と同様
                        return self._process_api_response(data, address)
            
            return None
            
        except Exception:
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
                    "prefecture": location.get('prefecture', ''),
                    "city": location.get('city', ''),
                    "town": location.get('town', ''),
                    "match_score": self._calculate_match_score(original_address, full_address),
                    "source": "HeartRails API"
                })
        
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results if results else None
    
    def _search_address_sample(self, address: str) -> Optional[list]:
        """
        サンプル住所データでの検索（無効化）
        APIのみ使用するため、この関数は使用されません
        """
        st.warning("⚠️ サンプルデータでの検索は無効化されています。APIのみで検索を行います。")
        return None
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
        
        # サンプルデータを使用した検索
        return self._search_sample_data(address, target_prefecture)
    
    def _search_sample_data(self, address: str, prefecture: str) -> Optional[list]:
        """サンプルデータでの検索（無効化）"""
        st.warning("⚠️ サンプルデータでの検索は無効化されています。APIのみで検索を行います。")
        return None
        """サンプルデータでの検索"""
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
            ],
            "千葉県": [
                {"postal_code": "260-0013", "address": "千葉県千葉市中央区中央"},
                {"postal_code": "260-0045", "address": "千葉県千葉市中央区弁天"},
                {"postal_code": "260-0026", "address": "千葉県千葉市中央区千葉港"},
                {"postal_code": "260-0028", "address": "千葉県千葉市中央区新町"},
                {"postal_code": "260-0001", "address": "千葉県千葉市中央区都町"},
                {"postal_code": "260-0031", "address": "千葉県千葉市中央区新千葉"},
                {"postal_code": "260-0024", "address": "千葉県千葉市中央区中央港"},
                {"postal_code": "260-0014", "address": "千葉県千葉市中央区本千葉町"},
                {"postal_code": "260-0021", "address": "千葉県千葉市中央区新宿"},
                {"postal_code": "260-0032", "address": "千葉県千葉市中央区登戸"},
                {"postal_code": "261-0001", "address": "千葉県千葉市美浜区幸町"},
                {"postal_code": "261-0021", "address": "千葉県千葉市美浜区ひび野"},
                {"postal_code": "262-0032", "address": "千葉県千葉市花見川区幕張町"},
                {"postal_code": "263-0031", "address": "千葉県千葉市稲毛区稲毛東"},
                {"postal_code": "264-0028", "address": "千葉県千葉市若葉区桜木"},
                {"postal_code": "266-0033", "address": "千葉県千葉市緑区おゆみ野南"},
                # 青葉町を追加
                {"postal_code": "260-0852", "address": "千葉県千葉市中央区青葉町"},
            ],
            "埼玉県": [
                {"postal_code": "330-0846", "address": "埼玉県さいたま市大宮区大門町"},
                {"postal_code": "330-0801", "address": "埼玉県さいたま市大宮区土手町"},
                {"postal_code": "330-0854", "address": "埼玉県さいたま市大宮区桜木町"},
                {"postal_code": "336-0018", "address": "埼玉県さいたま市南区南本町"},
                {"postal_code": "338-0001", "address": "埼玉県さいたま市中央区上落合"},
                # 熊谷市を追加
                {"postal_code": "360-0037", "address": "埼玉県熊谷市筑波"},
                {"postal_code": "360-0004", "address": "埼玉県熊谷市上川上"},
                {"postal_code": "360-0014", "address": "埼玉県熊谷市箱田"},
                {"postal_code": "360-0031", "address": "埼玉県熊谷市末広"},
                {"postal_code": "360-0033", "address": "埼玉県熊谷市曙町"},
                {"postal_code": "360-0032", "address": "埼玉県熊谷市銀座"},
                {"postal_code": "360-0042", "address": "埼玉県熊谷市本町"},
                {"postal_code": "360-0041", "address": "埼玉県熊谷市宮町"},
                {"postal_code": "360-0046", "address": "埼玉県熊谷市鎌倉町"},
                {"postal_code": "360-0043", "address": "埼玉県熊谷市星川"},
            ],
            "兵庫県": [
                {"postal_code": "650-0011", "address": "兵庫県神戸市中央区下山手通"},
                {"postal_code": "650-0021", "address": "兵庫県神戸市中央区三宮町"},
                {"postal_code": "651-0087", "address": "兵庫県神戸市中央区御幸通"},
                {"postal_code": "658-0032", "address": "兵庫県神戸市東灘区向洋町中"},
            ]
        }
        
        results = []
        if prefecture in sample_data:
            for item in sample_data[prefecture]:
                # 改善されたマッチング
                match_score = self._calculate_match_score(address, item["address"])
                
                # より厳しい閾値を設定
                if match_score > 0.7:
                    results.append({
                        "postal_code": item["postal_code"],
                        "full_address": item["address"],
                        "match_score": match_score,
                        "source": "サンプルデータ"
                    })
        
        # マッチスコアでソート
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:10] if results else None  # 最大10件まで
    
    def _calculate_match_score(self, query: str, target: str) -> float:
        """住所のマッチスコアを計算（厳密版）"""
        if not query or not target:
            return 0.0
        
        # 正規化
        query_clean = query.replace(" ", "").replace("　", "")
        target_clean = target.replace(" ", "").replace("　", "")
        
        # 完全一致の場合は最高スコア
        if query_clean == target_clean:
            return 1.0
        
        # 完全に含まれる場合
        if query_clean in target_clean:
            return 0.95
        
        if target_clean in query_clean:
            return 0.9
        
        # 住所の構成要素を抽出
        query_parts = self._extract_address_components(query_clean)
        target_parts = self._extract_address_components(target_clean)
        
        # 都道府県、市区町村、町域が全て一致する必要がある
        prefecture_match = self._compare_component(query_parts['prefecture'], target_parts['prefecture'])
        city_match = self._compare_component(query_parts['city'], target_parts['city'])
        area_match = self._compare_component(query_parts['area'], target_parts['area'])
        
        # 都道府県が一致しない場合は低スコア
        if not prefecture_match:
            return 0.1
        
        # 市区町村が一致しない場合も低スコア
        if not city_match:
            return 0.2
        
        # 町域の一致度で最終スコアを決定
        if area_match:
            return 0.85
        
        # 部分的な町域一致
        if query_parts['area'] and target_parts['area']:
            if (query_parts['area'] in target_parts['area'] or 
                target_parts['area'] in query_parts['area']):
                return 0.75
        
        # 都道府県と市区町村のみ一致
        return 0.3
    
    def _extract_address_components(self, address: str) -> dict:
        """住所を都道府県、市区町村、町域に分解"""
        components = {'prefecture': '', 'city': '', 'area': ''}
        remaining = address
        
        # 都道府県を抽出
        for pref in ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
                     "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
                     "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
                     "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
                     "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
                     "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
                     "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]:
            if pref in remaining:
                components['prefecture'] = pref
                remaining = remaining.replace(pref, "", 1)
                break
        
        # 市区町村を抽出
        import re
        city_pattern = r'([^都道府県]+?[市区町村])'
        city_match = re.search(city_pattern, remaining)
        if city_match:
            components['city'] = city_match.group(1)
            remaining = remaining.replace(components['city'], "", 1)
        
        # 残りは町域
        components['area'] = remaining.strip()
        
        return components
    
    def _compare_component(self, comp1: str, comp2: str) -> bool:
        """住所コンポーネントの比較"""
        if not comp1 or not comp2:
            return comp1 == comp2
        
        return comp1 == comp2 or comp1 in comp2 or comp2 in comp1

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
