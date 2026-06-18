import os
import json
import re
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# プロジェクトルートの.envからロード
load_dotenv()

db_path = "stores_db.json"
report_path = "competitive_report.md"

def normalize_name(name):
    """
    店舗名を比較・検索用に正規化する
    「スーパー」「ストアー」「店」「(仮称)」やスペースを除去し、英数字を半角小文字にする
    """
    name = name.lower()
    name = re.sub(r'[\s\n\t]', '', name)
    name = re.sub(r'スーパー|ストアー|ストア|店|\(仮称\)|（仮称）|（予定）|\(予定\)', '', name)
    return name

def extract_competitors_from_report(file_path):
    """
    competitive_report.md の ## b) 【詳細】テーブルから競合店舗名の一覧を抽出する
    """
    if not os.path.exists(file_path):
        print(f"Report file {file_path} not found.")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 詳細テーブルの抽出
    details_match = re.search(r"## b\) 【詳細】\n(.*?)(?=\n## c\)|$)", content, re.DOTALL)
    if not details_match:
        return []

    table_text = details_match.group(1).strip()
    lines = [line.strip() for line in table_text.split("\n") if line.strip()]

    competitors = []
    for line in lines:
        if line.startswith("|") and not re.match(r"^\|[\s:| \- ]+$", line):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            # ヘッダー行やアライメント行をスキップ
            if parts[0] == "エリア" or parts[0].startswith("---") or parts[0] == ":---":
                continue
            if len(parts) > 1:
                competitors.append(parts[1])
    return list(set(competitors))

def lookup_competitor_info(client, name):
    """
    Gemini API + Google Search Grounding を用いて競合店舗の詳細情報を取得する
    """
    print(f"Searching online details for: {name}...")
    
    prompt = f"""
競合店舗「{name}」について、Google検索を用いて正確な詳細情報を調べてください。
出力は以下のJSONフォーマットのみにしてください。説明やMarkdownの装飾（```jsonなど）は一切不要です。
必ず有効なJSONオブジェクトのみを返してください。

{{
  "address": "正確な住所（ビル名・階数などがあればそれも含む）",
  "coords": [緯度, 経度],
  "hours": "営業時間（例：9:00 - 22:00、不明な場合は N/A）",
  "area": "売場面積または店舗規模（例: 約1,500㎡、または不明な場合は N/A）",
  "parking": "駐車場台数または提携駐車場の有無（例：120台、または不明な場合は N/A）",
  "features": "店舗の特徴や強みなどの簡潔な説明（50〜100文字程度）"
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        text = response.text.strip()
        # JSON部分を抽出
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            # 簡易バリデーション
            coords = data.get("coords")
            if isinstance(coords, list) and len(coords) == 2:
                lat, lon = float(coords[0]), float(coords[1])
                if 34.0 <= lat <= 36.0 and 134.5 <= lon <= 136.5:
                    return data
                else:
                    print(f"  Warning: Coordinate out of bounds for {name}: {coords}")
            else:
                print(f"  Warning: Coords missing or invalid in JSON for {name}")
        else:
            print(f"  Warning: JSON match failed. Response text: {text}")
    except Exception as e:
        print(f"  Error geocoding competitor {name}: {e}")
    return None

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment. Skipping competitor auto-lookup.")
        return

    # レポートから競合店舗名を抽出
    report_comps = extract_competitors_from_report(report_path)
    if not report_comps:
        print("No competitors found in the report detail table.")
        return

    print(f"Found competitors in report: {report_comps}")

    # データベースのロード
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)

    db_comps = db_data.get("competitors", {})
    db_comp_normalized = {normalize_name(k): k for k in db_comps.keys()}

    client = genai.Client(api_key=api_key)
    updated = False

    for comp_name in report_comps:
        norm_name = normalize_name(comp_name)
        
        # すでにDBに登録されているか判定
        matched_key = None
        for k_norm, orig_key in db_comp_normalized.items():
            if norm_name in k_norm or k_norm in norm_name:
                matched_key = orig_key
                break

        if matched_key:
            print(f"Competitor '{comp_name}' is already registered in DB as '{matched_key}'.")
            continue

        print(f"Competitor '{comp_name}' is NOT registered in DB. Starting auto-lookup...")
        # 1日のAPI制限（RPM 5 / RPD 20）を考慮し、処理前に少し待機
        time.sleep(2.0)
        
        info = lookup_competitor_info(client, comp_name)
        if info:
            # データベースへの追加形式を整理
            db_key = comp_name
            # 特徴に補足情報などを付与
            db_comps[db_key] = {
                "coords": info["coords"],
                "address": info["address"],
                "hours": info["hours"],
                "area": info["area"],
                "parking": info["parking"],
                "features": info["features"]
            }
            print(f"Successfully added '{db_key}' to DB: {db_comps[db_key]}")
            updated = True
            
            # 複数店舗ある場合のAPIレートリミット回避スリープ
            time.sleep(10.0)
        else:
            print(f"Failed to lookup details for '{comp_name}'.")

    if updated:
        db_data["competitors"] = db_comps
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        print("stores_db.json updated with new competitor information.")
    else:
        print("No new competitors were added to DB.")

if __name__ == "__main__":
    main()
