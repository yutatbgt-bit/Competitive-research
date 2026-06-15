import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def generate_report():
    """Gemini APIのGoogle検索グラウンディング機能を使い、
    最新の競合ニュースを検索・分析してレポートを生成する"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in .env. Skipping LLM generation.")
        print("Falling back: keeping the previous competitive_report.md as-is.")
        return

    # 前回のレポートを読み込む
    previous_report = ""
    if os.path.exists("competitive_report.md"):
        try:
            with open("competitive_report.md", "r", encoding="utf-8") as f:
                previous_report = f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read previous report: {e}")

    client = genai.Client(api_key=api_key)
    today = datetime.today().strftime("%Y年%m月%d日")

    # Google検索グラウンディングを有効にしたツール設定
    google_search_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    prompt = f"""あなたは「いかりスーパーマーケット」（兵庫県・大阪府を中心に展開する高級スーパー）の経営戦略室に所属する競合分析アナリストです。
本日は{today}（調査日）です。

【あなたへの指示】
Google検索を使って、以下のキーワードに関連する最新のニュースや情報を検索してください。

検索キーワード:
- いかりスーパー 競合
- 関西 スーパー 新規出店 2026
- オーケー 関西 出店
- 阪急オアシス 新店舗 改装
- ロピア 関西 出店
- ヤマダストアー 出店
- 成城石井 関西

【前回のレポート内容】
{previous_report if previous_report else "(前回のレポートはありません)"}

【分析・判定ルール】
1. 前回のレポート（存在する場合）およびGoogle検索で得られた最新情報を比較し、前回のレポートから「更新された情報」や「新規の周辺環境の変化（新規の出店計画・改装計画・競合の新たな動きなど）」があるかどうかを判断してください。
2. 前回のレポートから情報更新がない場合（新しい出店ニュースや競合の新たな動きが検索結果から見つからない場合、あるいは前回の内容と重複している場合）、レポート全体を「更新情報無し」というテキストのみで出力してください。それ以外の見出しやフォーマットは不要です。
3. 調査日（本日：{today}）以前にすでにオープンしている店舗や、すでに終了しているイベントなど、調査日以前の過去情報は一切不要です。調査日以降（本日および未来）に発生する周辺環境の変化（これからオープン予定の店舗、これからの改装計画、本日に新しく発表された競合の動きなど）のみをレポートの対象としてください。
4. 情報更新がある場合、前回のレポート内容をそのまま引き継ぐのではなく、本日（調査日）以降に新たに発生・判明した周辺環境の変化や、前回のレポートからの差分（更新情報）のみを記載してください。
5. 参照ソースには、今回の検索で実際に見つけた新規ニュースのタイトルとURLのみを記載してください。架空のURLは禁止します。
6. コードブロック(```)は使わず、直接Markdownテキストのみ出力してください。

【情報更新がある場合の必須フォーマット】（以下の見出し構成を完全に守ること）

## a) 【結論】
*   (調査日以降の経営判断に直結する結論や、今回新たに発生した変化の要約を3〜5点。具体的な競合名・エリア・時期を含めること)

## b) 【詳細】
| エリア | 競合店舗名 | 時期 | 状態 | 影響レベル | 詳細説明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| (今回新たに確認された、調査日以降の競合動向のみ) | ... | ... | ... | ... | ... |

## c) 【地図分析】
*   (今回新しく出た出店・改装場所に関する地理的な考察。いかりスーパー既存店舗との位置関係など)

## d) 【影響分析】
*   (いかりスーパーの具体的な店舗名を挙げて、今回新たに判明した変化による影響を考察すること)

## e) 【参照ソース】
*   (実際のニュースタイトルとURL。架空のURLは禁止)
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
            ),
        )

        report_content = response.text.strip()
        # LLMがMarkdownコードブロックで囲んだ場合のクリーンアップ
        if report_content.startswith("```markdown"):
            report_content = report_content[len("```markdown"):]
        elif report_content.startswith("```"):
            report_content = report_content[3:]
        if report_content.endswith("```"):
            report_content = report_content[:-3]

        with open("competitive_report.md", "w", encoding="utf-8") as f:
            f.write(report_content.strip())
        print("Generated competitive_report.md successfully using Gemini API with Google Search.")

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        print("Falling back: keeping the previous competitive_report.md as-is.")


if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting report generation with Google Search grounding...")
    generate_report()
