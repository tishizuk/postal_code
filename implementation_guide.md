# 住所→郵便番号検索の実装ガイド 🗺️

## 📊 実装済みソリューション

### 1. 🗃️ サンプルデータ（軽量版）
**現在の実装:** `postal_data.py` の `_search_sample_data`
- **対応地域:** 東京都、大阪府、神奈川県の主要地域
- **メリット:** 高速、オフライン、セットアップ不要
- **デメリット:** 限定的な地域のみ

### 2. 🌐 HeartRails Geo API（無料API）
**現在の実装:** `postal_data.py` の `_search_with_heartrails_api`
- **対応地域:** 全国
- **メリット:** 無料、全国対応、セットアップ不要
- **デメリット:** インターネット必須、API制限あり

### 3. 🗄️ ローカルデータベース（高速・完全版）
**現在の実装:** `postal_database.py`
- **対応地域:** 全国（日本郵便公式データ）
- **メリット:** 高速、オフライン、完全対応
- **デメリット:** 初回セットアップ必要（約20MB）

## 🚀 運用レベルでの推奨実装

### A. スタートアップ・個人利用
```python
# HeartRails API + キャッシュ
def search_address_startup(address):
    # 1. キャッシュから検索
    # 2. API呼び出し
    # 3. 結果をキャッシュ
    pass
```

### B. 中規模サービス
```python
# ローカルDB + API フォールバック
def search_address_medium(address):
    # 1. ローカルDBで検索
    # 2. 見つからない場合はAPI
    # 3. API結果をDBに保存
    pass
```

### C. 大規模サービス
```python
# 専用DB + 定期更新
def search_address_enterprise(address):
    # 1. PostgreSQL/MySQL
    # 2. 全文検索インデックス
    # 3. 定期的なデータ更新
    # 4. 冗長化・負荷分散
    pass
```

## 💰 コスト比較

| 方式 | 初期コスト | 運用コスト | スケーラビリティ |
|------|------------|------------|------------------|
| サンプルデータ | 無料 | 無料 | 低 |
| HeartRails API | 無料 | 無料 | 中 |
| ローカルDB | 無料 | 低 | 高 |
| Google Maps API | 無料枠あり | 従量課金 | 高 |
| 専用DB構築 | 中〜高 | 中 | 最高 |

## 🔧 実装手順

### ステップ1: 現在のアプリで試す
1. 「⚙️設定」ページでデータソースを選択
2. 各方式の特徴を確認
3. 用途に応じて最適な方式を決定

### ステップ2: 本格運用への移行

#### 2-1. HeartRails API運用
```python
# レート制限の実装
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 1.0 / calls_per_second - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
```

#### 2-2. 専用データベース構築
```sql
-- PostgreSQL テーブル設計例
CREATE TABLE postal_addresses (
    id SERIAL PRIMARY KEY,
    postal_code VARCHAR(8) NOT NULL,
    prefecture VARCHAR(20) NOT NULL,
    city VARCHAR(50) NOT NULL,
    town VARCHAR(100),
    full_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 全文検索インデックス
CREATE INDEX idx_full_address_gin ON postal_addresses 
USING gin(to_tsvector('japanese', full_address));
```

#### 2-3. 商用APIの利用
```python
# Google Maps Geocoding API例
import googlemaps

def search_with_google_maps(address, api_key):
    gmaps = googlemaps.Client(key=api_key)
    geocode_result = gmaps.geocode(address)
    # 結果の処理
    return process_google_results(geocode_result)
```

## 🏆 推奨構成

### 段階的アップグレード戦略

1. **プロトタイプ段階**
   - サンプルデータ使用
   - 機能検証に集中

2. **MVP段階**
   - HeartRails API導入
   - ユーザーフィードバック収集

3. **成長段階**
   - ローカルDB構築
   - パフォーマンス最適化

4. **スケール段階**
   - 専用インフラ構築
   - 高可用性対応

## 📈 パフォーマンス目標

| 段階 | 応答時間目標 | 対応件数/日 |
|------|--------------|-------------|
| プロトタイプ | <2秒 | 〜100件 |
| MVP | <1秒 | 〜1,000件 |
| 成長期 | <500ms | 〜10,000件 |
| スケール期 | <200ms | 100,000件+ |
