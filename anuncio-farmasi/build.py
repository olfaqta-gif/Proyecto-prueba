import base64, re
s = open('anuncio.src.html').read()
def inline(m):
    data = base64.b64encode(open(m.group(1), 'rb').read()).decode()
    return f'src="data:image/jpeg;base64,{data}"'
s = s.replace('/*FONTS*/', open('fonts/fonts.css').read())
open('anuncio.html', 'w').write(re.sub(r'src="(img/[^"]+)"', inline, s))
