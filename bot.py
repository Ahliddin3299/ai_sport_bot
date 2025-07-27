import asyncio
import re
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient
from googletrans import Translator

# Telegram API ma'lumotlari
api_id = 21630422
api_hash = 'f1bb01a1ad8fada00c9656a5956b3b64'
phone = '+998336653299'
channel = '@futbolahlii'

# Google Translate
translator = Translator()

def translate_to_uzbek(text):
    try:
        translated = translator.translate(text, dest='uz')
        return translated.text
    except Exception as e:
        print(f"[!] Tarjima xatosi: {e}")
        return text

# Rasm URL ni sahifadan topish
def get_image_url(soup):
    img = soup.find('meta', property='og:image')
    if img and img.get('content'):
        return img['content']
    return None

# Saytlar roʻyxati (eurosport o‘chirildi)
sites = [
    'https://www.uefa.com/uefachampionsleague/news/',
    'https://www.fifa.com/fifaplus/en/news',
    'https://www.marca.com/en/football.html',
    'https://www.tribuna.uz/news/category/world'
]

# Har bir sayt uchun maxsus yangiliklarni olish funksiyasi
def get_articles_from_url(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        articles = []

        if 'uefa.com' in url:
            for item in soup.select('a[data-testid="article-link"]'):
                title = item.text.strip()
                link = 'https://www.uefa.com' + item.get('href')
                articles.append((title, link))

        elif 'tribuna.uz' in url:
            for item in soup.select('.news-item'): 
                a = item.find('a')
                if a:
                    title = a.text.strip()
                    link = 'https://www.tribuna.uz' + a.get('href')
                    articles.append((title, link))

        elif 'fifa.com' in url:
            for item in soup.select('a.card'):
                title = item.get('aria-label') or item.text.strip()
                link = 'https://www.fifa.com' + item.get('href')
                articles.append((title, link))

        elif 'marca.com' in url:
            for item in soup.select('li.ue-c-cover-content__headline-group > a'):
                title = item.text.strip()
                link = item.get('href')
                if not link.startswith('http'):
                    link = 'https://www.marca.com' + link
                articles.append((title, link))

        return articles[:5]  # har saytdan 5 ta yangilik

    except Exception as e:
        print(f"[!] Error fetching from {url}: {e}")
        return []

# Yangilik matnini olish
def get_full_article(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        paras = soup.find_all('p')
        text = '\n'.join(p.get_text() for p in paras if len(p.get_text()) > 40)
        return text.strip(), get_image_url(soup)
    except Exception as e:
        print(f"[!] Error loading article {url}: {e}")
        return '', None

# Asosiy ishchi funksiya
async def main():
    client = TelegramClient('ai_sport_bot_session', api_id, api_hash)
    await client.start(phone=phone)

    for site in sites:
        articles = get_articles_from_url(site)
        for title, link in articles:
            text, image_url = get_full_article(link)
            if not text:
                continue

            translated_text = translate_to_uzbek(text)

            message = f"<b>{translate_to_uzbek(title)}</b>\n\n{translated_text}\n\n<a href='{link}'>Manba: {link}</a>\n\n<b>@futbolahlii</b> kanali uchun maxsus"

            try:
                if image_url:
                    await client.send_file(channel, file=image_url, caption=message, parse_mode='html')
                else:
                    await client.send_message(channel, message, parse_mode='html')
                await asyncio.sleep(5)  # Antiban delay
            except Exception as e:
                print(f"[!] Failed to send message: {e}")

    await client.disconnect()

import schedule
import time

def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    schedule.every(10).minutes.do(run_bot)

    print("⏳ Bot ishga tushdi va har 10 daqiqada yangiliklarni tekshiradi...")
    while True:
        schedule.run_pending()
        time.sleep(1)
