from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QMessageBox, QLineEdit, QListWidget,
                             QSplitter, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit, QCheckBox, 
                             QDialog)
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
import sys

class Dialog(QDialog):
    get_title = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        uic.loadUi("save_title.ui", self)
        self.done_button.clicked.connect(self.on_clicked)
    def on_clicked(self):
        title = self.title_line_edit.text()

        if not title:
            QMessageBox.warning(self, "Title Error", "Please enter a title")
            return
        
        self.get_title.emit(title)
        self.accept()
class LoginForm(QWidget):
    entry_successful = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        uic.loadUi("Login.ui", self)

        self.__init__db()

        self.login_button.clicked.connect(self.login_user)
        self.sign_up_button.clicked.connect(self.sign_up_user)
    
    def close_window(self, username):
        self.entry_successful.emit(username)

        self.close()
    
    def __init__db(self):
        self.conn_name = "notepad_conn"
        self.db = QSqlDatabase.addDatabase("QSQLITE", self.conn_name)
        self.db.setDatabaseName("Notepad.db")

        if not self.db.open():
            QMessageBox.critical(self, "DB Error", "Could not open Database.")
            return
        
        query = QSqlQuery(self.db)
        query.exec("""
                        CREATE TABLE IF NOT EXISTS Users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE, password TEXT)
                      """)
    
    def login_user(self):
        username = self.username_line_edit.text()
        password = self.password_line_edit.text()

        if username and password:

            query = QSqlQuery(self.db)
            query.prepare("""
                            SELECT username FROM Users WHERE username = ? AND password = ?
                          """)
            query.addBindValue(username)
            query.addBindValue(password)
            query.exec()

            if not query.next():
                QMessageBox.critical(self, "Login Error", "No such user exists, try signing up.")
                return
            QMessageBox.information(self, "Login Successful", f"Welcome back {username}")
            self.close_window(username)
        else:
            QMessageBox.warning(self, "Login Error", "Please enter both a username and password.")
            return
    
    def sign_up_user(self):
        username = self.username_line_edit.text()
        password = self.password_line_edit.text()

        if username and password:
            query = QSqlQuery(self.db)
            query.prepare("""
                            INSERT INTO Users(username, password) VALUES(?, ?)
                          """)
            query.addBindValue(username)
            query.addBindValue(password)

            if not query.exec():
                QMessageBox.warning(self, "Sign up Error", "User already exists, try logging in.")
                return
            QMessageBox.information(self, "Sign up successful",
                                     f"Your sign up was successful {username}")
            self.close_window(username)
        else:
            QMessageBox.critical(self, "Sign up Error", "Please enter both username and password")
            return

class Notepad(QMainWindow):
    def __init__(self, username):
        super().__init__()

        self.username = username
        self.setGeometry(200, 200, 640, 480)
        self.setWindowTitle(f"{self.username}'s notes")

        self.__init__layout()
        self.__init__db()
        self.__init__notes()
    
    def __init__layout(self):
        splitter = QSplitter()

        self.note_list = QListWidget()
        self.note_list.itemClicked.connect(self.load_note)
        self.text_area = QTextEdit()

        splitter.addWidget(self.note_list)
        splitter.addWidget(self.text_area)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        button_layout = QHBoxLayout()
        self.new_button = QPushButton("New Note")
        self.new_button.clicked.connect(self.new_note)
        self.save_button = QPushButton("Save Note")
        self.save_button.clicked.connect(self.on_save_button_clicked)
        self.delete_button = QPushButton("Delete Note")
        self.delete_button.clicked.connect(self.delete_note)
        self.delete_button.setEnabled(False)

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)

        self.dark_mode_checkbox = QCheckBox("dark mode")
        self.dark_mode_checkbox.toggled.connect(self.on_checked)

        vbox = QVBoxLayout()

        vbox.addWidget(splitter)
        vbox.addLayout(button_layout)
        vbox.addWidget(self.dark_mode_checkbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)

        self.setCentralWidget(central_widget)
    
    def __init__db(self):

        self.db = QSqlDatabase.database("notepad_conn")

        query = QSqlQuery(self.db)
        query.exec("""
                    CREATE TABLE IF NOT EXISTS Notes(note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL, title TEXT NOT NULL UNIQUE, content TEXT, FOREIGN KEY(user_id) 
                   REFERENCES Users(user_id))
                   """)
    
    def get_user_id(self, username):

        query = QSqlQuery(self.db)
        query.prepare("""
                        SELECT user_id FROM Users WHERE username = ?
                    """)
        query.addBindValue(username)

        if not query.exec():
            print(f"Error fetching user_id: {query.lastError().text()}")
            return
        
        if not query.next():
            return None

        user_id = query.value(0)

        return user_id

    def get_note_id(self, title):
        query = QSqlQuery(self.db)
        query.prepare("SELECT note_id FROM Notes WHERE title = ?")
        query.addBindValue(title)

        if not query.exec():
            print(f"Error fetching note_id: {query.lastError().text()}")
            return
        
        if not query.next():
            return None

        note_id = query.value(0)

        return note_id
    def __init__notes(self):
        user_id = self.get_user_id(self.username)

        if user_id is None:
            QMessageBox.critical(self, "DB Error", "Logged-in user not found.")
            return

        query = QSqlQuery(self.db)

        query.prepare("SELECT title FROM Notes WHERE user_id = ?")
        query.addBindValue(user_id)
        if not query.exec():
            QMessageBox.critical(self, "DB Error", query.lastError().text())
            return

        while query.next():
            title = query.value(0)

            self.note_list.addItem(title)
        if self.note_list.count() > 0:
            self.delete_button.setEnabled(True)
    def new_note(self):
        self.note_list.clearSelection()
        self.note_list.setCurrentItem(None)
        self.text_area.setFocus()
        self.text_area.clear()
    
    def on_save_button_clicked(self):
        current_item = self.note_list.currentItem()

        if current_item is None:
            self.save_note()
        else:
            self.update_note()
    def save_note(self):
        text = self.text_area.toPlainText()

        if not text:
            QMessageBox.warning(self, "Save error", "Cannot save an empty note.")
            return
        
        title_dialog = Dialog()

        title_dialog.get_title.connect(self.collect_title)

        if title_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        user_id = self.get_user_id(self.username)

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO Notes(user_id, title, content) VALUES(?, ?, ?)")
        query.addBindValue(user_id)
        query.addBindValue(self.title)
        query.addBindValue(text)    

        if not query.exec():
            QMessageBox.warning(self, "DB Error", "Title already exists, pick a new title")
            return
        
        QMessageBox.information(self, "Save Successful", "Your note was saved successfully")
        self.note_list.addItem(self.title)
        self.delete_button.setEnabled(True)
    
    def update_note(self):
        current_item = self.note_list.currentItem()
        current_title = current_item.text()
        current_note_id = self.get_note_id(current_title)

        current_text = self.text_area.toPlainText()

        query = QSqlQuery(self.db)
        query.prepare("UPDATE Notes SET content = ? WHERE note_id = ?")
        query.addBindValue(current_text)
        query.addBindValue(current_note_id)  

        if not query.exec():
            print(f"Could not update note: {query.lastError().text()}")
            return
        
        QMessageBox.information(self, "Update Successful", "Your note was updated successfully")

    def collect_title(self, title):
        self.title = title
        
    def delete_note(self):
        current_item = self.note_list.currentItem()

        if not current_item:
            QMessageBox.information(self, "Deletion Error", "Please select a note to delete")
            return
        current_title = current_item.text()
        note_id = self.get_note_id(current_title)

        if note_id is None:
            print(f"Could not find your note.")
            return

        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM Notes WHERE note_id = ?")
        query.addBindValue(note_id)
        query.exec()

        row = self.note_list.row(current_item)
        self.note_list.takeItem(row)
        self.text_area.clear()

        if self.note_list.count() == 0:
            self.delete_button.setEnabled(False)

    def on_checked(self, checked):
        app = QApplication.instance()

        if checked:
            app.setStyleSheet("""
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
    }
    QLineEdit, QTextEdit, QListWidget {
        background-color: #3c3f41;
        color: #f0f0f0;
        border: 1px solid #555;
        selection-background-color: #5a5a5a;
    }
    QPushButton {
        background-color: #444;
        color: #f0f0f0;
        border: 1px solid #666;
        padding: 5px;
    }
    QPushButton:hover:!disabled {
        background-color: #555;
    }
    QPushButton:pressed:!disabled {
        background-color: #333;
    }
    QPushButton:disabled {
        background-color: #2a2a2a;
        color: #777;
        border: 1px solid #444;
    }
    QCheckBox {
        spacing: 5px;
    }
""")
        else:
            app.setStyleSheet("")
    
    def load_note(self):
        current_item = self.note_list.currentItem()
        if current_item is None:
            return
        current_title = current_item.text()
        current_note_id = self.get_note_id(current_title)
        if current_note_id is None:
            QMessageBox.warning(self, "Load Error", "Note not found in DB.")
            return

        query = QSqlQuery(self.db)
        query.prepare("SELECT content FROM Notes WHERE note_id = ?")
        query.addBindValue(current_note_id)
        if not query.exec() or not query.next():
            QMessageBox.warning(self, "Load Error", "Could not load note content.")
            return

        current_content = query.value(0) or ""
        self.text_area.setText(current_content)

def open_notepad_window(username):
    app = QApplication.instance()

    notepad_window = Notepad(username)
    notepad_window.show()

    app.notepad = notepad_window


def main():
    app = QApplication(sys.argv)

    window = LoginForm()
    window.show()

    window.entry_successful.connect(open_notepad_window)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()