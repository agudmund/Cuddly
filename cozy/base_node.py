from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QFont

class BaseNode(QGraphicsRectItem):
    def __init__(self, node_id, title, full_text, pos=QPointF(0, 0), width=300, height=200):
        super().__init__(0, 0, width, height)
        self.setPos(pos)
        self.node_id = node_id
        self.title = title
        self.full_text = full_text
        
        # UI State
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable | 
            QGraphicsRectItem.ItemIsSelectable | 
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        
        # Visuals - Centralizing the "Cozy" look
        self.setPen(QPen(QColor("#444444"), 2))
        self.setBrush(QColor(30, 30, 30, 200))
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)

    def paint(self, painter, option, widget):
        # Draw the main body
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), 10, 10)

        # Draw Title
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(self.rect().adjusted(10, 10, -10, -10), Qt.AlignTop | Qt.AlignLeft, self.title)

        # Let subclasses draw their specific content
        self.paint_content(painter)

    def paint_content(self, painter):
        """Override this in subclasses to draw text, images, or renders."""
        pass

    def to_dict(self):
        """Standardized export for SessionManager."""
        return {
            "node_id": self.node_id,
            "title": self.title,
            "full_text": self.full_text,
            "pos_x": self.scenePos().x(),
            "pos_y": self.scenePos().y(),
            "width": self.rect().width(),
            "height": self.rect().height()
        }