import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import shutil

class LabelingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labeling Software")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.top_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.caption_editor = QTextEdit()
        self.top_layout.addWidget(self.image_label)
        self.top_layout.addWidget(self.caption_editor)

        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_captions)
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.load_previous_image)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.load_next_image)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.button_layout)

        self.image_dir = None
        self.json_file_old = None
        self.json_file = None
        self.changed_files = set()
        self.captions = {}
        self.load_data()
        self.image_names = list(self.captions.keys())
        self.current_index = 0

    def load_data(self):
        self.image_dir = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        self.json_file_old = QFileDialog.getOpenFileName(self, "Select JSON File", filter="JSON Files (*.json)")[0]
        # print(type(self.json_file))
        self.json_file = str( "./" + str(self.json_file_old.split('/')[-1].split('.')[0]) +'_edited.json')
        shutil.copy(self.json_file_old, self.json_file)

        if self.image_dir and self.json_file:
            with open(self.json_file, 'r') as f:
                self.captions = json.load(f)
            self.image_names = list(self.captions.keys())
            self.load_image(self.image_names[0])

    def load_image(self, image_name):
        # image_dir = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        
        image_path = os.path.join(self.image_dir, image_name)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.caption_editor.setPlainText(self.captions[image_name])
            self.current_index = self.image_names.index(image_name)

    def load_next_image(self):
        # print(self.image_names)
        next_index = (self.current_index + 1) % len(self.image_names)
        self.load_image(self.image_names[next_index])

    def load_previous_image(self):
        prev_index = (self.current_index - 1) % len(self.image_names)
        self.load_image(self.image_names[prev_index])

    def save_captions(self):
        # save_file = QFileDialog.getSaveFileName(self, "Save JSON File", filter="JSON Files (*.json)")[0]
        save_file =  self.json_file
        if save_file:
            current_caption = self.caption_editor.toPlainText() #get caption
            current_image_name = self.image_names[self.current_index]
            
            #check if changed
            if (current_caption != self.captions[current_image_name]):
                self.changed_files.add(current_image_name)
            
            #set caption
            self.captions[current_image_name] = current_caption
            
            with open(save_file, 'w') as f:
                json.dump(self.captions, f, indent=4)

    def closeEvent(self, event):
        self.on_exit()
        event.accept()

    def on_exit(self):
        # print("closing")
        print("Files changed", self.changed_files)
        print("New json file saved at: ", self.json_file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelingWindow()
    window.show()
    sys.exit(app.exec_())