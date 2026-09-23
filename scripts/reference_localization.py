"""Serialize a reference view using canonical bilingual copy; fail on missing copy."""
import html
from html.parser import HTMLParser


class LocalizedHTML(HTMLParser):
    def __init__(self,messages,locale):
        super().__init__(convert_charrefs=True)
        self.locale=locale
        self.copy={v['cs']:v[locale] for v in messages.values()}
        self.parts=[]
        self.missing=set()

    def translate(self,value):
        trimmed=value.strip()
        if not trimmed:
            return value
        if trimmed not in self.copy:
            self.missing.add(trimmed)
            return value
        return value.replace(trimmed,self.copy[trimmed],1)

    def handle_decl(self,decl):
        self.parts.append('<!'+decl+'>')

    def handle_starttag(self,tag,attrs):
        translated=[]
        for key,value in attrs:
            if key=='lang':value=self.locale
            if key in {'aria-label','data-help','placeholder','title','value','data-demo-explanation'} and value:
                value=self.translate(value)
            translated.append(key if value is None else key+'="'+html.escape(value,quote=True)+'"')
        self.parts.append('<'+tag+(' '+' '.join(translated) if translated else '')+'>')

    def handle_endtag(self,tag):
        self.parts.append('</'+tag+'>')

    def handle_data(self,data):
        self.parts.append(html.escape(self.translate(data),quote=False))

    def handle_comment(self,data):
        self.parts.append('<!--'+data+'-->')


def localize(source,messages,locale):
    parser=LocalizedHTML(messages,locale);parser.feed(source);parser.close()
    if parser.missing:
        raise ValueError('Unregistered UI copy: '+repr(sorted(parser.missing)))
    return ''.join(parser.parts)
