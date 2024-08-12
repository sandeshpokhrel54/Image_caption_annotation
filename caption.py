import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit, QPushButton, QMessageBox, QLineEdit
from PyQt5.QtGui import QPixmap, QIntValidator
from PyQt5.QtCore import Qt

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

        self.navigation_layout = QHBoxLayout()
        self.image_number_input = QLineEdit()
        self.image_number_input.setPlaceholderText("Enter image number to jump")
        self.image_number_input.setValidator(QIntValidator(1, 9999))  # Limit input to integers
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.go_to_image)
        self.navigation_layout.addWidget(self.image_number_input)
        self.navigation_layout.addWidget(self.go_button)

        self.image_count_label = QLabel()
        self.image_count_label.setAlignment(Qt.AlignCenter)

        self.layout.addLayout(self.top_layout)
        self.layout.addWidget(self.image_count_label)
        self.layout.addLayout(self.button_layout)
        self.layout.addLayout(self.navigation_layout)

        self.image_dir = None
        self.json_file = None
        self.changed_files = set()
        self.captions = {}
        self.load_data()
        self.image_names = list(self.captions.keys())
        self.current_index = self.get_starting_index()
        self.is_caption_modified = False

        self.caption_editor.textChanged.connect(self.on_caption_changed)

    def load_data(self):
        self.image_dir = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        self.json_file = QFileDialog.getOpenFileName(self, "Select JSON File", filter="JSON Files (*.json)")[0]

        if self.image_dir and self.json_file:
            with open(self.json_file, 'r') as f:
                self.captions = json.load(f)
            self.image_names = list(self.captions.keys())
            if self.image_names:
                starting_index = self.get_starting_index()
                self.load_image(self.image_names[starting_index])

    def get_starting_index(self):
        last_modified_file = os.path.join(os.path.dirname(self.json_file), 'last_modified.txt')
        if os.path.exists(last_modified_file):
            with open(last_modified_file, 'r') as f:
                last_modified_image = f.read().strip()
            if last_modified_image in self.image_names:
                return self.image_names.index(last_modified_image)
        
        # If last_modified.txt doesn't exist or the image is not found, start with the first unannotated image
        return self.find_first_unannotated()

    def find_first_unannotated(self):
        for index, image_name in enumerate(self.image_names):
            if not self.captions[image_name].strip():
                return index
        return 0  # If all images are annotated, start from the beginning

    def load_image(self, image_name):
        image_path = os.path.join(self.image_dir, image_name)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.caption_editor.setPlainText(self.captions[image_name])
            self.current_index = self.image_names.index(image_name)
            self.update_image_count_label()
            self.is_caption_modified = False

    def update_image_count_label(self):
        total_images = len(self.image_names)
        current_image = self.current_index + 1
        self.image_count_label.setText(f"Image {current_image} of {total_images}")

    def load_next_image(self):
        if self.is_caption_modified:
            self.prompt_save_changes()
        next_index = (self.current_index + 1) % len(self.image_names)
        self.load_image(self.image_names[next_index])

    def load_previous_image(self):
        if self.is_caption_modified:
            self.prompt_save_changes()
        prev_index = (self.current_index - 1) % len(self.image_names)
        self.load_image(self.image_names[prev_index])

    def go_to_image(self):
        if self.is_caption_modified:
            self.prompt_save_changes()
        try:
            image_number = int(self.image_number_input.text())
            if 1 <= image_number <= len(self.image_names):
                self.load_image(self.image_names[image_number - 1])
            else:
                QMessageBox.warning(self, "Invalid Image Number", "Please enter a valid image number.")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")

    def save_captions(self):
        if self.json_file:
            current_caption = self.caption_editor.toPlainText()
            current_image_name = self.image_names[self.current_index]
            
            if current_caption != self.captions[current_image_name]:
                self.changed_files.add(current_image_name)
            
            self.captions[current_image_name] = current_caption
            
            # Save the updated captions
            with open(self.json_file, 'w') as f:
                json.dump(self.captions, f, indent=4)
            
            # Save the last modified image name in a separate file
            last_modified_file = os.path.join(os.path.dirname(self.json_file), 'last_modified.txt')
            with open(last_modified_file, 'w') as f:
                f.write(current_image_name)
            
            self.is_caption_modified = False

    def on_caption_changed(self):
        self.is_caption_modified = True

    def prompt_save_changes(self):
        reply = QMessageBox.question(self, 'Save Changes',
                                     'Do you want to save the changes?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.save_captions()

    def closeEvent(self, event):
        if self.is_caption_modified:
            self.prompt_save_changes()
        self.on_exit()
        event.accept()

    def on_exit(self):
        print("Files changed:", self.changed_files)
        print("Changes saved to:", self.json_file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelingWindow()
    window.show()
    sys.exit(app.exec_())
