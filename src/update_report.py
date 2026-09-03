import os
import re
import html
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def generate_report(mode="within_2km"):
    """Gemini API + Google Search Grounding を用いて、
    最新の競合ニュースを検索・調査しレポートを生成する"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in .env. Skipping LLM generation.")
        print("Falling back: keeping the previous report as-is.")
        return

    # 前回のレポートを読み込む
    os.makedirs("report", exist_ok=True)
    filename = "report/competitive_report_within_2km.md" if mode == "within_2km" else "report/competitive_report_no_limit.md"
    previous_report = ""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                previous_report = f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read previous report: {e}")

    # いかりスーパー既存店の位置情報（住所・座標）をロード
    ikari_stores_info = ""
    if os.path.exists("data/stores_db.json"):
        try:
            import json
            with open("data/stores_db.json", "r", encoding="utf-8") as f:
                db_data = json.load(f)
            ikari_list = []
            for name, info in db_data.get("ikari_stores", {}).items():
                ikari_list.append(f"- {name}: {info.get('address', '')} (座標: {info.get('coords', [])})")
            ikari_stores_info = "\n".join(ikari_list)
        except Exception as e:
            print(f"Warning: Could not load stores_db.json: {e}")

    client = genai.Client(api_key=api_key)
    today = datetime.today().strftime("%Y年%m月%d日")

    # モードに応じたクエリリストとプロンプトの組み立て
    if mode == "within_2km":
        queries_text = """1. "いかりスーパー 競合"
2. "関西 スーパー 新規出店 2026"
3. "オーケー 関西 出店"
4. "阪急オアシス 新店舗 改装"
5. "ロピア 関西 出店"
6. "ヤマダストアー 出店"
7. "成城石井 関西" """

        prompt = f"""あなたは「いかりスーパーマーケット」（兵庫県・大阪府を中心に展開する高級スーパー）の経営戦略室に所属する競合分析アナリストです。
本日しは{today}（調査日）です。

【あなたへの指示】
付属のGoogle検索ツールを用いて、以下の検索キーワードについて最新情報を調査し、いかりスーパー既存店舗の周辺環境における競合動向（新規出店・改装情報など）を分析してレポートを作成してください。
必ず、Google検索で実際に見つかった本物のニュース記事のタイトルとURLを参照ソースとして使用し、架空のURLや不正確なURL（例: xxxx やダミー文字を含むもの）を出力することは絶対に避けてください。

【調査キーワード】
{queries_text}

【前回のレポート内容】
{previous_report if previous_report else "(前回のレポートはありません)"}

【厳守：対象地域制限（半径2kmルール）】
レポートの対象とする競合店舗の新規出店・改装・動向は、以下の「いかりスーパー既存店舗」の一覧に記載されたいずれかの店舗から**半径2.0km以内**で発生するもののみに厳しく限定してください。
いかり既存店舗から2.0km以上離れたエリア（例: 大阪府堺市や大阪南部地域など、周辺2km以内にいかりスーパーが一切存在しない地域）の競合ニュースは、検索結果で見つかったとしても、絶対にレポートに含めず、完全に除外してください。

いかりスーパー既存店舗一覧:
{ikari_stores_info if ikari_stores_info else "(ロード失敗。通常通り阪神間・北摂・京都常盤等の既存エリア周辺に限定してください)"}

【分析・判定ルール】
1. 前回のレポート（存在する場合）およびGoogle検索結果を比較し、前回のレポートから「更新された情報」や「新規の周辺環境の変化（新規の出店計画・改装計画・競合の新たな動きなど）」があるかどうかを判断してください。
2. 前回のレポートから情報更新がない場合（新しい出店ニュースや競合の新たな動きが検索結果から見つからない場合、あるいは前回の内容と重複している場合）、レポート全体を「更新情報無し」というテキストのみで出力してください。それ以外の見出しやフォーマットは不要です。
3. 調査日（本日：{today}）以前にすでにオープンしている店舗や、すでに終了しているイベントなど、調査日以前の過去情報は一切不要です。調査日以降（本日および未来）に発生する周辺環境の変化（これからオープン予定の店舗、これからの改装計画、本日に新しく発表された競合の動きなど）のみをレポートの対象としてください。
4. 情報更新がある場合、前回のレポート内容をそのまま引き継ぐのではなく、本日（調査日）以降に新たに発生・判明した周辺環境の変化や、前回のレポートからの差分（更新情報）のみを記載してください。
5. 参照ソースには、今回の検索で実際に見つけた新規ニュースのタイトルと本物のURLを、Markdownのリンク形式のみで記載してください。形式は必ず「* [実際のニュースタイトル](本物のURL)」とし、タイトルの外側に余計なURLテキストを並べたり、「[URL](URL)」のような形式で出力することは厳禁とします。必ずタイトル文字列自体を[]の中に記述してください。Google検索結果以外の架空のURLは禁止します。
6. コードブロック(```)は使わず、直接Markdownテキストのみ出力してください。

【情報更新がある場合の必須フォーマット】（以下の見出し構成を完全に守ること）

## a) 【結論】
*   (調査日以降の経営判断に直結する結論や、今回新たに発生した変化の要約を3〜5点。具体的な競合名・エリア・時期を含めること)

## b) 【詳細】
| エリア | 競合店舗名 | 時期 | 状態 | 影響店舗 | 影響レベル | 詳細説明 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| (今回新たに確認された、調査日以降の競合動向のみ。影響店舗の列には、その競合店から半径2.0km以内にあるいかりスーパー既存店舗名をカンマ区切りで記載してください（例：いかりJR大阪店、いかり芦屋店）。) | ... | ... | ... | ... | ... | ... |

## c) 【地図分析】
*   (今回新しく出た出店・改装場所に関する地理的な考察。いかりスーパー既存店舗との位置関係など)

## d) 【影響分析】
*   (いかりスーパーの具体的な店舗名を挙げて、今回新たに判明した変化による影響を考察すること)

## e) 【参照ソース】
*   ([実際のニュースタイトル](本物のURL))
"""
    else:
        queries_text = """1. "いかりスーパー 競合"
2. "関西 スーパー 新規出店 2026"
3. "阪急オアシス 新店舗 改装"
4. "成城石井 関西"
5. "関西 食品スーパー 新規出店" """

        prompt = f"""あなたは「いかりスーパーマーケット」（兵庫県・大阪府を中心に展開する高級スーパー）の経営戦略室に所属する競合分析アナリストです。
本日しは{today}（調査日）です。

【あなたへの指示】
付属のGoogle検索ツールを用いて、以下の検索キーワードについて最新情報を調査し、関西エリア（兵庫県、大阪府、京都府など）のスーパーマーケット市場全体における競合動向（新規出店・改装情報など）を広く分析し、レポートを作成してください。
いかり既存店舗からの距離制限（半径2km制限）はありません。また、特定の優先的に調査する競合店舗（重点競合店舗）もありません。新規出店や改装などの動向があれば、スーパーマーケットチェーンの知名度や規模に関わらず、広く詳細をレポートに含めてください。
必ず、Google検索で実際に見つかった本物のニュース記事のタイトルとURLを参照ソースとして使用し、架空のURLや不正確なURL（例: xxxx やダミー文字を含むもの）を出力することは絶対に避けてください。

【調査キーワード】
{queries_text}

【前回のレポート内容】
{previous_report if previous_report else "(前回のレポートはありません)"}

いかりスーパー既存店舗一覧（影響分析や最も近い店舗の識別のために参考にしてください）:
{ikari_stores_info if ikari_stores_info else "(ロード失敗)"}

【分析・判定ルール】
1. 前回のレポート（存在する場合）およびGoogle検索結果を比較し、前回のレポートから「更新された情報」や「新規の周辺環境の変化（新規の出店計画・改装計画・競合の新たな動きなど）」があるかどうかを判断してください。
2. 前回のレポートから情報更新がない場合（新しい出店ニュースや競合の新たな動きが検索結果から見つからない場合、あるいは前回の内容と重複している場合）、レポート全体を「更新情報無し」というテキストのみで出力してください。それ以外の見出しやフォーマットは不要です。
3. 調査日（本日：{today}）以前にすでにオープンしている店舗や、すでに終了しているイベントなど、調査日以前の過去情報は一切不要です。調査日以降（本日および未来）に発生する周辺環境の変化（これからオープン予定の店舗、これからの改装計画、本日に新しく発表された競合の動きなど）のみをレポートの対象としてください。
4. 情報更新がある場合、前回のレポート内容をそのまま引き継ぐのではなく、本日（調査日）以降に新たに発生・判明した周辺環境の変化や、前回のレポートからの差分（更新情報）のみを記載してください。
5. 参照ソースには、今回の検索で実際に見つけた新規ニュースのタイトルと本物のURLを、Markdown의 リンク形式のみで記載してください。形式は必ず「* [実際のニュースタイトル](本物のURL)」とし、タイトルの外側に余計なURLテキストを並べたり、「[URL](URL)」のような形式で出力することは厳禁とします。必ずタイトル文字列自体を[]の中に記述してください。Google検索結果以外の架空のURLは禁止します。
6. コードブロック(```)は使わず、直接Markdownテキストのみ出力してください。

【情報更新がある場合の必須フォーマット】（以下の見出し構成を完全に守ること）

## a) 【結論】
*   (調査日以降の経営判断に直結する結論や、今回新たに発生した変化の要約を3〜5点。具体的な競合名・エリア・時期を含めること)

## b) 【詳細】
| エリア | 競合店舗名 | 時期 | 状態 | 影響店舗 | 影響レベル | 詳細説明 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| (今回新たに確認された、調査日以降の競合動向のみ。影響店舗の列には、その競合店から比較的近い位置にあるいかりスーパー既存店舗名をカンマ区切りで記載してください（いかりスーパー全店舗が対象です。特に近い店舗が複数あればカンマ区切りで記載し、特に該当しなければ「関西全域」や「特になし」などとしてください）。) | ... | ... | ... | ... | ... | ... |

## c) 【地図分析】
*   (今回新しく出た出店・改装場所に関する地理的な考察。いかりスーパー既存店舗との位置関係など)

## d) 【影響分析】
（※重要：必ず影響を受けるいかりスーパーの店舗名ごとに「1. 店舗名」「2. 店舗名」で見出しを立て、各行に箇条書きで具体的な影響や対策を記述してください。例：
1. いかりJR大阪店
*   ヤマダストアー大丸梅田店の出店により同一商圏での顧客争奪が予想されるため、デパ地下としての付加価値提供や独自商品の強化が必要。
2. いかり宝塚店、いかり阪急逆瀬川店
*   ヤマダストアー宝塚店（伊孑志計画）により地域顧客の流動が懸念されるため、地域密着サービスや独自PBの訴求強化が求められる。
）

## e) 【参照ソース】
*   ([実際のニュースタイトル](本物のURL))
"""

    # API呼び出し部分 (リトライとモデルのフォールバックを導入)
    import time
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash"]
    max_retries_per_model = 4
    response = None
    success = False

    for model_name in models_to_try:
        for attempt in range(max_retries_per_model):
            try:
                print(f"Calling Gemini API with {model_name} (Attempt {attempt+1}/{max_retries_per_model})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                if response and response.text:
                    success = True
                    break
                else:
                    wait_time = min(60, 5 * (2 ** attempt))
                    print(f"Warning: Gemini API returned empty text for {model_name} (Attempt {attempt+1}/{max_retries_per_model}). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            except Exception as e:
                wait_time = min(60, 5 * (2 ** attempt))
                print(f"Warning: Gemini API call failed for {model_name} (Attempt {attempt+1}/{max_retries_per_model}): {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        if success:
            break

    if not success or not response or not response.text:
        print("Error: Gemini API failed to return text after trying all models and retries.")
        raise RuntimeError("Failed to generate report text from Gemini API")

    try:
        report_content = response.text.strip()
        # LLMがMarkdownコードブロックで囲んだ場合のクリーンアップ
        if report_content.startswith("```markdown"):
            report_content = report_content[len("```markdown"):]
        elif report_content.startswith("```"):
            report_content = report_content[3:]
        if report_content.endswith("```"):
            report_content = report_content[:-3]

        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content.strip())
        print(f"Generated {filename} successfully using Gemini API with Google Search Grounding.")

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        print(f"Falling back: keeping the previous {filename} as-is.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate daily competitive report using Gemini API")
    parser.add_argument("--mode", choices=["within_2km", "no_limit"], default="within_2km", help="Generation mode")
    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting report generation (mode: {args.mode})...")
    generate_report(args.mode)
