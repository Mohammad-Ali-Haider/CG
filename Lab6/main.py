import sys
import time
import math
import pygame as pg

# ---------------------------
# Utility: safe pixel plotter
# ---------------------------
def set_px(surf, x, y, color):
    if 0 <= x < surf.get_width() and 0 <= y < surf.get_height():
        surf.set_at((x, y), color)

# ---------------------------------
# 8-way symmetry point plot helper
# ---------------------------------
def plot8(surf, cx, cy, x, y, color):
    set_px(surf, cx + x, cy + y, color)
    set_px(surf, cx - x, cy + y, color)
    set_px(surf, cx + x, cy - y, color)
    set_px(surf, cx - x, cy - y, color)
    set_px(surf, cx + y, cy + x, color)
    set_px(surf, cx - y, cy + x, color)
    set_px(surf, cx + y, cy - x, color)
    set_px(surf, cx - y, cy - x, color)

# ----------------------------------------
# Midpoint Circle (integer arithmetic)
# d0 = 1 - r; if d < 0 -> E step; else SE
# ----------------------------------------
def draw_circle_midpoint(surf, cx, cy, r, color):
    x, y = 0, r
    d = 1 - r
    plotted = 0

    while x <= y:
        # plot 8-fold symmetric points
        plot8(surf, cx, cy, x, y, color)
        plotted += 8 if x != 0 and x != y else (4 if x == 0 or x == y else 8)

        if d < 0:
            d += 2 * x + 3           # move E
        else:
            d += 2 * (x - y) + 5     # move SE
            y -= 1
        x += 1
    return plotted

# -----------------------------------------------------------
# Bresenham Circle (classic 3 - 2r form, all integer math)
# decision = 3 - 2r; if < 0 -> E; else SE
# -----------------------------------------------------------
def draw_circle_bresenham(surf, cx, cy, r, color):
    x, y = 0, r
    d = 3 - 2 * r
    plotted = 0

    while x <= y:
        plot8(surf, cx, cy, x, y, color)
        plotted += 8 if x != 0 and x != y else (4 if x == 0 or x == y else 8)

        if d < 0:
            d += 4 * x + 6           # move E
        else:
            d += 4 * (x - y) + 10    # move SE
            y -= 1
        x += 1
    return plotted

# -------------------
# Text rendering HUD
# -------------------
def blit_text(screen, text, pos, font, color=(20, 20, 20)):
    s = font.render(text, True, color)
    screen.blit(s, pos)

def main():
    pg.init()
    W, H = 1000, 650
    screen = pg.display.set_mode((W, H))
    pg.display.set_caption("Midpoint vs Bresenham – Circle Drawing (pygame-ce)")
    clock = pg.time.Clock()
    font = pg.font.Font(None, 26)
    big_font = pg.font.Font(None, 32)

    BG = (245, 245, 245)
    RED = (220, 60, 60)      # Midpoint
    BLUE = (50, 90, 210)     # Bresenham
    GRAY = (120, 120, 120)
    GREEN = (30, 140, 60)

    center = None
    radius = 0
    dragging = False
    results = None  # (r, t_mid, t_bre, n_mid, n_bre)

    def reset():
        nonlocal center, radius, dragging, results
        center = None
        radius = 0
        dragging = False
        results = None
        screen.fill(BG)

    reset()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_SPACE:
                    reset()
                elif event.key == pg.K_s:
                    # Save screenshot
                    ts = time.strftime("%Y%m%d-%H%M%S")
                    fname = f"circle_compare_{ts}.png"
                    pg.image.save(screen, fname)
                    # simple toast
                    pg.draw.rect(screen, (255, 255, 255), (10, H-40, 320, 30))
                    blit_text(screen, f"Saved: {fname}", (16, H-36), font, GREEN)
                    pg.display.flip()
                    # brief pause for visibility
                    pg.time.delay(500)

            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                center = event.pos
                radius = 0
                dragging = True
                screen.fill(BG)
            elif event.type == pg.MOUSEMOTION and dragging:
                # preview circle (geometric)
                screen.fill(BG)
                mx, my = event.pos
                radius = int(round(math.hypot(mx - center[0], my - center[1])))
                # simple preview using pg.draw.circle for guide only
                pg.draw.circle(screen, GRAY, center, radius, 1)
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1 and dragging:
                dragging = False
                if radius <= 0:
                    continue

                # Draw both algorithms on fresh buffer to compare
                screen.fill(BG)

                # Midpoint timing
                t0 = time.perf_counter()
                n_mid = draw_circle_midpoint(screen, center[0], center[1], radius, RED)
                t_mid = (time.perf_counter() - t0) * 1000.0  # ms

                # Bresenham timing
                t0 = time.perf_counter()
                n_bre = draw_circle_bresenham(screen, center[0], center[1], radius, BLUE)
                t_bre = (time.perf_counter() - t0) * 1000.0  # ms

                results = (radius, t_mid, t_bre, n_mid, n_bre)

        # HUD
        # Top header
        blit_text(screen, "Midpoint (red) vs Bresenham (blue) — Click & drag to draw. SPACE: reset, S: save, ESC: quit",
                  (12, 10), big_font, (15, 15, 15))

        # Live preview overlay
        if dragging and center is not None:
            cx, cy = center
            pg.draw.line(screen, (0, 0, 0), (cx, cy), pg.mouse.get_pos(), 1)
            blit_text(screen, f"Center: {center}  Radius: {radius}", (12, 50), font)

        # Results after drawing
        if results:
            r, t_mid, t_bre, n_mid, n_bre = results
            y = 50
            blit_text(screen, f"Center: {center}  Radius: {r}", (12, y), font); y += 26
            blit_text(screen, f"Midpoint:   {t_mid:.3f} ms, pixels plotted: {n_mid}", (12, y), font, RED); y += 26
            blit_text(screen, f"Bresenham:  {t_bre:.3f} ms, pixels plotted: {n_bre}", (12, y), font, BLUE); y += 26

            # Simple comparison verdict
            faster = "Midpoint" if t_mid < t_bre else ("Bresenham" if t_bre < t_mid else "Tie")
            blit_text(screen, f"Faster this run: {faster}", (12, y), font, GREEN)

        pg.display.flip()
        clock.tick(120)

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
