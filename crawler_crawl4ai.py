import asyncio
from crawl4ai import AsyncWebCrawler
import re
from crawl4ai.async_webcrawler import MIN_WORD_THRESHOLD
from crawl4ai.chunking_strategy import RegexChunking

def crawler(url='https://www.csie.ncu.edu.tw/') -> str:

    async def arun(url):
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url)
            md = result.markdown
            md = filter_markdown(md)
            return md
    
    return asyncio.run(arun(url))

def crawler_custom(url, html, screenshot):

    async def arun(url, html, screenshot):
        async with AsyncWebCrawler() as crawler:
            result = await crawler.aprocess_html(
                url=url,
                html=html,
                extracted_content=None,
                word_count_threshold=MIN_WORD_THRESHOLD,
                css_selector=None,
                screenshot=screenshot,
                verbose=False,
                is_cached=False,
                extraction_strategy=None,
                chunking_strategy=RegexChunking()
            )
            md = result.markdown
            md = filter_markdown(md)
            return md
    
    return asyncio.run(arun(url, html, screenshot))

def filter_markdown(text):
    """
    過濾Markdown文本中的連結和圖片標記,只保留純文字內容
    使用非貪婪匹配來正確處理括號
    
    參數:
        text (str): 包含Markdown格式的文本
        
    返回:
        str: 過濾後的純文字
    """
    def remove_images(text):
        while True:
            # 使用非貪婪匹配 .*? 並且明確匹配完整的圖片語法
            new_text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'\1', text)
            if new_text == text:
                break
            text = new_text
        return text
    
    def remove_links(text):
        while True:
            # 分別處理帶有標題的連結和普通連結
            new_text = re.sub(r'\[(.*?)\]\((.*?)(?:\s+".*?")?\)', r'\1', text)
            if new_text == text:
                break
            text = new_text
        return text
    
    # 順序很重要：先處理圖片，再處理連結
    text = remove_images(text)
    text = remove_links(text)
    
    # 移除參考式連結定義
    text = re.sub(r'^\[[^\]]+\]:\s*.*$', '', text, flags=re.MULTILINE)
    
    # 清理多餘空白和換行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text


if __name__ == "__main__":
   crawler()