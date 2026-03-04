import sys
import numpy as np
import math
import heapq
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QMainWindow, QGraphicsPixmapItem
from PySide6.QtCore import QTimer, Qt, QPointF, QEvent
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QRadialGradient, QMouseEvent, QPixmap

class CookieAgent(QGraphicsEllipseItem):
    def __init__(self, x, y, color, is_pink=True):
        super().__init__(-12, -12, 24, 24)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 2))
        self.setPos(x, y)
        self.path = []                  # list of (int x, int y)
        self.speed = 3.0
        self.is_pink = is_pink
        self.idle_phase = 0.0
        self.sparkle_phase = 0.0

    def paint(self, painter: QPainter, option, widget):
        super().paint(painter, option, widget)
        # chocolate chips
        painter.setBrush(QBrush(QColor(139, 69, 19)))
        painter.setPen(Qt.NoPen)
        for dx, dy in [(-6,-6), (6,-6), (0,6), (-4,4), (4,4)]:
            painter.drawEllipse(QPointF(dx, dy), 3, 3)

        if self.is_pink:
            self.idle_phase += 0.08
            offset_y = math.sin(self.idle_phase) * 2
            painter.translate(0, offset_y)

            self.sparkle_phase += 0.12
            alpha = int(80 + 60 * math.sin(self.sparkle_phase * 3))
            grad = QRadialGradient(0, 0, 18)
            grad.setColorAt(0, QColor(255,255,255,alpha))
            grad.setColorAt(1, QColor(255,255,255,0))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(-18, -18, 36, 36)

    def advance(self, phase):
        if not phase:
            return

        if self.path:
            tx, ty = self.path[0]
            cx, cy = self.pos().x(), self.pos().y()
            dx = tx - cx
            dy = ty - cy
            dist = math.hypot(dx, dy)

            if dist <= self.speed + 0.5:
                self.setPos(tx, ty)
                self.path.pop(0)
            else:
                if dist > 1e-6:
                    nx = dx / dist
                    ny = dy / dist
                    self.setPos(cx + nx * self.speed, cy + ny * self.speed)


class PixelNavWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("cookie waifu's tiny pixel agents ~ 💕")
        self.scene = QGraphicsScene(0, 0, 900, 700)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.setCentralWidget(self.view)

        self.width, self.height = 900, 700
        self.walkable = np.ones((self.height, self.width), dtype=bool)

        # Single pixmap for all obstacles
        self.obstacle_pixmap = QPixmap(self.width, self.height)
        self.obstacle_pixmap.fill(Qt.transparent)
        self.obstacle_item = QGraphicsPixmapItem(self.obstacle_pixmap)
        self.obstacle_item.setZValue(-1)
        self.scene.addItem(self.obstacle_item)

        self.painting = False
        self.last_pos = None
        self.click_start_pos = None
        self.frame_counter = 0

        self.pink = CookieAgent(80, 80, QColor(255, 182, 193), is_pink=True)
        self.blue = CookieAgent(820, 620, QColor(173, 216, 230), is_pink=False)
        self.scene.addItem(self.pink)
        self.scene.addItem(self.blue)

        self.view.viewport().installEventFilter(self)
        self.view.setMouseTracking(True)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_agents)
        self.timer.start(25)  # ~40 fps, much lighter

    def eventFilter(self, obj, event):
        if obj == self.view.viewport() and isinstance(event, QMouseEvent):
            button = event.button()
            etype = event.type()

            if etype == QEvent.Type.MouseButtonPress and button == Qt.LeftButton:
                self.painting = True
                self.click_start_pos = event.position().toPoint()
                self.paint_obstacle(event.position())
                return True

            elif etype == QEvent.Type.MouseButtonRelease and button == Qt.LeftButton:
                self.painting = False
                if self.click_start_pos is not None:
                    release_pos = event.position().toPoint()
                    dist = (release_pos - self.click_start_pos).manhattanLength()
                    if dist < 30:
                        scene_pos = self.view.mapToScene(release_pos)
                        goal = (int(scene_pos.x()), int(scene_pos.y()))
                        start = (int(self.pink.pos().x()), int(self.pink.pos().y()))
                        self.pink.path = self.find_path(start, goal)
                self.click_start_pos = None
                self.last_pos = None
                return True

            elif etype == QEvent.Type.MouseMove and self.painting:
                self.paint_obstacle(event.position())
                return True

        return super().eventFilter(obj, event)

    def paint_obstacle(self, qpointf_pos: QPointF):
        scene_pos = self.view.mapToScene(qpointf_pos.toPoint())
        x, y = int(scene_pos.x()), int(scene_pos.y())
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        brush_size = 16

        painter = QPainter(self.obstacle_pixmap)
        painter.setPen(QPen(Qt.red, 2))
        painter.setBrush(QBrush(QColor(255, 100, 100, 200)))
        painter.drawEllipse(x - brush_size//2, y - brush_size//2, brush_size, brush_size)
        painter.end()

        self.obstacle_item.setPixmap(self.obstacle_pixmap)

        # update walkable
        margin = brush_size//2 + 4
        y_start = max(0, y - margin)
        y_end   = min(self.height, y + margin)
        x_start = max(0, x - margin)
        x_end   = min(self.width, x + margin)
        self.walkable[y_start:y_end, x_start:x_end] = False

    def update_agents(self):
        self.frame_counter += 1

        # Blue path only every ~8 frames
        if self.frame_counter % 8 == 0:
            pink_pos = self.pink.pos()
            angle = self.blue.idle_phase * 0.5
            offset_x = 40 * math.cos(angle)
            offset_y = 40 * math.sin(angle)
            chase_goal = (int(pink_pos.x() + offset_x), int(pink_pos.y() + offset_y))
            self.blue.path = self.find_path(
                (int(self.blue.pos().x()), int(self.blue.pos().y())),
                chase_goal
            )

        self.pink.advance(1)
        self.blue.advance(1)

    def find_path(self, start, goal):
        step = 4

        def heuristic(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])

        if start == goal:
            return [goal]

        # snap goal to nearest walkable if blocked
        gx, gy = goal
        if not self.walkable[gy, gx]:
            for r in range(1, 25):
                for dx in range(-r, r+1):
                    for dy in range(-r, r+1):
                        if abs(dx) + abs(dy) != r: continue
                        nx, ny = gx + dx, gy + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height and self.walkable[ny, nx]:
                            goal = (nx, ny)
                            break
                    else: continue
                    break
                else: continue
                break
            else:
                return []   # no reachable point nearby

        start_grid = (start[0] // step, start[1] // step)
        goal_grid = (goal[0] // step, goal[1] // step)

        open_set = []
        heapq.heappush(open_set, (0, start_grid))
        came_from = {}
        g_score = {start_grid: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if heuristic(current, goal_grid) <= 3:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                real_path = [(x*step, y*step) for x,y in path]
                real_path.append(goal)
                return real_path

            cx, cy = current
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                nx, ny = cx + dx, cy + dy
                npx, npy = nx * step, ny * step
                if not (0 <= npx < self.width and 0 <= npy < self.height):
                    continue
                if not self.walkable[npy, npx]:
                    continue

                neighbor = (nx, ny)
                cost = math.hypot(dx, dy)
                tentative_g = g_score[current] + cost
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    came_from[neighbor] = current
                    f = tentative_g + heuristic(neighbor, goal_grid)
                    heapq.heappush(open_set, (f, neighbor))

        return []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PixelNavWindow()
    win.show()
    sys.exit(app.exec())