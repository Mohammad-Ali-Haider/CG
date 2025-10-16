import pygame
import sys
from collections import deque
import time

# Initialize Pygame
pygame.init()

# Grid settings
GRID_SIZE = 20  # Size of each grid cell

# Screen dimensions (will be set properly in __init__)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
GRID_COLOR = (50, 50, 50)
BG_COLOR = (20, 20, 20)
POLYGON_COLOR = (255, 255, 255)
FILL_COLOR = (0, 255, 100)
BOUNDARY_COLOR = (255, 0, 0)
POINT_COLOR = (255, 255, 0)

# Animation settings
DELAY = 0.001  # Delay between filling each pixel (seconds)

class PolygonFiller:
    def __init__(self):
        # Get the desktop screen dimensions before creating any display
        infoObject = pygame.display.Info()
        actual_width = infoObject.current_w
        actual_height = infoObject.current_h
        
        print(f"Detected desktop resolution: {actual_width} x {actual_height}")  # Debug info
        
        # Create fullscreen display using SCALED mode for better compatibility
        self.screen = pygame.display.set_mode((actual_width, actual_height), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("Polygon Fill Algorithms Visualizer")
        self.clock = pygame.time.Clock()
        
        # Update global dimensions
        global SCREEN_WIDTH, SCREEN_HEIGHT
        SCREEN_WIDTH = actual_width
        SCREEN_HEIGHT = actual_height
        
        print(f"Display created with: {SCREEN_WIDTH} x {SCREEN_HEIGHT}")  # Debug info
        
        self.points = []  # User-defined polygon points
        self.polygon_closed = False
        self.grid_points = set()  # Filled grid points
        self.current_algorithm = None
        self.is_filling = False
        self.waiting_for_seed = False  # Waiting for user to click seed point
        self.selected_algorithm = None  # Which algorithm is waiting for seed
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
    def grid_to_screen(self, x, y):
        """Convert grid coordinates to screen coordinates"""
        return x * GRID_SIZE, y * GRID_SIZE
    
    def screen_to_grid(self, x, y):
        """Convert screen coordinates to grid coordinates"""
        return x // GRID_SIZE, y // GRID_SIZE
    
    def draw_grid(self):
        """Draw the grid"""
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))
    
    def draw_polygon(self):
        """Draw the polygon edges"""
        if len(self.points) < 2:
            return
        
        for i in range(len(self.points)):
            start = self.points[i]
            end = self.points[(i + 1) % len(self.points)] if self.polygon_closed else self.points[i + 1] if i < len(self.points) - 1 else start
            
            if start != end:
                self.draw_line_bresenham(start[0], start[1], end[0], end[1], POLYGON_COLOR)
    
    def draw_line_bresenham(self, x0, y0, x1, y1, color):
        """Draw a line using Bresenham's algorithm"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            screen_x, screen_y = self.grid_to_screen(x0, y0)
            pygame.draw.rect(self.screen, color, (screen_x, screen_y, GRID_SIZE, GRID_SIZE))
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def draw_points(self):
        """Draw the polygon vertices"""
        for point in self.points:
            screen_x, screen_y = self.grid_to_screen(point[0], point[1])
            pygame.draw.circle(self.screen, POINT_COLOR, 
                             (screen_x + GRID_SIZE // 2, screen_y + GRID_SIZE // 2), 
                             GRID_SIZE // 3)
    
    def draw_filled_cells(self):
        """Draw all filled grid cells"""
        for point in self.grid_points:
            screen_x, screen_y = self.grid_to_screen(point[0], point[1])
            pygame.draw.rect(self.screen, FILL_COLOR, (screen_x, screen_y, GRID_SIZE, GRID_SIZE))
    
    def draw_ui(self):
        """Draw UI instructions"""
        instructions = [
            "Left Click: Add point",
            "Right Click / ENTER: Close polygon",
            "1: Scanline Fill",
            "2: Flood Fill (4-connected)",
            "3: Flood Fill (8-connected)",
            "4: Boundary Fill",
            "C: Clear",
            "ESC: Exit"
        ]
        
        y_offset = 10
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (255, 255, 255))
            self.screen.blit(text, (10, y_offset))
            y_offset += 30
        
        if self.waiting_for_seed:
            seed_text = self.font.render("Click inside polygon to start filling!", True, (255, 100, 100))
            text_rect = seed_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            # Draw background for better visibility
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(self.screen, (255, 100, 100), bg_rect, 2)
            self.screen.blit(seed_text, text_rect)
        
        if self.current_algorithm:
            algo_text = self.font.render(f"Algorithm: {self.current_algorithm}", True, (255, 255, 0))
            self.screen.blit(algo_text, (SCREEN_WIDTH - 500, 10))
    
    def scanline_fill(self):
        """Scanline Fill Algorithm with animation"""
        if len(self.points) < 3:
            return
        
        self.current_algorithm = "Scanline Fill"
        self.grid_points.clear()
        
        # Find min and max y coordinates
        min_y = min(p[1] for p in self.points)
        max_y = max(p[1] for p in self.points)
        
        # Get polygon edges with proper vertex handling
        edges = []
        n = len(self.points)
        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]
            
            # Ensure p1.y <= p2.y for consistent processing
            if p1[1] > p2[1]:
                p1, p2 = p2, p1
            
            if p1[1] != p2[1]:  # Skip horizontal edges
                edges.append((p1, p2))
        
        # Process each scanline
        for y in range(min_y, max_y + 1):
            intersections = []
            
            # Find intersections with edges
            for p1, p2 in edges:
                # Check if scanline intersects this edge
                # Use < for y_max to handle vertices correctly (except when it's the top vertex)
                if p1[1] <= y < p2[1]:
                    # Calculate x intersection
                    if p2[1] != p1[1]:
                        x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                        intersections.append(x)
                elif y == p2[1] == max_y:  # Special case for topmost scanline
                    if p1[1] <= y <= p2[1]:
                        x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                        intersections.append(x)
            
            # Sort intersections and remove duplicates
            intersections.sort()
            
            # Fill between pairs of intersections
            i = 0
            while i < len(intersections) - 1:
                x_start = int(intersections[i])
                x_end = int(intersections[i + 1])
                
                for x in range(x_start, x_end + 1):
                    self.grid_points.add((x, y))
                    
                    # Animation
                    screen_x, screen_y = self.grid_to_screen(x, y)
                    pygame.draw.rect(self.screen, FILL_COLOR, (screen_x, screen_y, GRID_SIZE, GRID_SIZE))
                    pygame.display.flip()
                    time.sleep(DELAY)
                    
                    # Check for exit events
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            return
                
                i += 2
    
    def flood_fill_4(self, start_x, start_y):
        """4-connected Flood Fill with animation"""
        self.current_algorithm = "Flood Fill (4-connected)"
        self.grid_points.clear()
        
        # Check if starting point is valid
        if not self.is_inside_polygon(start_x, start_y):
            return
        
        # Calculate grid boundaries
        max_grid_x = SCREEN_WIDTH // GRID_SIZE
        max_grid_y = SCREEN_HEIGHT // GRID_SIZE
        
        queue = deque([(start_x, start_y)])
        visited = set()
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
            
            # Check bounds
            if x < 0 or x >= max_grid_x or y < 0 or y >= max_grid_y:
                continue
            
            if not self.is_inside_polygon(x, y):
                continue
            
            visited.add((x, y))
            self.grid_points.add((x, y))
            
            # Animation
            screen_x, screen_y = self.grid_to_screen(x, y)
            pygame.draw.rect(self.screen, FILL_COLOR, (screen_x, screen_y, GRID_SIZE, GRID_SIZE))
            pygame.display.flip()
            time.sleep(DELAY)
            
            # 4-connected neighbors
            neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            for nx, ny in neighbors:
                if (nx, ny) not in visited:
                    queue.append((nx, ny))
            
            # Check for exit events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return
    
    def flood_fill_8(self, start_x, start_y):
        """8-connected Flood Fill with animation"""
        self.current_algorithm = "Flood Fill (8-connected)"
        self.grid_points.clear()
        
        if not self.is_inside_polygon(start_x, start_y):
            return
        
        # Calculate grid boundaries
        max_grid_x = SCREEN_WIDTH // GRID_SIZE
        max_grid_y = SCREEN_HEIGHT // GRID_SIZE
        
        queue = deque([(start_x, start_y)])
        visited = set()
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
            
            # Check bounds
            if x < 0 or x >= max_grid_x or y < 0 or y >= max_grid_y:
                continue
            
            if not self.is_inside_polygon(x, y):
                continue
            
            visited.add((x, y))
            self.grid_points.add((x, y))
            
            # Animation
            screen_x, screen_y = self.grid_to_screen(x, y)
            pygame.draw.rect(self.screen, FILL_COLOR, (screen_x, screen_y, GRID_SIZE, GRID_SIZE))
            pygame.display.flip()
            time.sleep(DELAY)
            
            # 8-connected neighbors
            neighbors = [
                (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                (x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)
            ]
            for nx, ny in neighbors:
                if (nx, ny) not in visited:
                    queue.append((nx, ny))
            
            # Check for exit events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return
    
    def boundary_fill(self, start_x, start_y):
        """Boundary Fill Algorithm with animation"""
        self.current_algorithm = "Boundary Fill"
        self.grid_points.clear()
        
        # Calculate grid boundaries
        max_grid_x = SCREEN_WIDTH // GRID_SIZE
        max_grid_y = SCREEN_HEIGHT // GRID_SIZE
        
        # Get boundary points
        boundary = set()
        n = len(self.points)
        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]
            boundary.update(self.get_line_points(p1[0], p1[1], p2[0], p2[1]))
        
        if not self.is_inside_polygon(start_x, start_y):
            return
        
        queue = deque([(start_x, start_y)])
        visited = set()
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited or (x, y) in boundary:
                continue
            
            # Check bounds
            if x < 0 or x >= max_grid_x or y < 0 or y >= max_grid_y:
                continue
            
            visited.add((x, y))
            self.grid_points.add((x, y))
            
            # Animation
            screen_x, screen_y = self.grid_to_screen(x, y)
            pygame.draw.rect(self.screen, FILL_COLOR, (screen_x, screen_y, GRID_SIZE, GRID_SIZE))
            pygame.display.flip()
            time.sleep(DELAY)
            
            # 4-connected neighbors
            neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            for nx, ny in neighbors:
                if (nx, ny) not in visited and (nx, ny) not in boundary:
                    queue.append((nx, ny))
            
            # Check for exit events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return
    
    def get_line_points(self, x0, y0, x1, y1):
        """Get all points on a line using Bresenham's algorithm"""
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            points.append((x0, y0))
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        
        return points
    
    def is_inside_polygon(self, x, y):
        """Check if a point is inside the polygon using ray casting"""
        if len(self.points) < 3:
            return False
        
        count = 0
        n = len(self.points)
        
        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]
            
            if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):
                x_intersect = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                if x < x_intersect:
                    count += 1
        
        return count % 2 == 1
    
    def get_interior_point(self):
        """Get a point inside the polygon for flood fill"""
        if len(self.points) < 3:
            return None
        
        # Use centroid as starting point
        cx = sum(p[0] for p in self.points) // len(self.points)
        cy = sum(p[1] for p in self.points) // len(self.points)
        
        if self.is_inside_polygon(cx, cy):
            return (cx, cy)
        
        # If centroid is outside, search nearby
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                if self.is_inside_polygon(cx + dx, cy + dy):
                    return (cx + dx, cy + dy)
        
        return None
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    elif event.key == pygame.K_RETURN and len(self.points) >= 3:
                        self.polygon_closed = True
                    
                    elif event.key == pygame.K_c:
                        self.points.clear()
                        self.grid_points.clear()
                        self.polygon_closed = False
                        self.current_algorithm = None
                        self.waiting_for_seed = False
                        self.selected_algorithm = None
                    
                    elif event.key == pygame.K_1 and self.polygon_closed:
                        self.scanline_fill()
                    
                    elif event.key == pygame.K_2 and self.polygon_closed:
                        self.waiting_for_seed = True
                        self.selected_algorithm = "flood_4"
                    
                    elif event.key == pygame.K_3 and self.polygon_closed:
                        self.waiting_for_seed = True
                        self.selected_algorithm = "flood_8"
                    
                    elif event.key == pygame.K_4 and self.polygon_closed:
                        self.waiting_for_seed = True
                        self.selected_algorithm = "boundary"
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        grid_x, grid_y = self.screen_to_grid(event.pos[0], event.pos[1])
                        
                        if self.waiting_for_seed:
                            # User is selecting seed point for fill algorithm
                            if self.is_inside_polygon(grid_x, grid_y):
                                self.waiting_for_seed = False
                                
                                if self.selected_algorithm == "flood_4":
                                    self.flood_fill_4(grid_x, grid_y)
                                elif self.selected_algorithm == "flood_8":
                                    self.flood_fill_8(grid_x, grid_y)
                                elif self.selected_algorithm == "boundary":
                                    self.boundary_fill(grid_x, grid_y)
                                
                                self.selected_algorithm = None
                            else:
                                # Show feedback that point is outside
                                print("Click inside the polygon!")
                        elif not self.polygon_closed:
                            # User is creating polygon
                            self.points.append((grid_x, grid_y))
                    
                    elif event.button == 3 and len(self.points) >= 3:  # Right click
                        self.polygon_closed = True
            
            # Draw everything
            self.screen.fill(BG_COLOR)
            self.draw_grid()
            self.draw_filled_cells()
            self.draw_polygon()
            self.draw_points()
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = PolygonFiller()
    app.run()