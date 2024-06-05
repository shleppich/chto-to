import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import os

BASE_URL  = 'https://lenta.ru'
PAGE_URL = lambda page_number: f'{BASE_URL }/page/{page_number}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}

async def fetch(session, url):
    print(f"Fetching URL: {url}")
    async with session.get(url, headers=HEADERS) as response:
        return await response.text()

async def parse_article(session, url):
    try:
        print(f"Parsing article: {url}")
        html = await fetch(session, url)
        soup = BeautifulSoup(html, 'lxml')

        
        title = soup.find('h1') or soup.find('title')  
        content_elements = soup.find_all('p')
        category = soup.find('a', class_='rubric-label')  
        created_date = soup.find('time') 

        article_data = {}
        if title and content_elements:
            article_data['title'] = title.get_text(strip=True)
            article_data['content'] = " ".join(p.get_text(strip=True) for p in content_elements)
            article_data['category'] = category.get_text(strip=True) if category else "N/A"
            article_data['created_date'] = created_date['datetime'] if created_date and 'datetime' in created_date.attrs else "Unknown"
            article_data['url'] = url

            print(f"Article parsed successfully: {article_data['title']}")
        else:
            print("Missing title or content, article not parsed")

        return article_data
    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return {}

async def parse_main_page():
    async with aiohttp.ClientSession() as session:
        main_page = await fetch(session, BASE_URL)
        soup = BeautifulSoup(main_page, 'lxml')
        articles_urls = []

        
        for a in soup.select('a'):  
            href = a.get('href', '')
            if href.startswith('/'):
                href = BASE_URL + href
            if BASE_URL in href and href not in articles_urls:
                articles_urls.append(href)

        print(f"Found {len(articles_urls)} articles")
        tasks = [asyncio.create_task(parse_article(session, url)) for url in articles_urls]
        articles_data = await asyncio.gather(*tasks)

        
        articles_data = [article for article in articles_data if article]

        results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, 'articles.json')

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=4)

        print(f"Saved {len(articles_data)} articles to {file_path}")

if __name__ == '__main__':
    asyncio.run(parse_main_page())