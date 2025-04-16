import sys
import os
import glob
import cv2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QLineEdit, QFrame
)

# --------------------------
# Crop Functionality Classes
# --------------------------

class ImageCropper:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        # Find images with various extensions
        self.image_paths = glob.glob(os.path.join(self.input_folder, "*.jpg")) + \
                           glob.glob(os.path.join(self.input_folder, "*.webp")) + \
                           glob.glob(os.path.join(self.input_folder, "*.png"))
        self.current_index = 0
        self.cropping = False
        self.ref_point = []
        self.image = None
        self.clone = None

        if not self.image_paths:
            print("No images found in the directory.")
            return

        self.load_image()

    def load_image(self):
        if self.current_index >= len(self.image_paths):
            print("All images processed.")
            cv2.destroyAllWindows()
            return

        self.image = cv2.imread(self.image_paths[self.current_index])
        self.clone = self.image.copy()
        cv2.namedWindow("Image Cropper")
        cv2.setMouseCallback("Image Cropper", self.mouse_crop)
        self.show_image()

    def show_image(self):
        cv2.imshow("Image Cropper", self.image)

    def mouse_crop(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.ref_point = [(x, y)]
            self.cropping = True

        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            temp_image = self.clone.copy()
            cv2.rectangle(temp_image, self.ref_point[0], (x, y), (0, 255, 0), 2)
            cv2.imshow("Image Cropper", temp_image)

        elif event == cv2.EVENT_LBUTTONUP:
            self.ref_point.append((x, y))
            self.cropping = False
            cv2.rectangle(self.image, self.ref_point[0], self.ref_point[1], (0, 255, 0), 2)
            self.show_image()

    def save_crop(self, flip=False):
        if len(self.ref_point) == 2:
            x1, y1 = self.ref_point[0]
            x2, y2 = self.ref_point[1]
            cropped = self.clone[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
            if cropped.size > 0:
                if flip:
                    cropped = cv2.flip(cropped, 1)
                    save_name = "flipped_" + os.path.basename(self.image_paths[self.current_index])
                else:
                    save_name = os.path.basename(self.image_paths[self.current_index])
                save_path = os.path.join(self.output_folder, save_name)
                cv2.imwrite(save_path, cropped)
                print(f"Saved: {save_path}")
        self.current_index += 1
        self.load_image()

    def save_full_image(self):
        save_name = os.path.basename(self.image_paths[self.current_index])
        save_path = os.path.join(self.output_folder, save_name)
        cv2.imwrite(save_path, self.image)
        print(f"Saved: {save_path}")
        self.current_index += 1
        self.load_image()

    def skip_image(self):
        print(f"Skipped: {self.image_paths[self.current_index]}")
        self.current_index += 1
        self.load_image()

    def delete_image(self):
        image_to_delete = self.image_paths[self.current_index]
        try:
            os.remove(image_to_delete)
            print(f"Deleted: {image_to_delete}")
        except Exception as e:
            print(f"Error deleting {image_to_delete}: {e}")
        self.current_index += 1
        self.load_image()

    def run(self):
        # Run the cropping loop until 'q' is pressed.
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                self.save_crop()
            elif key == ord("f"):
                self.save_crop(flip=True)
            elif key == ord("t"):
                self.save_full_image()
            elif key == ord("a"):
                self.delete_image()
            elif key == ord("j"):
                self.skip_image()
            elif key == ord("x"):  # Left Arrow Key
                self.previous_image()
            elif key == ord("v"):  # Right Arrow Key
                self.next_image()
        cv2.destroyAllWindows()

    def previous_image(self):
        # Go to the previous image
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()

    def next_image(self):
        # Go to the next image
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()

class CropImagePage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.input_label = QLabel("Input Directory:")
        self.input_dir = QLineEdit()
        self.input_button = QPushButton("Select Input Folder")
        self.input_button.clicked.connect(self.select_input_folder)

        self.output_label = QLabel("Output Directory:")
        self.output_dir = QLineEdit()
        self.output_button = QPushButton("Select Output Folder")
        self.output_button.clicked.connect(self.select_output_folder)

        self.start_button = QPushButton("Start Cropping")
        self.start_button.clicked.connect(self.start_cropping)

        layout.addWidget(self.input_label)
        layout.addWidget(self.input_dir)
        layout.addWidget(self.input_button)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_dir)
        layout.addWidget(self.output_button)
        layout.addWidget(self.start_button)

        for button in [self.input_button, self.output_button, self.start_button]:
            button.setFixedHeight(60)  # Set button height to 60px

        self.setLayout(layout)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if folder:
            self.input_dir.setText(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_dir.setText(folder)

    def start_cropping(self):
        input_path = self.input_dir.text().strip()
        output_path = self.output_dir.text().strip()
        if not os.path.isdir(input_path) or not os.path.isdir(output_path):
            print("Invalid directories!")
            return
        cropper = ImageCropper(input_path, output_path)
        cropper.run()

# ---------------------------
# Rename Functionality
# ---------------------------

# Rename Functionality
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
import os

class RenameImagePage(QWidget):
    def __init__(self):
        super().__init__()
        self.rename_type_function = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.input_label = QLabel("Select Folder:")
        self.input_dir = QLineEdit()
        self.input_dir.setPlaceholderText("No folder selected...")
        self.input_dir.setFixedHeight(40)

        self.input_button = QPushButton("Browse Folder")
        self.input_button.setFixedHeight(50)
        self.input_button.clicked.connect(self.select_folder)

        self.mode_label = QLabel("Choose Renaming Mode:")

        self.rename_type_dataset = QPushButton("Text Replacement (.txt files)")
        self.rename_type_dataset.setFixedHeight(50)
        self.rename_type_dataset.clicked.connect(self.rename_dataset_func)

        self.rename_type_counter = QPushButton("Counter-Based Renaming")
        self.rename_type_counter.setFixedHeight(50)
        self.rename_type_counter.clicked.connect(self.rename_files_counter_func)

        self.old_phrase_input = QLineEdit()
        self.old_phrase_input.setPlaceholderText("Old Phrase")
        self.old_phrase_input.setFixedHeight(40)

        self.new_phrase_input = QLineEdit()
        self.new_phrase_input.setPlaceholderText("New Phrase")
        self.new_phrase_input.setFixedHeight(40)

        self.start_button = QPushButton("Start Renaming")
        self.start_button.setFixedHeight(60)
        self.start_button.clicked.connect(self.start_renaming)

        self.deduplicate_button = QPushButton("Remove Duplicate Phrases")
        self.deduplicate_button.setFixedHeight(50)
        self.deduplicate_button.clicked.connect(self.remove_duplicate_phrases_in_txt_files)

        self.status_label = QLabel("Status: Waiting for input.")
        self.status_label.setStyleSheet("color: gray;")

        layout.addWidget(self.input_label)
        layout.addWidget(self.input_dir)
        layout.addWidget(self.input_button)
        layout.addSpacing(10)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.rename_type_dataset)
        layout.addWidget(self.rename_type_counter)
        layout.addSpacing(10)
        layout.addWidget(self.old_phrase_input)
        layout.addWidget(self.new_phrase_input)
        layout.addSpacing(10)
        layout.addWidget(self.start_button)
        layout.addWidget(self.deduplicate_button)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.toggle_phrase_inputs(False)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.input_dir.setText(folder)

    def rename_dataset_func(self):
        self.rename_type_function = "dataset"
        self.update_selection_styles()
        self.toggle_phrase_inputs(True)

    def rename_files_counter_func(self):
        self.rename_type_function = "counter"
        self.update_selection_styles()
        self.toggle_phrase_inputs(False)

    def update_selection_styles(self):
        self.rename_type_dataset.setStyleSheet("")
        self.rename_type_counter.setStyleSheet("")
        if self.rename_type_function == "dataset":
            self.rename_type_dataset.setStyleSheet("background-color: #111; color: white;")
        elif self.rename_type_function == "counter":
            self.rename_type_counter.setStyleSheet("background-color: #111; color: white;")

    def toggle_phrase_inputs(self, show):
        self.old_phrase_input.setVisible(show)
        self.new_phrase_input.setVisible(show)

    def start_renaming(self):
        directory = self.input_dir.text().strip()
        if not os.path.isdir(directory):
            self.status_label.setText("Status: Invalid directory selected.")
            return

        if self.rename_type_function == "dataset":
            old_phrase = self.old_phrase_input.text().strip()
            new_phrase = self.new_phrase_input.text().strip()
            if old_phrase and new_phrase:
                rename_dataset(directory, old_phrase, new_phrase)
                self.status_label.setText("Status: Text replacement completed.")
            else:
                self.status_label.setText("Status: Enter both old and new phrases.")
        elif self.rename_type_function == "counter":
            rename_files_counter(directory)
            self.status_label.setText("Status: Counter-based renaming completed.")
        else:
            self.status_label.setText("Status: Please select a renaming mode.")

    def remove_duplicate_phrases_in_txt_files(self):
        directory = self.input_dir.text().strip()
        if not os.path.isdir(directory):
            self.status_label.setText("Status: Invalid directory selected.")
            return
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                phrases = [phrase.strip() for phrase in content.split(',')]
                unique_phrases = []
                seen = set()
                for phrase in phrases:
                    if phrase not in seen:
                        seen.add(phrase)
                        unique_phrases.append(phrase)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(', '.join(unique_phrases))
        self.status_label.setText("Status: Duplicate phrases removed.")

def rename_dataset(folder_path, old_phrase, new_phrase):
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            content = content.replace(old_phrase, new_phrase)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)

def rename_files_counter(directory):
    files = sorted(os.listdir(directory))
    base_name = 0
    file_map = {}
    for file in files:
        name, ext = os.path.splitext(file)
        if name not in file_map:
            file_map[name] = f"{base_name:03d}"
            base_name += 1
    for file in files:
        name, ext = os.path.splitext(file)
        new_name = f"{file_map[name]}{ext}"
        os.rename(os.path.join(directory, file), os.path.join(directory, new_name))


# ---------------------------
# Label Images UI
# ---------------------------
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QTextEdit, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import glob
import os

class LabelDatasetPage(QWidget):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.text_paths = []
        self.current_index = 0
        self.input_buttons = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.image_label = QLabel("Image")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Edit the description here...")
        self.text_edit.setFontPointSize(12)
        self.text_edit.setReadOnly(False)

        self.image_frame = QFrame()
        self.image_frame.setLayout(QVBoxLayout())
        self.text_frame = QFrame()
        self.text_frame.setLayout(QVBoxLayout())

        self.image_frame.layout().addWidget(self.image_label)
        self.text_frame.layout().addWidget(self.text_edit)

        self.image_area = QScrollArea()
        self.text_area = QScrollArea()

        self.image_area.setWidget(self.image_frame)
        self.text_area.setWidget(self.text_frame)

        self.image_area.setWidgetResizable(True)
        self.text_area.setWidgetResizable(True)

        self.input_layout = QVBoxLayout()
        self.add_remove_buttons()

        self.navigation_layout = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(self.previous_image)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_image)
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)

        # Add the "Open Folder" button here
        self.open_folder_button = QPushButton("Open Label Folder")
        self.open_folder_button.clicked.connect(self.set_directory)

        # Add the "Unselect Folder" button
        self.unselect_folder_button = QPushButton("Unselect Folder")
        self.unselect_folder_button.clicked.connect(self.unselect_folder)

        # Add the buttons to the layout
        self.navigation_layout.addWidget(self.previous_button)
        self.navigation_layout.addWidget(self.next_button)
        self.navigation_layout.addWidget(self.save_button)
        self.navigation_layout.addWidget(self.open_folder_button)
        self.navigation_layout.addWidget(self.unselect_folder_button)

        # Apply larger font size to buttons
        button_style = """
            QPushButton {
                background-color: #444;
                color: white;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-size: 18px;  /* Increased font size */
            }
            QPushButton:hover {
                background-color: #666;
            }
        """
        # Apply style to all buttons
        for button in [self.previous_button, self.next_button, self.save_button, self.open_folder_button, self.unselect_folder_button]:
            button.setStyleSheet(button_style)
            button.setFixedHeight(60)  # Set button height to 60px

        layout.addWidget(self.image_area)
        layout.addWidget(self.text_area)
        layout.addLayout(self.input_layout)
        layout.addLayout(self.navigation_layout)

        self.setLayout(layout)

    def unselect_folder(self):
        # Clear the image and text paths
        self.image_paths = []
        self.text_paths = []
        self.current_index = 0
        
        # Reset the image and text area
        self.image_label.clear()  # Clear the image
        self.text_edit.clear()  # Clear the text editor
        print("Folder unselected and view cleared.")
        
    def load_images_and_texts(self, folder_path):
        self.image_paths = sorted(glob.glob(os.path.join(folder_path, "*.jpg")) +
                                  glob.glob(os.path.join(folder_path, "*.jpeg")) +
                                  glob.glob(os.path.join(folder_path, "*.png")))
        self.text_paths = sorted(glob.glob(os.path.join(folder_path, "*.txt")))
        if len(self.image_paths) != len(self.text_paths):
            print("Error: Number of images does not match number of text files.")
            return
        self.load_image_and_text()

    def load_image_and_text(self):
        if self.current_index < 0 or self.current_index >= len(self.image_paths):
            return
        pixmap = QPixmap(self.image_paths[self.current_index])
        pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
        with open(self.text_paths[self.current_index], "r", encoding="utf-8") as file:
            text = file.read()
            self.text_edit.setText(text)


    def add_remove_buttons(self):
        self.control_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Input")
        self.add_button.setFixedHeight(50)
        self.add_button.clicked.connect(self.add_input_button)
        self.control_layout.addWidget(self.add_button)
        self.input_layout.addLayout(self.control_layout)

    def add_input_button(self):
        input_layout = QHBoxLayout()
        input_field = QLineEdit()
        add_text_button = QPushButton("➕")
        add_text_button.clicked.connect(lambda: self.append_to_text(input_field))
        remove_button = QPushButton("❌")
        remove_button.clicked.connect(lambda: self.remove_input_button(input_layout, input_field, add_text_button, remove_button))
        
        input_layout.addWidget(input_field)
        input_layout.addWidget(add_text_button)
        input_layout.addWidget(remove_button)

        self.input_layout.addLayout(input_layout)
        self.input_buttons.append((input_layout, input_field, add_text_button, remove_button))

    def remove_input_button(self, layout, field, add_button, remove_button):
        for widget in [field, add_button, remove_button]:
            widget.deleteLater()
        layout.deleteLater()
        self.input_buttons.remove((layout, field, add_button, remove_button))

    def append_to_text(self, input_field):
        if self.current_index < 0 or self.current_index >= len(self.text_paths):
            return
        
        new_text = input_field.text().strip()
        if new_text:
            with open(self.text_paths[self.current_index], "a", encoding="utf-8") as file:
                file.write(new_text)
            self.text_edit.setPlainText(self.text_edit.toPlainText().strip() + new_text)

    def save_changes(self):
        if self.current_index < 0 or self.current_index >= len(self.text_paths):
            return
        new_text = self.text_edit.toPlainText()
        with open(self.text_paths[self.current_index], "w", encoding="utf-8") as file:
            file.write(new_text)
        print(f"Changes saved to: {self.text_paths[self.current_index]}")

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image_and_text()

    def previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image_and_text()

    def set_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.load_images_and_texts(folder)

# ---------------------------
# Make Dataset Functionality
# ---------------------------

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PySide6.QtCore import QThread, Signal
import os
import pyautogui
import keyboard
from datetime import datetime

class ScreenshotWorker(QThread):
    status_changed = Signal(str)

    def __init__(self, save_dir):
        super().__init__()
        self.save_dir = save_dir
        self.running = True

    def run(self):
        keyboard.add_hotkey('g', self.take_screenshot)
        self.status_changed.emit("Listening: Press 'G' to capture, 'ESC' to stop.")
        keyboard.wait('esc')
        self.running = False
        keyboard.clear_all_hotkeys()
        self.status_changed.emit("Stopped listening.")

    def take_screenshot(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        filename = os.path.join(self.save_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

class DatasetScreenshotPage(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.save_dir = "screenshots"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.status_label = QLabel("Select a folder and start listening.")
        self.select_button = QPushButton("Select Save Directory")
        self.start_button = QPushButton("Start Listening (G to capture)")
        self.start_button.setEnabled(False)

        self.select_button.clicked.connect(self.select_directory)
        self.start_button.clicked.connect(self.start_listening)

        layout.addWidget(self.status_label)
        layout.addWidget(self.select_button)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def select_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Screenshots")
        if folder:
            self.save_dir = folder
            self.start_button.setEnabled(True)
            self.status_label.setText(f"Save directory set: {self.save_dir}")

    def start_listening(self):
        if self.worker is None or not self.worker.isRunning():
            self.worker = ScreenshotWorker(self.save_dir)
            self.worker.status_changed.connect(self.update_status)
            self.worker.start()

    def update_status(self, text):
        self.status_label.setText(text)


# ---------------------------
# Manage Tags Section
# ---------------------------

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QFileDialog, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt
import os
import glob
from collections import Counter

class ManageTagsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.tag_counter = Counter()
        self.text_files = []
        self.full_tag_list = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.folder_label = QLabel("No folder selected.")
        self.folder_label.setWordWrap(True)
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tags...")
        self.search_input.textChanged.connect(self.filter_tags)

        self.tag_list = QListWidget()
        self.tag_list.setStyleSheet("""
            QListWidget {
                font-size: 18px;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)

        self.remove_button = QPushButton("Remove Selected Tag")
        self.remove_button.clicked.connect(self.remove_selected_tag)

        layout.addWidget(self.folder_label)
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.search_input)
        layout.addWidget(QLabel("Tags and Counts:"))
        layout.addWidget(self.tag_list)
        layout.addWidget(self.remove_button)

        for widget in [self.select_folder_button, self.remove_button]:
            widget.setFixedHeight(50)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing TXT Files")
        if folder:
            self.folder_path = folder
            self.load_tags()

    def load_tags(self):
        self.tag_counter = Counter()
        self.text_files = sorted(glob.glob(os.path.join(self.folder_path, "*.txt")))
        for path in self.text_files:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                tags = [tag.strip().lower() for tag in content.split(",") if tag.strip()]
                self.tag_counter.update(tags)

        self.full_tag_list = sorted(self.tag_counter.items(), key=lambda x: (-x[1], x[0]))
        self.update_tag_list(self.full_tag_list)

    def update_tag_list(self, tag_data):
        self.tag_list.clear()
        for tag, count in tag_data:
            self.tag_list.addItem(f"{tag} ({count})")

    def filter_tags(self, text):
        filtered = [(tag, count) for tag, count in self.full_tag_list if text.lower() in tag.lower()]
        self.update_tag_list(filtered)

    def remove_selected_tag(self):
        selected = self.tag_list.currentItem()
        if not selected:
            QMessageBox.information(self, "No Tag Selected", "Please select a tag to remove.")
            return

        tag_to_remove = selected.text().split(" (")[0]
        removed_count = 0

        for path in self.text_files:
            with open(path, "r", encoding="utf-8") as file:
                tags = [tag.strip() for tag in file.read().split(",") if tag.strip()]
            new_tags = [tag for tag in tags if tag.lower() != tag_to_remove.lower()]
            if len(new_tags) != len(tags):
                with open(path, "w", encoding="utf-8") as file:
                    file.write(", ".join(new_tags))
                removed_count += 1

        QMessageBox.information(self, "Removal Complete",
                                f'Tag "{tag_to_remove}" removed from {removed_count} file(s).')

        self.load_tags()


# ---------------------------
# Main Window with Split UI
# ---------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Data Manager")
        self.setGeometry(100, 100, 1000, 600)
        main_layout = QHBoxLayout()

        # Left Navigation Panel
        self.nav_menu = QWidget()
        nav_layout = QVBoxLayout()
        self.nav_menu.setStyleSheet("background-color: #333; padding: 10px;")
        self.buttons = {
            "Crop Images": lambda: self.set_page(self.crop_page),
            "Rename Images": lambda: self.set_page(self.rename_page),
            "Label Images": lambda: self.set_page(self.label_page),
            "Make Dataset": lambda: self.set_page(self.dataset_page),
            "Manage Tags": lambda: self.set_page(self.manage_tags_page),
        }
        for text, func in self.buttons.items():
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: 2px solid #555;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #666;
                }
            """)
            btn.clicked.connect(func)
            nav_layout.addWidget(btn)
        self.nav_menu.setLayout(nav_layout)

        # Right Display Area
        self.display_area = QWidget()
        self.display_area.setLayout(QVBoxLayout())

        # Instantiate our tool pages
        self.dataset_page = DatasetScreenshotPage()
        self.crop_page = CropImagePage()
        self.manage_tags_page = ManageTagsPage()
        self.label_page = LabelDatasetPage()
        self.rename_page = RenameImagePage()

        self.dataset_page.setStyleSheet("font-size: 18px; padding: 20px; color: white;")

        # Main container
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Divider between nav and display
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setStyleSheet("background-color: #555; width: 2px;")

        main_layout.addWidget(self.nav_menu, 1)   # Small left panel
        main_layout.addWidget(divider)
        main_layout.addWidget(self.display_area, 4)  # Larger right panel

        # Set default page to Crop Images (or any page you prefer)
        self.set_page(self.crop_page)

    def set_page(self, page):
        layout = self.display_area.layout()
        # Clear the current display area
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        # Add the new page
        layout.addWidget(page)

    def open_label_folder(self):
        # If the Label Images tool is active, use its built-in folder selection
        if self.label_page:
            self.label_page.set_directory()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
