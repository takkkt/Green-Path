"""Procedural landmark line art and a geometric title composition."""
import math
from theme import CHARCOAL, CYAN, FONT, TITLE, MAGENTA, SAGE, MONO
MAP_ART = {"Taj Mahal": "taj", "River": "river", "City": "city", "Glacier": "glacier", "Factory": "factory"}

def drawing_for(place):
    name = place.get("name", "").lower()
    for words, style in ((('taj',), 'taj'), (('river', 'ganga'), 'river'), (('city', 'delhi'), 'city'), (('glacier', 'himalaya'), 'glacier')):
        if any(word in name for word in words):
            return place.get("art_style") or style
    return place.get("art_style") or "factory"

def draw_landmark(canvas, location_name, point, box):
    c = canvas
    color = CHARCOAL
    name = location_name.lower()

    def line(*points, **kw):
        coords = []
        for i in range(0, len(points), 2):
            coords.extend(point(points[i], points[i+1]))
        return c.create_line(*coords, fill=color, width=2, tags="boss", **kw)

    def rect(*points):
        return c.create_rectangle(*box(*points), outline=color, width=2, tags="boss")

    if "taj" in name:
        rect(390, 61, 570, 117)
        c.create_arc(*box(420, 2, 540, 117), start=0, extent=180,
                     style="arc", outline=color, width=2, tags="boss")
        line(480, 2, 480, -3)
        for x in (352, 608):
            rect(x-7, 32, x+7, 117)
            line(x-12, 32, x, 15, x+12, 32)
            line(x-10, 69, x+10, 69)
        c.create_arc(*box(460, 78, 500, 131), start=0, extent=180,
                     style="arc", outline=color, width=2, tags="boss")
        line(460, 104, 460, 117, 500, 117, 500, 104)
        for x in (409, 439, 521, 551):
            rect(x-5, 78, x+5, 101)
    elif "ganga" in name or "river" in name:
        for y in (64, 84, 104):
            points = []
            for x in range(328, 633, 8):
                points.extend((x, y+math.sin(x/24)*5))
            line(*points, smooth=True)
        for x in (380, 480, 580):
            line(x-12, 20, x+12, 20, x+12, 60)
            line(x-12, 20, x-12, 60)
    elif "delhi" in name or "city" in name:
        for x, h in ((345, 53), (390, 96), (440, 70), (495, 110), (550, 85), (600, 60)):
            rect(x, 120-h, x+28, 120)
            for y in range(132-h, 114, 16):
                line(x+7, y, x+21, y)
    elif "glacier" in name or "himalaya" in name:
        line(315, 120, 414, 12, 490, 120, 545, 28, 645, 120)
        line(384, 45, 414, 58, 439, 48)
        line(522, 58, 545, 72, 568, 58)
        line(414, 58, 396, 92, 418, 112)
    else:
        rect(380, 58, 580, 120)
        for x in (400, 470, 540):
            rect(x, 18, x+18, 58)
    line(310, 121, 650, 121)
    return c.create_oval(*box(471, 117, 489, 135), fill=MAGENTA, outline="", tags="boss")


def draw_login_hero(canvas, width):
    canvas.delete("all")
    size = min(72, max(52, round(width*.16)))
    x = width - 133
    canvas.create_oval(x, 11, x+118, 129, fill=MAGENTA, outline="", tags="title_circle")
    canvas.create_rectangle(x+22, 145, x+118, 241, fill=CYAN, outline="", tags="title_square")
    canvas.create_polygon(x-52, 241, x+4, 143, x+60, 241, fill=SAGE, outline=CHARCOAL, width=2, tags="title_triangle")
    canvas.create_text(0, -6, anchor="nw", text="green", fill=CHARCOAL, font=(TITLE, size, "bold"))
    canvas.create_text(0, 75, anchor="nw", text="path", fill=CHARCOAL, font=(TITLE, size, "bold"))
    canvas.create_line(2, 183, x-67, 183, fill=CHARCOAL, width=2)
    canvas.create_text(2, 200, anchor="nw", text="four moves.\none pair of lungs.", fill=CHARCOAL,
                       font=(FONT, 14), justify="left")
    canvas.create_text(2, 263, anchor="nw", text="01 / AGRA   02 / GANGA   03 / DELHI   04 / GANGOTRI", fill=CHARCOAL, font=(MONO, 8))
