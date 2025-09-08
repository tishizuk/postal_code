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
