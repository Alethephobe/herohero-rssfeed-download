#!/usr/bin/env python3
from datetime import datetime
import os
import requests
import sys
import xml.etree.ElementTree as ET

# USAGE: herohero-downloader.py <https://herohero.co/services/functions/rss-feed>

feed_uri = sys.argv[1]
if not feed_uri.startswith("https://herohero.co"):
  raise Exception("HeroHero feed URI required")

response = requests.get(feed_uri)
root_node = ET.fromstring(response.content)

download_dir = root_node.find(".//channel/title").text
if not os.path.exists(download_dir):
  os.mkdir(download_dir)

def download_file(filename, url):
  destination = f"./{download_dir}/{filename}"
  if os.path.exists(destination):
    print(f"Soubor {filename} již existuje, přeskakuji...")
    return destination

  print(f"Stahuji {filename}...")
  response = requests.get(url, stream=True)
  total_size = int(response.headers.get('content-length', 0))
  downloaded = 0
  
  with open(destination, 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024): # 1MB chunks
      if chunk:
        f.write(chunk)
        downloaded += len(chunk)
        # Zobrazení průběhu stahování
        percent = int(100 * downloaded / total_size) if total_size > 0 else 0
        sys.stdout.write(f"\r{percent}% staženo ({downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB)")
        sys.stdout.flush()
  
  print(f"\nStahování souboru {filename} dokončeno!")
  return destination

def meta_atributes(item):
  data = {}
  pubDate = item.find("pubDate").text
  released_date = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
  
  # Získání titulku z popisu - první řádek do první tečky
  desc_text = item.find("description").text
  title_line = desc_text.splitlines()[0].strip() if desc_text and '\n' in desc_text else desc_text
  title = title_line.split(".")[0] if title_line and '.' in title_line else title_line
  
  data["date"] = released_date
  data["title"] = title
  data["description"] = desc_text
  data["guid"] = item.find("guid").text

  return data

print(f"Zpracovávám RSS feed pro {download_dir}...")
items = root_node.findall(".//item")
list.reverse(items)
n = 1
total_items = len(items)

for item in items:
  try:
    print(f"\nZpracovávám položku {n} z {total_items}")
    id = item.find("guid").text
    data = meta_atributes(item)
    
    # Kontrola, zda položka obsahuje enclosure (odkaz na soubor)
    enclosure = item.find("enclosure")
    if enclosure is None:
      print(f"Položka {n} neobsahuje odkaz na soubor, přeskakuji...")
      n += 1
      continue
    
    url = enclosure.attrib["url"]
    content_type = enclosure.attrib.get("type", "")
    
    # Určení přípony souboru
    if "video" in content_type:
      if "mp4" in content_type:
        ext = "mp4"
      elif "webm" in content_type:
        ext = "webm"
      else:
        ext = "mp4"  # Výchozí video formát
    else:
      # Pokus o získání přípony z URL
      ext = url.split(".")[-1] if "." in url else "mp4"
    
    # Vytvoření bezpečného názvu souboru
    safe_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in data["title"]])
    filename = f"{data['date'].strftime('%Y-%m-%d')} {n:03d} - {safe_title}.{ext}"
    
    # Stažení souboru
    file = download_file(filename, url)
    n += 1
  except Exception as e:
    print(f"Chyba při zpracování položky {n}: {e}")
    n += 1

print(f"\nStahování dokončeno! Všechny soubory byly uloženy do složky: {download_dir}")
