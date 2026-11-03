# -*- coding: utf-8 -*-
"""
ici_doc — icitech kurumsal iç doküman motoru (PDF).
TimeLog-MCP-Kurulum şablonu stili: koyu indigo splash + numaralı bölümler,
yuvarlak kutular, koyu kod blokları, uyarı kutuları.

Kullanım:
    from ici_doc import *
    story = []
    story += [section(1,'Başlık'), sp(6), Paragraph('metin', st_body)]
    render('cikti.pdf',
           badge='ŞİRKET İÇİ TEKNİK KILAVUZ',
           title='Başlık', subtitle='Alt başlık',
           subline='PostgreSQL · ek bilgi',
           desc_lines=['satır 1','satır 2'],
           meta_line='Temmuz 2026 · Yazılım Ekibi · Hazırlayan: ...',
           header_title='Kısa Başlık', header_sub='Alt · v1.0',
           footer_left='tagline', story=story)
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, XPreformatted, PageBreak,
                                NextPageTemplate, KeepTogether, Image)
from xml.sax.saxutils import escape as _esc
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ---------- Fonts (Türkçe destekli; macOS Arial, yoksa DejaVu/Vera fallback) ----------
def _first(paths):
    for p in paths:
        if os.path.exists(p): return p
    return None

_MAC = '/System/Library/Fonts/Supplemental/'
_reg = pdfmetrics.registerFont
_normal = _first([_MAC+'Arial.ttf'])
if _normal:
    _reg(TTFont('ArialTR',        _MAC+'Arial.ttf'))
    _reg(TTFont('ArialTR-Bold',   _MAC+'Arial Bold.ttf'))
    _reg(TTFont('ArialTR-Italic', _MAC+'Arial Italic.ttf'))
    _reg(TTFont('MonoTR',         _MAC+'Courier New.ttf'))
    _reg(TTFont('MonoTR-Bold',    _MAC+'Courier New Bold.ttf'))
    _reg(TTFont('ArialUni',       _MAC+'Arial Unicode.ttf'))
    _SYM = 'ArialUni'
else:
    # fallback: DejaVu (Türkçe + çoğu simge) ya da reportlab Vera
    from reportlab.rl_config import defaultPageSize  # noqa
    import reportlab
    rlf = os.path.join(os.path.dirname(reportlab.__file__), 'fonts')
    dj = _first(['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/Library/Fonts/DejaVuSans.ttf'])
    if dj:
        base = os.path.dirname(dj)
        _reg(TTFont('ArialTR', dj))
        _reg(TTFont('ArialTR-Bold', os.path.join(base,'DejaVuSans-Bold.ttf')))
        _reg(TTFont('ArialTR-Italic', os.path.join(base,'DejaVuSans-Oblique.ttf')))
        _reg(TTFont('MonoTR', os.path.join(base,'DejaVuSansMono.ttf')))
        _reg(TTFont('MonoTR-Bold', os.path.join(base,'DejaVuSansMono-Bold.ttf')))
        _reg(TTFont('ArialUni', dj)); _SYM='ArialUni'
    else:
        _reg(TTFont('ArialTR', os.path.join(rlf,'Vera.ttf')))
        _reg(TTFont('ArialTR-Bold', os.path.join(rlf,'VeraBd.ttf')))
        _reg(TTFont('ArialTR-Italic', os.path.join(rlf,'VeraIt.ttf')))
        _reg(TTFont('MonoTR', os.path.join(rlf,'Vera.ttf')))
        _reg(TTFont('MonoTR-Bold', os.path.join(rlf,'VeraBd.ttf')))
        _reg(TTFont('ArialUni', os.path.join(rlf,'Vera.ttf'))); _SYM='ArialUni'
registerFontFamily('ArialTR', normal='ArialTR', bold='ArialTR-Bold',
                   italic='ArialTR-Italic', boldItalic='ArialTR-Bold')
registerFontFamily('MonoTR', normal='MonoTR', bold='MonoTR-Bold',
                   italic='MonoTR', boldItalic='MonoTR-Bold')

_ICON_FALLBACK = {'⚠': '▲', 'ℹ': '◉'}  # Arial Unicode'da ⚠ ve ℹ glifi yok, kutu (□) çıkıyordu
def ic(char, color=None):
    char = _ICON_FALLBACK.get(char, char)
    if color: return f'<font name="{_SYM}" color="{color}">{char}</font>'
    return f'<font name="{_SYM}">{char}</font>'

# ---------- Palette ----------
NAVY=HexColor('#1b1b4b'); INK=HexColor('#181838'); INDIGO=HexColor('#4f46e5')
INDIGO2=HexColor('#6366f1'); MUTED=HexColor('#6b7280')
LIGHTBOX=HexColor('#f5f5fb'); LIGHTBRD=HexColor('#e2e2f0')
CODEBG=HexColor('#1e1e42'); CODETXT=HexColor('#e7e7f6')
WARNBG=HexColor('#fff8e6'); WARNBRD=HexColor('#f59e0b')
GOODBG=HexColor('#eafaf0'); GOODBRD=HexColor('#16a34a'); GOOD=HexColor('#15803d')
BAD=HexColor('#b91c1c'); WHITE=HexColor('#ffffff')
BLUE=HexColor('#0369a1'); PURPLE=HexColor('#7c3aed')

PAGE_W, PAGE_H = A4
MX = 20*mm
CW = PAGE_W-2*MX  # content width

# ---------- Styles ----------
def S(name, **kw):
    base=dict(fontName='ArialTR', fontSize=9.5, leading=14, textColor=INK); base.update(kw)
    return ParagraphStyle(name, **base)
st_body=S('body'); st_muted=S('muted',textColor=MUTED,fontSize=8.8,leading=12.5)
st_h2=S('h2',fontName='ArialTR-Bold',fontSize=13.5,textColor=NAVY,leading=17)
st_h3=S('h3',fontName='ArialTR-Bold',fontSize=10.5,textColor=NAVY,leading=14)
st_lead=S('lead',fontSize=10,leading=15)
st_code=S('code',fontName='MonoTR',fontSize=8.3,leading=12.2,textColor=CODETXT)
st_badge=S('badge',fontName='ArialTR-Bold',fontSize=10,textColor=WHITE,alignment=TA_CENTER)
st_good=S('good',fontSize=9,leading=13,textColor=GOOD,fontName='ArialTR-Bold')
st_bad=S('bad',fontSize=9,leading=13,textColor=BAD,fontName='ArialTR-Bold')
st_small=S('small',fontSize=8.5,leading=12)
st_th=S('th',fontName='ArialTR-Bold',fontSize=8.3,textColor=WHITE)
st_td=S('td',fontSize=8.3,leading=11.5)
st_tdm=S('tdm',fontName='MonoTR',fontSize=8,leading=11.5)

def esc(s): return _esc(str(s))
def sp(h=6): return Spacer(1,h)

# ---------- Building blocks ----------
def section(num, title):
    badge=Table([[Paragraph(str(num),st_badge)]],colWidths=[17],rowHeights=[17])
    badge.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),INDIGO),('ROUNDEDCORNERS',[9,9,9,9]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    row=Table([[badge,Paragraph(esc(title),st_h2)]],colWidths=[24,None])
    row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    row._toc=(1,str(num),str(title))          # İçindekiler'e girer (render toc=True)
    return row

def sub(title, style=None):
    """Alt başlık (st_h3). İçindekiler'de bir önceki section()'ın altında girintili görünür."""
    p=Paragraph(title, style or st_h3)
    p._toc=(2,'',_strip_tags(title))
    return p

def _strip_tags(html):
    import re
    return re.sub(r'<[^>]+>','',html).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')

def box(flowables, fill=LIGHTBOX, brd=LIGHTBRD, pad=9):
    if not isinstance(flowables,list): flowables=[flowables]
    t=Table([[flowables]],colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),fill),('BOX',(0,0),(-1,-1),0.75,brd),
        ('ROUNDEDCORNERS',[6,6,6,6]),('LEFTPADDING',(0,0),(-1,-1),pad+2),('RIGHTPADDING',(0,0),(-1,-1),pad+2),
        ('TOPPADDING',(0,0),(-1,-1),pad),('BOTTOMPADDING',(0,0),(-1,-1),pad)]))
    return t

def _wrap_code(lines, width):
    """Uzun satırı kutu genişliğinde kaydırır (XPreformatted kendisi kaydırmaz, taşar). Devam satırı +4 girintili."""
    out=[]
    for l in lines:
        ind=len(l)-len(l.lstrip(' '))
        while len(l)>width:
            cut=max(l.rfind(c,ind+10,width) for c in ' ><,')
            cut=cut+1 if cut>ind+10 else width
            out.append(l[:cut].rstrip()); l=' '*(ind+4)+l[cut:].lstrip()
        out.append(l)
    return out

def codeblock(lines):
    if isinstance(lines,str): lines=lines.split('\n')
    width=int((CW-24)/(0.6*st_code.fontSize))  # Courier: karakter genişliği 0.6 em
    p=XPreformatted("\n".join(esc(l) for l in _wrap_code(lines, width)), st_code)
    t=Table([[p]],colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),CODEBG),('ROUNDEDCORNERS',[6,6,6,6]),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    return t

def callout(text, kind='warn'):
    if kind=='warn': fill,brd,icon=WARNBG,WARNBRD,ic('⚠','#d97706')
    elif kind=='good': fill,brd,icon=GOODBG,GOODBRD,ic('✔','#15803d')
    else: fill,brd,icon=LIGHTBOX,INDIGO,ic('ℹ','#4f46e5')
    p=Paragraph(f'<b>{icon}</b>&nbsp;&nbsp;{text}', st_small)
    t=Table([[p]],colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),fill),('LINEBEFORE',(0,0),(0,-1),3,brd),
        ('ROUNDEDCORNERS',[4,4,4,4]),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    return t

def beforeafter(title, before, after, note=None):
    inner=[Paragraph(ic('✕')+'  '+before,st_bad), Spacer(1,3), Paragraph(ic('✔')+'  '+after,st_good)]
    if note: inner += [Spacer(1,4), Paragraph(note,st_muted)]
    body=Table([[Paragraph('<b>ÖRNEK · '+esc(title)+'</b>',st_th)],[inner]],colWidths=[CW])
    body.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),INDIGO),('BACKGROUND',(0,1),(0,1),WHITE),
        ('BOX',(0,0),(-1,-1),0.75,LIGHTBRD),('ROUNDEDCORNERS',[6,6,6,6]),
        ('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),
        ('TOPPADDING',(0,0),(0,0),5),('BOTTOMPADDING',(0,0),(0,0),5),
        ('TOPPADDING',(0,1),(0,1),9),('BOTTOMPADDING',(0,1),(0,1),10)]))
    return body

def bullets(items, style=None):
    style=style or st_body
    data=[[Paragraph('•',ParagraphStyle('b',parent=style,textColor=INDIGO,fontName='ArialTR-Bold')),
           Paragraph(t,style)] for t in items]
    t=Table(data,colWidths=[12,CW-12])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),1.5),('BOTTOMPADDING',(0,0),(-1,-1),1.5)]))
    return t

def checklist(items, fill=LIGHTBOX):
    rows=[]
    for i,item in enumerate(items):
        rows.append(Paragraph(ic('☐','#4f46e5')+'&nbsp;&nbsp;'+item, st_small))
        if i<len(items)-1: rows.append(Spacer(1,4))
    return box(rows, fill=fill)

_LABELCOLOR={'BELİRTİ':BAD,'TEŞHİS':INDIGO,'DÜŞÜNCE':PURPLE,'AKSİYON':BLUE,
             'SONUÇ':GOOD,'DERS':HexColor('#b45309'),'NOT':MUTED}
def labelrow(label, html, color=None, style=None):
    style=style or st_body
    color=color or _LABELCOLOR.get(label.upper(), INDIGO)
    lab=Table([[Paragraph(label.upper(),ParagraphStyle('lc',parent=st_badge,fontSize=6.6,textColor=WHITE,leading=8))]],
              colWidths=[60],rowHeights=[13])
    lab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),color),('ROUNDEDCORNERS',[3,3,3,3]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    row=Table([[lab,Paragraph(html,style)]],colWidths=[68,CW-68])
    row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(0,0),0),('LEFTPADDING',(1,0),(1,0),4),
        ('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),1.5),('BOTTOMPADDING',(0,0),(-1,-1),1.5)]))
    return row

def story_case(code, title):
    """Vaka başlığı: küçük kod + başlık, ince alt çizgi."""
    p=Paragraph(f'<font color="#4f46e5"><b>{esc(code)}</b></font>&nbsp;&nbsp;{esc(title)}', st_h3)
    t=Table([[p]],colWidths=[CW])
    t.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,-1),1.2,INDIGO),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return t

def datatable(header, rows, widths):
    """header: list[str]; rows: list[list[flowable-or-str]]; widths: list[float fractions summing ~1]"""
    def mk(x, st):
        return x if hasattr(x,'wrap') else Paragraph(str(x), st)
    data=[[Paragraph(h,st_th) for h in header]]
    for r in rows:
        data.append([mk(c,st_td) for c in r])
    tbl=Table(data,colWidths=[CW*w for w in widths])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LIGHTBOX]),('BOX',(0,0),(-1,-1),0.75,LIGHTBRD),
        ('INNERGRID',(0,1),(-1,-1),0.4,LIGHTBRD),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5.5)]))
    return tbl

def figure(path, caption=None, width=1.0):
    """Görsel (PNG/JPG; ör. Graphviz ile çizilmiş akış şeması). width: içerik genişliğine oran; en-boy korunur.
    caption: altta soluk, ortalı açıklama."""
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(path).getSize()
    w = CW*width; h = w*ih/iw
    maxh = PAGE_H-25*mm-18*mm-40
    if h > maxh: w, h = w*maxh/h, maxh
    img = Image(path, width=w, height=h)
    if not caption: return img
    return KeepTogether([img, sp(3), Paragraph(caption, S('cap', textColor=MUTED, fontSize=8.8, leading=12.5, alignment=TA_CENTER))])

# ---------- Splash + header/footer ----------
_CFG={}
def _draw_splash(c, doc):
    g=_CFG; c.saveState()
    c.setFillColor(HexColor('#0e0e2c')); c.rect(0,0,PAGE_W,PAGE_H,stroke=0,fill=1)
    c.linearGradient(0,PAGE_H,0,0,(HexColor('#3b3ba6'),HexColor('#232370'),HexColor('#0e0e2c')),(0,0.45,1),extend=True)
    c.setFillColor(HexColor('#5b5bd0')); c.setFillAlpha(0.30)
    c.rect(PAGE_W-72*mm,PAGE_H-88*mm,72*mm,88*mm,stroke=0,fill=1); c.setFillAlpha(1)
    c.setFillColor(WHITE); c.setFont('ArialTR-Bold',30); c.drawString(MX,PAGE_H-38*mm,'icitech')
    bw=len(g['badge'])*3.0*mm+8*mm
    c.setStrokeColor(HexColor('#8b8bd8')); c.setLineWidth(1)
    c.roundRect(MX,PAGE_H-118*mm,bw,8*mm,4,stroke=1,fill=0)
    c.setFillColor(HexColor('#c7c7f0')); c.setFont('ArialTR-Bold',8.5)
    c.drawString(MX+4*mm,PAGE_H-115.3*mm,' '.join(g['badge']))
    c.setFillColor(WHITE); c.setFont('ArialTR-Bold',27); c.drawString(MX,PAGE_H-133*mm,g['title'])
    c.setFillColor(HexColor('#c9c9ee')); c.setFont('ArialTR-Bold',15); c.drawString(MX,PAGE_H-142*mm,g['subtitle'])
    y=PAGE_H-149*mm
    if g.get('subline'):
        c.setFillColor(HexColor('#8f8fd8')); c.setFont('ArialTR-Bold',9.5)
        c.drawString(MX,y,g['subline']); y-=7*mm
    c.setFillColor(HexColor('#b6b6dd')); c.setFont('ArialTR',10)
    for line in g.get('desc_lines',[]):
        c.drawString(MX,y,line); y-=5.6*mm
    y-=3*mm
    c.setFillColor(INDIGO); c.roundRect(MX,y-1.5*mm,15*mm,7*mm,3.5,stroke=0,fill=1)
    c.setFillColor(WHITE); c.setFont('ArialTR-Bold',8.5); c.drawString(MX+3.2*mm,y+0.8*mm,g.get('version','v1.0'))
    c.setFillColor(HexColor('#b6b6dd')); c.setFont('ArialTR',9); c.drawString(MX+18*mm,y+0.8*mm,g.get('meta_line',''))
    c.setStrokeColor(INDIGO2); c.setLineWidth(1.2); c.line(MX,24*mm,PAGE_W-MX,24*mm)
    c.setFillColor(HexColor('#b6b6dd')); c.setFont('ArialTR-Italic',9)
    c.drawString(MX,18*mm,g.get('splash_footer','Shape your digital future with us.'))
    c.setFont('ArialTR',9); c.drawRightString(PAGE_W-MX,18*mm,'www.icitech.com.tr')
    c.restoreState()

def _draw_content(c, doc):
    g=_CFG; c.saveState()
    c.setFillColor(NAVY); c.setFont('ArialTR-Bold',15); c.drawString(MX,PAGE_H-16*mm,'icitech')
    c.setFillColor(NAVY); c.setFont('ArialTR-Bold',8.6); c.drawRightString(PAGE_W-MX,PAGE_H-14*mm,g.get('header_title',g['title']))
    c.setFillColor(MUTED); c.setFont('ArialTR',8); c.drawRightString(PAGE_W-MX,PAGE_H-18*mm,g.get('header_sub',''))
    c.setStrokeColor(LIGHTBRD); c.setLineWidth(0.8); c.line(MX,PAGE_H-21*mm,PAGE_W-MX,PAGE_H-21*mm)
    c.line(MX,15*mm,PAGE_W-MX,15*mm)
    c.setFillColor(INDIGO); c.setFont('ArialTR-Italic',8.3); c.drawString(MX,10*mm,g.get('footer_left',''))
    c.setFillColor(MUTED); c.setFont('ArialTR',8.3); c.drawRightString(PAGE_W-MX,10*mm,f'www.icitech.com.tr  ·  {doc.page-1}')
    c.restoreState()

# ---------- İçindekiler (otomatik) ----------
st_toc1=S('toc1',fontName='ArialTR-Bold',fontSize=10.2,leading=13,textColor=NAVY)
st_toc2=S('toc2',fontSize=8.8,leading=11.5,textColor=MUTED)
st_tocp1=S('tocp1',fontName='ArialTR-Bold',fontSize=10,leading=13,textColor=INDIGO,alignment=2)
st_tocp2=S('tocp2',fontSize=8.6,leading=11.5,textColor=MUTED,alignment=2)
st_tocb=S('tocb',fontName='ArialTR-Bold',fontSize=8.6,leading=10,textColor=WHITE,alignment=TA_CENTER)

def _toc_flowables(entries, title):
    """entries: [(level, num, title, page, key)]. Modern görünüm: indigo rozet, başlık, sağda sayfa; alt başlıklar girintili."""
    out=[Paragraph(esc(title), S('toch',fontName='ArialTR-Bold',fontSize=20,leading=24,textColor=NAVY)), sp(4),
         Table([['']],colWidths=[CW],rowHeights=[3],style=TableStyle([('BACKGROUND',(0,0),(-1,-1),INDIGO),
              ('ROUNDEDCORNERS',[1.5,1.5,1.5,1.5])])), sp(14)]
    if not entries: return out
    rows=[]; styles=[('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]
    for i,(lvl,num,t,page,key) in enumerate(entries):
        link=lambda txt: f'<a href="#{key}">{txt}</a>' if key else txt
        if lvl==1:
            if num:
                badge=Table([[Paragraph(esc(num),st_tocb)]],colWidths=[max(20,7+6*len(num))],rowHeights=[18])
                badge.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),INDIGO),('ROUNDEDCORNERS',[9,9,9,9]),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),
                    ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                    ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
            else: badge=''
            rows.append([badge, Paragraph(link(esc(t)),st_toc1), Paragraph(link(str(page) if page else ''),st_tocp1)])
            r=len(rows)-1
            styles+= [('TOPPADDING',(0,r),(-1,r),9 if r else 2),('BOTTOMPADDING',(0,r),(-1,r),6)]
            if r: styles.append(('LINEABOVE',(0,r),(-1,r),0.6,LIGHTBRD))
        else:
            rows.append(['', Paragraph(link(esc(t)),st_toc2), Paragraph(link(str(page) if page else ''),st_tocp2)])
            r=len(rows)-1
            styles+= [('TOPPADDING',(0,r),(-1,r),1.5),('BOTTOMPADDING',(0,r),(-1,r),1.5),('LEFTPADDING',(1,r),(1,r),14)]
    tbl=Table(rows,colWidths=[34,CW-34-36,36],repeatRows=0)
    tbl.setStyle(TableStyle(styles))
    return out+[tbl]

class _Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        t=getattr(f,'_toc',None)
        if not t: return
        lvl,num,title=t
        key=f'toc{len(self._toc_seen)}'
        self.canv.bookmarkPage(key)
        label=f'{num}  {title}' if num else title
        last=self._toc_seen[-1][0] if self._toc_seen else 1
        self.canv.addOutlineEntry(label, key, level=0 if lvl==1 or not self._toc_seen else min(lvl-1, last))
        self._toc_seen.append((lvl,num,title,self.page-1,key))   # footer numarası = sayfa - 1 (kapak hariç)

def render(path, *, badge, title, subtitle, story, subline=None, desc_lines=None,
           version='v1.0', meta_line='', header_title=None, header_sub='',
           footer_left='', splash_footer='Shape your digital future with us.',
           toc=True, toc_title='İçindekiler'):
    """toc=True: kapaktan sonra otomatik İçindekiler sayfası (section() ve sub() başlıkları, sayfa numarası,
    tıklanabilir bağlantı + PDF yer imleri). Sayfa numaraları için belge birkaç kez derlenir."""
    import copy
    _CFG.clear(); _CFG.update(dict(badge=badge,title=title,subtitle=subtitle,subline=subline,
        desc_lines=desc_lines or [], version=version, meta_line=meta_line,
        header_title=header_title or title, header_sub=header_sub, footer_left=footer_left,
        splash_footer=splash_footer))
    def build(entries):
        doc=_Doc(path,pagesize=A4,leftMargin=MX,rightMargin=MX,topMargin=25*mm,bottomMargin=20*mm)
        doc._toc_seen=[]
        sf=Frame(0,0,PAGE_W,PAGE_H,id='splash',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        cf=Frame(MX,18*mm,CW,PAGE_H-25*mm-18*mm,id='content')
        doc.addPageTemplates([PageTemplate(id='splash',frames=[sf],onPage=_draw_splash),
                              PageTemplate(id='content',frames=[cf],onPage=_draw_content)])
        head=[NextPageTemplate('content'), PageBreak()]
        if toc: head+=_toc_flowables(entries,toc_title)+[PageBreak()]
        doc.build(head+copy.deepcopy(story))
        return doc._toc_seen
    if not toc:
        build([]); return path
    # 1. geçiş: sayfa numarasız (aynı satır sayısı, aynı yükseklik) → 2. geçiş: gerçek numaralar; sabitlenene kadar
    seen=build([])
    seen=build([(l,n,t,0,k) for l,n,t,_,k in seen])
    for _ in range(3):
        again=build(seen)
        if [x[3] for x in again]==[x[3] for x in seen]: break
        seen=again
    return path
