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

    client = genai.Client(api_key=api_key)
    today = datetime.today().strftime("%Y年%m月%d日")

    # Google検索グラウンディングを有効にしたツール設定
    google_search_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    prompt = f"""あなたは「いかりスーパーマーケット」（兵庫県・大阪府を中心に展開する高級スーパー）の経営戦略室に所属する競合分析アナリストです。
本日は{today}です。

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

検索結果を踏まえ、いかりスーパーの経営判断・経営戦略に直接役立つ競合分析レポートを作成してください。

【絶対に守るべきルール】
1. レポートに含める情報は「{today}時点で最新かつ有効な情報」のみとすること。
2. 2025年以前の過去の出店情報や終了済みのイベント情報は一切記載しないこと。
3. 「詳細」テーブルの「時期」列には、2026年以降の未来または直近の日付のみを記載すること。
4. ニュースから最新の競合情報が十分に見つからない場合でも、過去のデータで埋めることは絶対に禁止。代わりに「現時点で確認できる最新情報は限定的」と正直に記載すること。
5. 参照ソースには、実際に検索で見つけたニュースのタイトルとURLのみを記載すること。架空のURLを生成しないこと。
6. コードブロック(```)は使わず、直接Markdownテキストのみ出力すること。

【必須フォーマット】（以下の見出し構成を完全に守ること）

## a) 【結論】
*   (経営判断に直結する結論を3〜5点。具体的な競合名・エリア・時期を含めること)

## b) 【詳細】
| エリア | 競合店舗名 | 時期 | 状態 | 影響レベル | 詳細説明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| (最新のニュースから抽出した競合動向のみ) | ... | ... | ... | ... | ... |

## c) 【地図分析】
*   (出店場所に関する地理的な考察。いかりスーパーの既存店舗との位置関係を含めること)

## d) 【影響分析】
*   (いかりスーパーの具体的な店舗名を挙げて、影響を考察すること)

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
