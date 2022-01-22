#!/usr/bin/python3
from functools import partial
from time import sleep
import sys

from PyQt5.QtGui import QPalette, QKeySequence, QIcon
from PyQt5.QtCore import QDir, Qt, QUrl, QSize, QPoint, QTime, QMimeData, QProcess, QEvent
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaMetaData
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QShortcut

from weback_unofficial.client import WebackApi
from weback_unofficial.vacuum import CleanRobot

APP = QApplication(sys.argv)


def init_robot(user, pwd):
    """Login and get first available robot"""
    client = WebackApi(user, pwd)
    client.get_session()
    return CustomRobot(client.device_list()[0]['Thing_Name'], client)


class CustomRobot(CleanRobot):
    """Setup extra movements to CleanRobot"""
    def move_left(self):
        return self.publish_single('working_status', 'MoveLeft')

    def move_right(self):
        return self.publish_single('working_status', 'MoveRight')

    def move_up(self):
        return self.publish_single('working_status', 'MoveFront')

    def move_back(self):
        return self.publish_single('working_status', 'MoveBack')

    def move_down(self):
        return self.move_back()

    def move_stop(self):
        return self.publish_single('working_status', 'MoveStop')

    def move(self, position):
        getattr(self, f'move_{position}')()
        sleep(1)
        getattr(self, 'move_stop')()


class VideoPlayer(QWidget):
    """Main videoplayer"""

    def __init__(self, url, parent=None):
        """Setup video player and url"""
        super().__init__(parent)

        video_widget = QVideoWidget(self)
        self.mp = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.mp.setVideoOutput(video_widget)
        self.mp.setMedia(QMediaContent(QUrl(url)))

        layout = QVBoxLayout()
        layout.addWidget(video_widget)
        self.setLayout(layout)
        self.vac = init_robot(sys.argv[-2], sys.argv[-1])
        keys = {
            's': 'start',
            'p': 'stop',
            Qt.Key_Right: 'right',
            Qt.Key_Left: 'left',
            Qt.Key_Up: 'up',
            Qt.Key_Down: 'down',
            'q': 'exit'
        }
        for key, cmd in keys.items():
            QShortcut(QKeySequence(key),
                      self).activated.connect(partial(self.mqtt_send, cmd))

    def mqtt_send(self, cmd):
        """Send commands to weback instance."""
        if cmd == 's':
            self.vac.turn_on()
        elif cmd == 'p':
            self.vac.stop()
        elif cmd == 'exit':
            self.mp.stop()
            APP.quit()
        else:
            self.vac.move(cmd)

    def play(self):
        return self.mp.play()


def main():
    """Run"""
    print(f'Playing {sys.argv[-3]} for user {sys.argv[-2]} with pass {sys.argv[-1]}')
    player = VideoPlayer(sys.argv[-3])
    player.setWindowTitle("Game")
    player.setGeometry(100, 300, 600, 380)
    player.show()
    player.play()


if __name__ == '__main__':
    main()
    sys.exit(APP.exec_())
