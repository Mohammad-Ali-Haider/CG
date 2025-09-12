import pygame as pg

GAMERES = (GAMEWIDTH, GAMEHEIGHT) = (100, 100)

class App:
    def __init__(self):
        pg.init()

        display_info = pg.display.Info()
        self.width = display_info.current_w
        self.height = display_info.current_h
        self.screen = pg.display.set_mode((self.width, self.height), pg.FULLSCREEN)
        pg.display.set_caption("2D Line Drawing Algorithm")

        self.clock = pg.time.Clock()
        self.running = True
        self.fps = 60

    def draw(self, entities):
        self.screen.fill((0, 0, 0))

        for entity in entities:
            entity.draw(self.screen)

        pg.display.flip()

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            

    def run(self):
        while self.running:
            lines = [Line(10, 20, 50, 50, (255, 0, 0))]

            self.handle_events()
            self.draw(lines)

class Line:
    def __init__(self, x1, y1, x2, y2, color):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color

    def draw(self, screen):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        steps = max(abs(dx), abs(dy))

        xinc = dx/steps
        yinc = dy/steps

        x, y = self.x1, self.y1

        for k in range(0, steps):
            screen.set_at((x, y), self.color)
            x += xinc
            y += yinc


if __name__ == "__main__":
    app = App()
    app.run()

