import pygame as pg
import time

GAMERES = (GAMEWIDTH, GAMEHEIGHT) = (100, 100)

class App:
    def __init__(self):
        pg.init()
        display_info = pg.display.Info()
        self.width = display_info.current_w
        self.height = display_info.current_h
        self.screen = pg.display.set_mode((self.width, self.height), pg.FULLSCREEN)
        pg.display.set_caption("DDA vs Bresenham Line Drawing")
        self.clock = pg.time.Clock()
        self.running = True
        self.fps = 60
        self.font = pg.font.Font(None, 48)
        self.points = []
        self.lines = []
        self.last_benchmark = None
        
    def draw(self, entities):
        self.screen.fill((20, 20, 20))
        
        # Draw lines
        for entity in entities:
            entity.draw(self.screen)
        
        # Draw current points
        for point in self.points:
            pg.draw.circle(self.screen, (80, 255, 80), point, 8)
        
        # Draw UI
        info = [
            "Click two points to draw lines",
            "RED = DDA | CYAN = Bresenham",
            "Press C to clear | Press ESC to exit"
        ]
        
        for i, text in enumerate(info):
            surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (20, 20 + i * 50))
        
        # Show benchmark results
        if self.last_benchmark:
            dda_time, bresenham_time, dda_pts, bresenham_pts = self.last_benchmark
            faster = "Bresenham" if bresenham_time < dda_time else "DDA"
            speedup = max(dda_time, bresenham_time) / min(dda_time, bresenham_time)
            
            perf_info = [
                f"DDA: {dda_time:.2f}ms ({dda_pts} points)",
                f"Bresenham: {bresenham_time:.2f}ms ({bresenham_pts} points)",
                f"{faster} is {speedup:.1f}x faster"
            ]
            
            for i, text in enumerate(perf_info):
                color = (255, 80, 80) if "DDA" in text else (80, 255, 255) if "Bresenham" in text else (80, 255, 80)
                surface = self.font.render(text, True, color)
                self.screen.blit(surface, (20, self.height - 150 + i * 50))
        
        pg.display.flip()
        
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
                elif event.key == pg.K_c:
                    self.lines = []
                    self.last_benchmark = None
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.points.append(event.pos)
                    if len(self.points) == 2:
                        x1, y1 = self.points[0]
                        x2, y2 = self.points[1]
                        
                        # Create both lines with slight offset
                        dda_line = Line(x1, y1, x2, y2, (255, 80, 80), "DDA")
                        bresenham_line = Line(x1, y1+3, x2, y2+3, (80, 255, 255), "Bresenham")
                        
                        # Benchmark
                        self.last_benchmark = self.benchmark_lines(x1, y1, x2, y2)
                        
                        self.lines.extend([dda_line, bresenham_line])
                        self.points = []
    
    def benchmark_lines(self, x1, y1, x2, y2):
        # Benchmark DDA
        start = time.perf_counter()
        dda_points = None
        for _ in range(1000):
            dda_points = self.dda_algorithm(x1, y1, x2, y2)
        dda_time = (time.perf_counter() - start) * 1000
        
        # Benchmark Bresenham
        start = time.perf_counter()
        bresenham_points = None
        for _ in range(1000):
            bresenham_points = self.bresenham_algorithm(x1, y1, x2, y2)
        bresenham_time = (time.perf_counter() - start) * 1000
        
        return dda_time, bresenham_time, len(dda_points), len(bresenham_points)
    
    def dda_algorithm(self, x1, y1, x2, y2):
        points = []
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return [(x1, y1)]
        
        xinc = dx / steps
        yinc = dy / steps
        x, y = x1, y1
        
        for _ in range(steps + 1):
            points.append((int(round(x)), int(round(y))))
            x += xinc
            y += yinc
        
        return points
    
    def bresenham_algorithm(self, x1, y1, x2, y2):
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            points.append((x, y))
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return points
            
    def run(self):
        while self.running:
            self.handle_events()
            self.draw(self.lines)
            self.clock.tick(self.fps)

class Line:
    def __init__(self, x1, y1, x2, y2, color, algorithm="DDA"):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color
        self.algorithm = algorithm
        
    def draw(self, screen):
        if self.algorithm == "DDA":
            self.draw_dda(screen)
        else:
            self.draw_bresenham(screen)
    
    def draw_dda(self, screen):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            if 0 <= self.x1 < screen.get_width() and 0 <= self.y1 < screen.get_height():
                screen.set_at((int(self.x1), int(self.y1)), self.color)
            return
        
        xinc = dx / steps
        yinc = dy / steps
        x, y = self.x1, self.y1
        
        for _ in range(steps + 1):
            if 0 <= int(round(x)) < screen.get_width() and 0 <= int(round(y)) < screen.get_height():
                screen.set_at((int(round(x)), int(round(y))), self.color)
            x += xinc
            y += yinc
    
    def draw_bresenham(self, screen):
        x1, y1, x2, y2 = self.x1, self.y1, self.x2, self.y2
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            if 0 <= x < screen.get_width() and 0 <= y < screen.get_height():
                screen.set_at((x, y), self.color)
            
            if x == x2 and y == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

if __name__ == "__main__":
    app = App()
    app.run()
