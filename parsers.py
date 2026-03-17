from html.parser import HTMLParser

LIST_URL = "https://www.univ-chlef.dz/actualites/"
BASE_URL = "https://www.univ-chlef.dz/?p={id}"


def fetch(url: str) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


class PostParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.posts        = []
        self._in_article  = False
        self._in_title    = False
        self._in_date     = False
        self._cur         = {}
        self._depth       = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls   = attrs.get('class', '')
        href  = attrs.get('href', '')

        if tag == 'article':
            self._in_article = True
            self._cur        = {}
            self._depth      = 0

        if self._in_article:
            self._depth += 1
            if tag == 'h2' and 'entry-title' in cls:
                self._in_title = True
            if tag == 'a' and self._in_title and href:
                self._cur['url']  = href
                post_id           = href.split('p=')[-1] if 'p=' in href else ''
                self._cur['id']   = int(post_id) if post_id.isdigit() else None
            if tag == 'time' and 'entry-date' in cls:
                self._in_date     = True
                self._cur['date'] = attrs.get('datetime', '')
            if tag == 'img' and 'attachment' in cls and 'src' in attrs:
                self._cur.setdefault('image', attrs['src'])

    def handle_data(self, data):
        if self._in_title:
            self._cur['title'] = self._cur.get('title', '') + data.strip()
        if self._in_date and not self._cur.get('date'):
            self._cur['date'] = data.strip()

    def handle_endtag(self, tag):
        if tag == 'h2':
            self._in_title = False
        if tag == 'time':
            self._in_date = False
        if self._in_article:
            self._depth -= 1
            if tag == 'article' and self._depth <= 0:
                self._in_article = False
                if self._cur.get('title'):
                    self.posts.append(self._cur)
                self._cur = {}


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.pdf_links  = []
        self.images     = []
        self._in_content = False
        self._in_p       = False
        self._cur_text   = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls   = attrs.get('class', '')

        if tag == 'div' and 'entry-content' in cls:
            self._in_content = True

        if self._in_content:
            if tag == 'p':
                self._in_p    = True
                self._cur_text = ''
            if tag == 'a':
                href = attrs.get('href', '')
                if href.lower().endswith('.pdf'):
                    self.pdf_links.append(href)
            if tag == 'img':
                src = attrs.get('src', '')
                if src:
                    self.images.append(src)

    def handle_data(self, data):
        if self._in_p:
            self._cur_text += data

    def handle_endtag(self, tag):
        if tag == 'p' and self._in_p:
            text = self._cur_text.strip()
            if text:
                self.paragraphs.append(text)
            self._in_p    = False
            self._cur_text = ''
        if tag == 'div' and self._in_content:
            self._in_content = False
