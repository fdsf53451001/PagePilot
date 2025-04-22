from selenium.webdriver.chrome.options import Options
from selenium import webdriver

chrome_options = Options()
chrome_options.add_argument("user-data-dir=D:\WebVoyager\selenium")
chrome_options.add_argument("disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(1024, 768)
#for selenium 4.15.2 options instead of chrome_options
#driver = webdriver.Chrome(options=chrome_options) 
driver.get("https://24h.pchome.com.tw/")

input()