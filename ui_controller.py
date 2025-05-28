import argparse
from PyQt6 import QtCore, QtGui, QtWidgets
import sys
import threading
import tempfile

from ui_model import TaskModel
from ui_view import TaskView

class TaskController:
    def __init__(self, view:TaskView, model:TaskModel):
        self.view = view
        self.model = model
        self.model.add_observer(self)
        self.recording = False
        self.audio_file = None
        self.audio_thread = None

        self.view.ui.pushButton.clicked.connect(self.on_command_send)
        self.view.ui.pushButton_2.clicked.connect(self.on_voice_button)


    def on_command_send(self):
        threading.Thread(target=self.model.execute_task_from_ui, args=(self.view.ui.lineEdit_2.text(), self.view.ui.lineEdit.text(), self.view.ui.checkBox.isChecked()), daemon=True).start()
        # self.model.execute_task_from_ui(ques=self.view.ui.lineEdit_2.text(), url=self.view.ui.lineEdit.text(), require_reload=self.view.ui.checkBox.isChecked())


    # def handle_start_task(self):
    #     """處理開始任務的邏輯"""
    #     input_data = self.view.input_entry.get()
    #     if not input_data:
    #         self.view.set_result("請輸入資料！")
    #         return

    #     # 啟動多工處理
    #     threading.Thread(target=self.model.process_data, args=(input_data,), daemon=True).start()

    def on_voice_button(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording_and_transcribe()

    def start_recording(self):
        self.recording = True
        self.view.set_voice_button_state(True)
        self.audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        self.audio_thread = threading.Thread(
            target=self.model.record_audio,
            args=(self.audio_file, lambda: self.recording),
            daemon=True
        )
        self.audio_thread.start()
        self.view.add_status_text("錄音中...")

    def stop_recording_and_transcribe(self):
        self.recording = False
        self.view.set_voice_button_state(False)
        self.view.add_status_text("錄音結束，正在辨識...")
        if self.audio_thread:
            self.audio_thread.join()
        # def transcribe_and_set():
        #     text = self.model.transcribe_audio(self.audio_file)
        #     if text:
        #         pass # do task
        threading.Thread(target=self.model.transcribe_audio, args=(self.audio_file,), daemon=True).start()
        
        # save the audio file
        # import shutil
        # import os
        # target_path = os.path.join(".", os.path.basename(self.audio_file))
        # shutil.copy(self.audio_file, target_path)



    def update(self, data, update_type='status'):
        if update_type == 'status':
            self.view.add_status_text(data)
        elif update_type == 'voice':
            self.view.ui.lineEdit_2.setText(data)


# Main Application
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_file', type=str, default='data/test.json')
    parser.add_argument('--max_iter', type=int, default=5)
    parser.add_argument("--api_key", default="key", type=str, help="YOUR_OPENAI_API_KEY")
    parser.add_argument("--api_model", default="gpt-4-vision-preview", type=str, help="api model name")
    parser.add_argument("--output_dir", type=str, default='results')
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max_attached_imgs", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--download_dir", type=str, default="downloads")
    parser.add_argument("--text_only", action='store_true')
    # for web browser
    parser.add_argument("--headless", action='store_true', help='The window of selenium')
    parser.add_argument("--save_accessibility_tree", action='store_true')
    parser.add_argument("--force_device_scale", action='store_true')
    parser.add_argument("--window_width", type=int, default=1024)
    parser.add_argument("--window_height", type=int, default=768)  # for headless mode, there is no address bar
    parser.add_argument("--fix_box_color", action='store_true')
    # improvement
    parser.add_argument("--dynamic_load",action='store_true', help='dynamic load web content')
    parser.add_argument("--web_markdown",action='store_true', help='load web html to markdown')
    parser.add_argument("--web_assistant",action='store_true', help='use web assistant to get suggestion')
    parser.add_argument("--web_observer",action='store_true', help='use web observer')
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)  

    # 建立 MVC 結構
    model = TaskModel(args)
    view = TaskView()
    controller = TaskController(view, model)
      
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()