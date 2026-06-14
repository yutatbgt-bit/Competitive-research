import os
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from google import genai

load_dotenv()

def fetch_news(queries):
    all_news = []
    with DDGS() as ddgs:
        for q in queries:
            try:
                results = ddgs.news(q, region="jp-jp", safesearch="off", max_results=5)
                if results:
                    all_news.extend(results)
            except Exception as e:
                print(f"Error fetching news for '{q}': {e}")
    
    # deduplicate by url
    unique_news = {item['url']: item for item in all_news}.values()
    return list(unique_news)

def generate_report(news_data):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in .env. Skipping LLM generation.")
        print("Falling back to copying the previous report structure...")
        if os.path.exists("competitive_report_2026_06.md"):
            shutil.copy("competitive_report_2026_06.md", "competitive_report.md")
        return

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
あなたは「いかりスーパー」の競合分析アナリストです。以下の最新のウェブニュース記事を分析し、指定されたMarkdownフォーマットで競合レポートを作成してください。

【最新ニュース】
{json.dumps(news_data, ensure_ascii=False, indent=2)}

【必須フォーマット】（以下の見出し構成を完全に守り、内容は最新情報に基づき記述してください。コードブロック(\`\`\`)は使わず、直接Markdownテキストのみ出力してください）

## a) 【結論】
* (ここに結論の箇条書きを数点)

## b) 【詳細】
| エリア | 競合店舗名 | 時期 | 状態 | 影響レベル | 詳細説明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| (ニュースから抽出したテーブルデータ) | ... | ... | ... | ... | ... |

## c) 【地図分析】
* (出店場所に関する地理的な考察)

## d) 【影響分析】
* (いかりスーパーへの影響考察)

## e) 【参照ソース】
* (ニュースのタイトルとURLなど)

※注意: ニュースから新しい競合情報が見つからない場合は、一般的な関西の高級スーパー・ディスカウントスーパーの動向推測を交えて上記フォーマットを埋めてください。
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        report_content = response.text.strip()
        # Clean up markdown code blocks if the LLM wrapped it
        if report_content.startswith("```markdown"):
            report_content = report_content[11:]
        if report_content.startswith("```"):
            report_content = report_content[3:]
        if report_content.endswith("```"):
            report_content = report_content[:-3]
            
        with open("competitive_report.md", "w", encoding="utf-8") as f:
            f.write(report_content.strip())
        print("Generated competitive_report.md successfully using Gemini API.")
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # fallback
        if os.path.exists("competitive_report_2026_06.md"):
            shutil.copy("competitive_report_2026_06.md", "competitive_report.md")

if __name__ == "__main__":
    queries = [
        "ヤマダストアー 大阪 出店",
        "オーケー 関西 出店",
        "阪急オアシス",
        "いかりスーパー 競合"
    ]
    print("Fetching news...")
    news = fetch_news(queries)
    print(f"Fetched {len(news)} news items. Generating report...")
    generate_report(news)
