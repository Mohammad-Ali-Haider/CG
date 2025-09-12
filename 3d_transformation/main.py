import pygame as pg
import numpy as np
import math
import sys

def to_rad(deg): return deg * math.pi / 180.0

class CubeManipulator:
    def __init__(self):
        pg.init()

        # Always fullscreen
        display_info = pg.display.Info()
        self.width = display_info.current_w
        self.height = display_info.current_h
        self.screen = pg.display.set_mode((self.width, self.height), pg.FULLSCREEN)
        pg.display.set_caption("3D Cube Manipulator (Homogeneous)")

        self.clock = pg.time.Clock()
        self.running = True
        self.fps = 60

        # Fixed diagonal camera looking at origin
        self.camera_pos = np.array([5.0, 4.0, 5.0], dtype=np.float32)
        self.camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        # Projection settings
        self.is_orthographic = False
        self.fov = 60.0
        self.min_fov = 15.0
        self.max_fov = 120.0
        self.ortho_size = 5.0
        self.near = 0.1
        self.far = 100.0
        self.aspect_ratio = self.width / self.height

        # Cube properties
        self.cube_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)     # translation in world
        self.cube_rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32) # Euler angles (radians)
        self.cube_size = 1.0                                             # uniform scale

        # Control settings
        self.move_speed = 3.0
        self.rotation_speed = 2.0
        self.shift_held = False
        self.mouse_grabbed = False

        # Geometry in homogeneous coordinates (w = 1)
        self.cube_vertices, self.cube_edges = self.create_cube_geometry()
        self.axes = self.create_axes()

        # Fonts
        self.font = pg.font.Font(None, 32)
        self.small_font = pg.font.Font(None, 28)

    # --------------------------
    # Geometry (homogeneous)
    # --------------------------
    def create_cube_geometry(self):
        half = self.cube_size / 2.0
        verts3 = np.array([
            [-half, -half, -half],
            [ half, -half, -half],
            [ half,  half, -half],
            [-half,  half, -half],
            [-half, -half,  half],
            [ half, -half,  half],
            [ half,  half,  half],
            [-half,  half,  half],
        ], dtype=np.float32)

        # Convert to homogeneous (append w=1)
        ones = np.ones((verts3.shape[0], 1), dtype=np.float32)
        vertices = np.hstack([verts3, ones])

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top
            (0, 4), (1, 5), (2, 6), (3, 7),  # Sides
        ]
        return vertices, edges

    def create_axes(self):
        length = 2.0
        # start and end as homogeneous
        def H(v): return np.array([v[0], v[1], v[2], 1.0], dtype=np.float32)

        axes = [
            {'start': H([0, 0, 0]), 'end': H([length, 0, 0]), 'color': (255,   0,   0)},  # X
            {'start': H([0, 0, 0]), 'end': H([0, length, 0]), 'color': (  0, 255,   0)},  # Y
            {'start': H([0, 0, 0]), 'end': H([0, 0, length]), 'color': (  0,   0, 255)},  # Z
        ]
        return axes

    # --------------------------
    # Matrix builders (4x4)
    # --------------------------
    def rotation_matrix_xyz(self, angles):
        rx, ry, rz = angles

        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)

        Rx = np.array([
            [1, 0,  0, 0],
            [0, cx, -sx, 0],
            [0, sx,  cx, 0],
            [0, 0,  0, 1],
        ], dtype=np.float32)

        Ry = np.array([
            [ cy, 0, sy, 0],
            [  0, 1,  0, 0],
            [-sy, 0, cy, 0],
            [  0, 0,  0, 1],
        ], dtype=np.float32)

        Rz = np.array([
            [cz, -sz, 0, 0],
            [sz,  cz, 0, 0],
            [ 0,   0, 1, 0],
            [ 0,   0, 0, 1],
        ], dtype=np.float32)

        # Z * Y * X
        return Rz @ Ry @ Rx

    def translation_matrix(self, t):
        T = np.eye(4, dtype=np.float32)
        T[:3, 3] = t[:3]
        return T

    def scale_matrix(self, s):
        S = np.eye(4, dtype=np.float32)
        S[0, 0] = S[1, 1] = S[2, 2] = s
        return S

    def look_at(self, eye, target, up):
        # Right-handed lookAt compatible with our projection
        f = target - eye
        f = f / np.linalg.norm(f)
        r = np.cross(f, up)
        r = r / np.linalg.norm(r)
        u = np.cross(r, f)

        M = np.eye(4, dtype=np.float32)
        M[0, :3] = r
        M[1, :3] = u
        M[2, :3] = -f
        M[0, 3] = -np.dot(r, eye)
        M[1, 3] = -np.dot(u, eye)
        M[2, 3] =  np.dot(f, eye)
        return M

    def perspective(self, fov_deg, aspect, near, far):
        f = 1.0 / math.tan(to_rad(fov_deg) / 2.0)
        P = np.zeros((4, 4), dtype=np.float32)
        P[0, 0] = f / aspect
        P[1, 1] = f
        P[2, 2] = (far + near) / (near - far)
        P[2, 3] = (2.0 * far * near) / (near - far)
        P[3, 2] = -1.0
        return P

    def orthographic(self, left, right, bottom, top, near, far):
        O = np.eye(4, dtype=np.float32)
        O[0, 0] = 2.0 / (right - left)
        O[1, 1] = 2.0 / (top - bottom)
        O[2, 2] = -2.0 / (far - near)
        O[0, 3] = -(right + left) / (right - left)
        O[1, 3] = -(top + bottom) / (top - bottom)
        O[2, 3] = -(far + near) / (far - near)
        return O

    # --------------------------
    # Pipeline matrices
    # --------------------------
    def model_matrix(self):
        # S * R * T applied to column vectors on the right -> final is T * R * S for row-major draw order
        # We’re building for column-vector math (v' = M * v), so M = T * R * S
        S = self.scale_matrix(1.0)  # cube_size is baked into geometry; keep S if you want dynamic scale
        R = self.rotation_matrix_xyz(self.cube_rotation)
        T = self.translation_matrix(self.cube_pos)
        return T @ R @ S

    def view_matrix(self):
        return self.look_at(self.camera_pos, self.camera_target, self.world_up)

    def projection_matrix(self):
        if self.is_orthographic:
            left  = -self.ortho_size * self.aspect_ratio
            right =  self.ortho_size * self.aspect_ratio
            bottom = -self.ortho_size
            top    =  self.ortho_size
            return self.orthographic(left, right, bottom, top, self.near, self.far)
        else:
            return self.perspective(self.fov, self.aspect_ratio, self.near, self.far)

    # --------------------------
    # Transform & project
    # --------------------------
    def world_to_screen(self, p_world_h):
        """p_world_h is a 4D homogeneous point (x,y,z,w=1)."""
        M = self.model_matrix()
        V = self.view_matrix()
        P = self.projection_matrix()

        clip = P @ (V @ (M @ p_world_h))

        w = clip[3]
        if self.is_orthographic:
            # orthographic still gives w=1 after projection; treat like perspective divide for consistency
            if abs(w) < 1e-8:
                return None
            ndc = clip[:3] / w
        else:
            if w <= 0:  # behind the camera or on plane
                return None
            ndc = clip[:3] / w

        x_ndc, y_ndc = ndc[0], ndc[1]
        screen_x = int((x_ndc + 1.0) * 0.5 * self.width)
        screen_y = int((1.0 - y_ndc) * 0.5 * self.height)
        return (screen_x, screen_y)

    def worldline_to_screen(self, start_h, end_h):
        s = self.world_to_screen(start_h)
        e = self.world_to_screen(end_h)
        if s is None or e is None:
            return None, None
        return s, e

    # --------------------------
    # Input/event handling
    # --------------------------
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
                elif event.key in (pg.K_LSHIFT, pg.K_RSHIFT):
                    self.shift_held = True
                elif event.key == pg.K_o:
                    self.is_orthographic = not self.is_orthographic

            elif event.type == pg.KEYUP:
                if event.key in (pg.K_LSHIFT, pg.K_RSHIFT):
                    self.shift_held = False

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1 and self.shift_held:
                    if not self.mouse_grabbed:
                        pg.mouse.set_visible(False)
                        pg.event.set_grab(True)
                        self.mouse_grabbed = True

            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1 and self.mouse_grabbed:
                    pg.mouse.set_visible(True)
                    pg.event.set_grab(False)
                    self.mouse_grabbed = False

            elif event.type == pg.MOUSEWHEEL:
                if not self.is_orthographic:
                    self.fov -= event.y * 5.0
                    self.fov = max(self.min_fov, min(self.max_fov, self.fov))
                else:
                    self.ortho_size -= event.y * 0.5
                    self.ortho_size = max(1.0, min(10.0, self.ortho_size))

    def handle_input(self, dt):
        keys = pg.key.get_pressed()
        if self.shift_held and self.mouse_grabbed:
            mx, my = pg.mouse.get_rel()
            if mx or my:
                self.cube_rotation[1] += mx * self.rotation_speed * dt  # yaw
                self.cube_rotation[0] += my * self.rotation_speed * dt  # pitch
        else:
            move = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            if keys[pg.K_w]:     move[2] -= 1
            if keys[pg.K_s]:     move[2] += 1
            if keys[pg.K_a]:     move[0] -= 1
            if keys[pg.K_d]:     move[0] += 1
            if keys[pg.K_SPACE]: move[1] += 1
            if keys[pg.K_c]:     move[1] -= 1

            if np.linalg.norm(move) > 0:
                move = move / np.linalg.norm(move)
                delta = move * self.move_speed * dt

                # apply homogeneous translation
                T = self.translation_matrix(delta)
                pos_h = np.array([*self.cube_pos, 1.0], dtype=np.float32)
                new_pos_h = T @ pos_h
                self.cube_pos = new_pos_h[:3]


    # --------------------------
    # Rendering
    # --------------------------
    def render(self):
        self.screen.fill((30, 30, 40))

        # Axes (world lines)
        for axis in self.axes:
            s, e = self.worldline_to_screen(axis['start'], axis['end'])
            if s is not None and e is not None:
                pg.draw.line(self.screen, axis['color'], s, e, 3)

        # Cube
        # Transform & project each vertex (already done inside world_to_screen)
        screen_pts = []
        for v in self.cube_vertices:
            sp = self.world_to_screen(v)
            screen_pts.append(sp)

        for a, b in self.cube_edges:
            sa = screen_pts[a]
            sb = screen_pts[b]
            if sa is not None and sb is not None:
                pg.draw.line(self.screen, (255, 255, 255), sa, sb, 2)

        self.draw_ui()

        pg.display.flip()

    def draw_ui(self):
        # Instructions
        instructions = [
            "WASD + Space/C - Move cube",
            "Hold Shift + Mouse - Rotate cube",
            "Mouse Wheel - FOV/Zoom",
            "O - Toggle Orthographic/Perspective",
            "ESC - Quit",
            "",
            f"Mode: {'Orthographic' if self.is_orthographic else 'Perspective'}",
        ]
        if not self.is_orthographic:
            instructions.append(f"FOV: {self.fov:.0f}°")
        else:
            instructions.append(f"Ortho Size: {self.ortho_size:.1f}")

        y = 10
        for line in instructions:
            if line == "":
                y += 10
                continue
            color = (255, 255, 0) if line.startswith(("Mode:", "FOV:", "Ortho")) else (255, 255, 255)
            surf = self.small_font.render(line, True, color)
            self.screen.blit(surf, (10, y))
            y += 25

        # Status
        pos = self.cube_pos
        rot_deg = self.cube_rotation * 180.0 / math.pi
        status = [
            f"Cube Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})",
            f"Cube Rotation: ({rot_deg[0]:.1f}°, {rot_deg[1]:.1f}°, {rot_deg[2]:.1f}°)",
        ]
        y = self.height - 80
        for s in status:
            surf = self.small_font.render(s, True, (200, 200, 255))
            self.screen.blit(surf, (10, y))
            y += 25

        # Mode indicator
        mode_text = "ROTATE" if (self.shift_held and self.mouse_grabbed) else "MOVE"
        mode_color = (255, 100, 100) if mode_text == "ROTATE" else (100, 255, 100)
        mode_surface = self.font.render(mode_text, True, mode_color)
        rect = mode_surface.get_rect()
        rect.topright = (self.width - 20, 20)
        self.screen.blit(mode_surface, rect)

    # --------------------------
    # Main loop
    # --------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0
            self.handle_events()
            self.handle_input(dt)
            self.render()

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    CubeManipulator().run()
