import os
import json
import requests
from bs4 import BeautifulSoup
import re

def scrape_ikari_stores():
    url = "https://www.ikarisuper.com/info/store/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch store page: {response.status_code}")
        return {}
        
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    stores_info = {}
    
    # 1. 主要店舗の抽出 (section.store_detail)
    major_sections = soup.find_all("section", class_="store_detail")
    for sec in major_sections:
        name = ""
        all_as = sec.find_all("a", href=re.compile(r"info/author/"))
        for a in all_as:
            t = a.text.strip()
            if t and t != "詳細を見る":
                name = t
                break
        
        if not name:
            continue
            
        img_tag = sec.find("img")
        img_url = img_tag["src"] if img_tag else ""
        if img_url and img_url.startswith("/"):
            img_url = "https://www.ikarisuper.com" + img_url
            
        address = ""
        phone = ""
        parking = "なし"
        hours = ""
        
        dl = sec.find("dl")
        if dl:
            dts = [dt.text.strip() for dt in dl.find_all("dt")]
            dds = [dd.text.strip() for dd in dl.find_all("dd")]
            details = dict(zip(dts, dds))
            address = details.get("所在地", "")
            phone = details.get("電話番号", "")
            parking = details.get("駐車場", "なし")
            hours = details.get("営業時間", "")
            
        if name not in stores_info or (stores_info[name]["image_url"] == "" and img_url != ""):
            stores_info[name] = {
                "image_url": img_url,
                "address": address,
                "phone": phone,
                "parking": parking,
                "hours": hours
            }

    # 2. 一般店舗の抽出 (article タグ)
    # id="contents" や class="pc_none" は除く
    articles = soup.find_all("article")
    for art in articles:
        classes = art.get("class", [])
        art_id = art.get("id", "")
        
        if "pc_none" in classes or art_id == "contents":
            continue
            
        name = ""
        all_as = art.find_all("a", href=re.compile(r"info/author/"))
        for a in all_as:
            t = a.text.strip()
            if t and t != "詳細を見る":
                name = t
                break
                
        if not name:
            continue
            
        img_tag = art.find("img")
        img_url = img_tag["src"] if img_tag else ""
        if img_url and img_url.startswith("/"):
            img_url = "https://www.ikarisuper.com" + img_url
            
        address = ""
        phone = ""
        parking = "なし"
        hours = ""
        
        dl = art.find("dl")
        if dl:
            dts = [dt.text.strip() for dt in dl.find_all("dt")]
            dds = [dd.text.strip() for dd in dl.find_all("dd")]
            details = dict(zip(dts, dds))
            address = details.get("所在地", "")
            phone = details.get("電話番号", "")
            parking = details.get("駐車場", "なし")
            hours = details.get("営業時間", "")
        else:
            addr_tag = art.find("p", class_="mgn_t5")
            if addr_tag:
                address = addr_tag.text.strip()
                
            p_tags = art.find_all("p")
            for p in p_tags:
                text = p.text.strip()
                if text.startswith("TEL"):
                    phone = text.replace("TEL", "").replace(":", "").replace("：", "").strip()
                elif "営業時間" in text:
                    hours = text.replace("営業時間", "").replace(":", "").replace("：", "").strip()
                elif "駐車場" in text:
                    parking = text.replace("駐車場", "").replace(":", "").replace("：", "").strip()
                    
        if name not in stores_info or (stores_info[name]["image_url"] == "" and img_url != ""):
            stores_info[name] = {
                "image_url": img_url,
                "address": address,
                "phone": phone,
                "parking": parking,
                "hours": hours
            }
            
    return stores_info

def clean_store_name(name):
    """
    店舗名を正規化して比較しやすくする。
    例: 'いかり神戸三宮店' -> '神戸三宮'
        '芦屋店' -> '芦屋'
    """
    n = name.strip()
    n = n.replace("いかり", "").replace("スーパー", "").replace("（本店）", "").replace("(本店)", "")
    if n.endswith("店") and n not in ["ラ・グルメゾン", "ライクスホール"]:
        n = n[:-1]
    return n.strip()

def update_db():
    db_path = "stores_db.json"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return
        
    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)
        
    web_stores = scrape_ikari_stores()
    print(f"Scraped {len(web_stores)} unique stores from website.")
    
    ikari_db = db_data.get("ikari_stores", {})
    updated_count = 0
    
    for db_name, db_info in list(ikari_db.items()):
        matched_web_info = None
        norm_db = clean_store_name(db_name)
        
        for web_name, web_info in web_stores.items():
            if not web_name:
                continue
                
            norm_web = clean_store_name(web_name)
            if norm_web == norm_db:
                matched_web_info = web_info
                break
                    
        if matched_web_info:
            # coordinates (coords) は絶対に変更しない！
            # 画像URLの追加
            db_info["image_url"] = matched_web_info["image_url"]
            
            # 住所情報
            web_addr = matched_web_info["address"]
            if web_addr:
                # Web側の住所に都道府県名が抜けていれば補完
                if not (web_addr.startswith("兵庫県") or web_addr.startswith("大阪府") or web_addr.startswith("京都府")):
                    if any(x in db_name for x in ["芦屋", "神戸", "西宮", "宝塚", "尼崎", "伊丹", "有野", "六甲", "御影", "岡本", "逆瀬川", "塚口", "夙川", "門戸", "甲子園", "甲陽園"]):
                        web_addr = "兵庫県" + web_addr
                    elif any(x in db_name for x in ["豊中", "箕面", "王子", "高槻", "大阪", "なんば"]):
                        web_addr = "大阪府" + web_addr
                    elif "常盤" in db_name:
                        web_addr = "京都府" + web_addr
                db_info["address"] = web_addr
                
            if matched_web_info["phone"]:
                db_info["phone"] = matched_web_info["phone"]
            if matched_web_info["parking"]:
                db_info["parking"] = matched_web_info["parking"]
            if matched_web_info["hours"]:
                db_info["hours"] = matched_web_info["hours"]
                
            updated_count += 1
        else:
            print(f"No match found for DB store: {db_name}")
            
    # 書き戻し
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully updated {updated_count} stores in stores_db.json.")

if __name__ == "__main__":
    update_db()
