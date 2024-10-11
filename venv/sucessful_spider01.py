import re
import requests
from bs4 import BeautifulSoup
import pymysql.cursors

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='lvdong0603',
                             database='spider2202_douban',
                             cursorclass=pymysql.cursors.DictCursor)

h = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "cookie":"bid=o3UZllaLmpQ; _pk_id.100001.4cf6=f614993d69362cf0.1725628432.; __utmz=30149280.1725628432.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmz=223695111.1725628432.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __yadk_uid=iA9du0IvGcqyMbWIMJwF3UXjWaXsWoi7; _pk_ses.100001.4cf6=1; __utma=30149280.1528143641.1725628432.1726793920.1727399752.7; __utmb=30149280.0.10.1727399752; __utmc=30149280; __utma=223695111.964260492.1725628432.1726793920.1727399752.7; __utmc=223695111; __utmt=1; __utmb=223695111.1.10.1727399752; ap_v=0,6.0"
}
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}
# proxies = {
# "http": "http://183.234.215.11:8443",
# "https": "http://183.234.215.11:8443"
# }
base_url = "https://movie.douban.com/top250"
page_start = 0

try:
    while True:
        url = f"{base_url}?start={page_start}"
        req = requests.get(url, headers=h,proxies=proxies)
        req.encoding = 'utf-8'

        # 使用 bs4 解析页面
        soup = BeautifulSoup(req.content.decode(), 'html.parser')
        item = soup.find_all("div", class_="item")

        if not item:
            break
        with connection.cursor() as cursor:
            for items in item:
                pic_div = items.find("div", class_="pic")
                img = pic_div.a.img
                name = img['alt'].replace('&nbsp;', ' ')
                url = img['src']
                info_div = items.find("div", class_="info")
                hd_div = items.find("div", class_="hd")
                title_span = items.find("span", class_="title")
                other_span = items.find("span", class_="other")
                playable_span = items.find("span", class_="playable")
                title = title_span.text.strip().replace('&nbsp;', ' ') if title_span else ""
                other = other_span.text.strip().replace('&nbsp;', ' ') if other_span else ""
                playable = playable_span.text.strip().replace('&nbsp;', ' ') if playable_span else ""
                bd_div = items.find("div", class_="bd")
                people_p = bd_div.find('p')
                text = people_p.text.strip().replace('&nbsp;', ' ') if people_p else ""
                parts = text.split('\n')
                director = None
                actors = None
                year = None
                country = None
                genre = None
                if len(parts) > 0:
                    director_and_actors = parts[0].split('主演:')
                    if len(director_and_actors) > 0:
                        director = director_and_actors[0].replace('导演:', '').strip()
                    if len(director_and_actors) > 1:
                        actors = director_and_actors[1].strip()
                if len(parts) > 1:
                    movie_info = parts[1].split('/')
                    if len(movie_info) > 0:
                        year_match = re.search(r'\d{4}', movie_info[0])
                        year = int(year_match.group()) if year_match else None
                    if len(movie_info) > 1:
                        country = movie_info[1].strip()
                    if len(movie_info) > 2:
                        genre = movie_info[2].strip()
                star_div = items.find("div", class_="star")
                rating_num_span = items.find("span", class_="rating_num")
                span_span = items.find("span")
                quote_p = items.find("p", class_="quote")
                inq_span = items.find("span", class_="inq")
                rating_num = rating_num_span.text.strip().replace('&nbsp;', ' ') if rating_num_span else ""
                people = span_span.text.strip().replace('&nbsp;', ' ') if span_span else ""
                comment = people  # Assuming comment is the same as people
                inq = inq_span.text.strip().replace('&nbsp;', ' ') if inq_span else ""
                with connection.cursor() as cursor:
                    # 查询是否存在相同数据
                    cursor.execute("SELECT id FROM movie_info08 WHERE movie_name=%s AND movie_url=%s AND title=%s AND other=%s AND playable=%s AND rating_num=%s AND people=%s AND comment=%s AND inq=%s",
                                   (name, url, title, other, playable, rating_num, people, comment, inq))
                    existing_record = cursor.fetchone()
                    if existing_record:
                        print("Record already exists. Skipping insertion.")
                    else:
                        # 执行插入操作
                        sql = "INSERT INTO `movie_info08` (`movie_name`, `movie_url`, `title`, `other`, `playable`, `rating_num`, `director`, `actors`, `year`, `country`, `genre`, `people`, `comment`, `inq`) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, (name, url, title, other, playable, rating_num, director, actors, year, country, genre, people, comment, inq))
                    connection.commit()
        page_start += 25
finally:
    connection.close()