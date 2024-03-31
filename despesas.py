import sys
import json
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QListWidget, QMessageBox, QDialog, QInputDialog, QLabel, QLineEdit, QHBoxLayout, QTextEdit, QFileDialog, QStackedWidget, QComboBox
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush
from PyQt5.QtCore import Qt, QRect

class Despesa:
    def __init__(self, categoria, item, valor):
        self.categoria = categoria
        self.item = item
        self.valor = valor

class Categoria:
    def __init__(self, nome):
        self.nome = nome
        self.itens = []

    def adicionar_item(self, item, valor):
        self.itens.append((item, valor))

    def remover_item(self, item):
        for i, (nome_item, valor) in enumerate(self.itens):
            if nome_item == item:
                del self.itens[i]
                break

class GerenciadorDespesas:
    def __init__(self):
        self.categorias = []
        self.conn = sqlite3.connect("despesas.db")
        self.criar_tabela()

    def criar_tabela(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
                            id INTEGER PRIMARY KEY,
                            nome TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS itens (
                            id INTEGER PRIMARY KEY,
                            categoria_id INTEGER,
                            item TEXT,
                            valor REAL,
                            FOREIGN KEY(categoria_id) REFERENCES categorias(id))''')
        self.conn.commit()

    def adicionar_categoria(self, nome):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))
        self.conn.commit()

    def remover_categoria(self, nome):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM categorias WHERE nome=?", (nome,))
        self.conn.commit()

    def adicionar_item(self, categoria, item, valor):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM categorias WHERE nome=?", (categoria,))
        categoria_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO itens (categoria_id, item, valor) VALUES (?, ?, ?)", (categoria_id, item, valor))
        self.conn.commit()

    def remover_item(self, categoria, item):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM itens WHERE categoria_id IN (SELECT id FROM categorias WHERE nome=?) AND item=?", (categoria, item))
        self.conn.commit()

    def calcular_total_por_categoria(self):
        total_por_categoria = {}
        cursor = self.conn.cursor()
        cursor.execute("SELECT nome FROM categorias")
        categorias = cursor.fetchall()
        for cat_nome in categorias:
            cursor.execute("SELECT item, valor FROM itens WHERE categoria_id IN (SELECT id FROM categorias WHERE nome=?)", (cat_nome[0],))
            itens = cursor.fetchall()
            total_categoria = sum(item[1] for item in itens)
            total_por_categoria[cat_nome[0]] = total_categoria
        return total_por_categoria

    def resumo_geral(self):
        resumo_geral = ""
        total_geral = 0
        cursor = self.conn.cursor()
        cursor.execute("SELECT nome FROM categorias")
        categorias = cursor.fetchall()
        for cat_nome in categorias:
            cursor.execute("SELECT item, valor FROM itens WHERE categoria_id IN (SELECT id FROM categorias WHERE nome=?)", (cat_nome[0],))
            itens = cursor.fetchall()
            resumo_geral += f"{cat_nome[0]}:\n"
            for item, valor in itens:
                resumo_geral += f" - {item}: R$ {valor:.2f}\n"
                total_geral += valor
            resumo_geral += f"Total: R$ {sum(valor for _, valor in itens):.2f}\n\n"
        resumo_geral += f"Total Geral: R$ {total_geral:.2f}\n"
        return resumo_geral

class PaginaInicio(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.lista_categorias = QListWidget()
        layout.addWidget(self.lista_categorias)

class PaginaAdicionar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.btn_adicionar_categoria = QPushButton("Adicionar Categoria")
        self.btn_adicionar_categoria.clicked.connect(parent.adicionar_categoria)
        layout.addWidget(self.btn_adicionar_categoria)
        self.btn_adicionar_item = QPushButton("Adicionar Item")
        self.btn_adicionar_item.clicked.connect(parent.adicionar_item)
        layout.addWidget(self.btn_adicionar_item)

class PaginaRemover(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.btn_remover_categoria = QPushButton("Remover Categoria")
        self.btn_remover_categoria.clicked.connect(parent.remover_categoria)
        layout.addWidget(self.btn_remover_categoria)
        self.btn_remover_item = QPushButton("Remover Item")
        self.btn_remover_item.clicked.connect(parent.remover_item)
        layout.addWidget(self.btn_remover_item)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mairink Gerenciador De Despesas")  # Definindo o título da janela
        self.setGeometry(100, 100, 600, 400)  # Definindo o tamanho da janela
        self.setWindowFlag(Qt.FramelessWindowHint)  # Removendo a barra de título

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Widget do menu lateral
        self.menu_widget = QWidget()
        layout_menu = QVBoxLayout()
        self.menu_widget.setLayout(layout_menu)
        self.layout.addWidget(self.menu_widget)

        # Botões do menu lateral
        self.btn_inicio = QPushButton("Início")
        self.btn_adicionar = QPushButton("Adicionar")
        self.btn_remover = QPushButton("Remover")
        self.estilizar_botao(self.btn_inicio)
        self.estilizar_botao(self.btn_adicionar)
        self.estilizar_botao(self.btn_remover)

        # Adicionando os botões ao menu lateral
        layout_menu.addWidget(self.btn_inicio)
        layout_menu.addWidget(self.btn_adicionar)
        layout_menu.addWidget(self.btn_remover)
        layout_menu.addStretch(1)

        # Título
        self.titulo_label = QLabel("Mairink Gerenciador de Despesas")
        self.titulo_label.setAlignment(Qt.AlignCenter)
        self.titulo_label.setStyleSheet("font-size: 18px; color: white; margin-top: 10px; margin-bottom: 20px;")
        self.layout.addWidget(self.titulo_label)

        # Stack de páginas
        self.stacked_widget = QStackedWidget()
        self.pagina_inicio = PaginaInicio(self)
        self.pagina_adicionar = PaginaAdicionar(self)
        self.pagina_remover = PaginaRemover(self)
        self.stacked_widget.addWidget(self.pagina_inicio)
        self.stacked_widget.addWidget(self.pagina_adicionar)
        self.stacked_widget.addWidget(self.pagina_remover)
        self.layout.addWidget(self.stacked_widget)

        # Conectar botões à troca de página
        self.btn_inicio.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_adicionar.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_remover.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        # Gerenciador de despesas
        self.gerenciador_despesas = GerenciadorDespesas()

        # Variáveis para controle de movimento da janela
        self.dragging = False
        self.offset = None

        self.setStyleSheet("background-color: rgba(51, 51, 51, 200); color: white; border-radius: 10px;")

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def adicionar_categoria(self):
        nome_categoria, ok = QInputDialog.getText(self, "Adicionar Categoria", "Nome da Categoria:")
        if ok and nome_categoria:
            self.gerenciador_despesas.adicionar_categoria(nome_categoria)
            self.atualizar_lista_categorias()

    def remover_categoria(self):
        nome_categoria, ok = QInputDialog.getText(self, "Remover Categoria", "Nome da Categoria:")
        if ok and nome_categoria:
            self.gerenciador_despesas.remover_categoria(nome_categoria)
            self.atualizar_lista_categorias()

    def adicionar_item(self):
        dialog = AdicionarItemDialog(self.gerenciador_despesas)
        dialog.exec_()

    def remover_item(self):
        dialog = RemoverItemDialog(self.gerenciador_despesas)
        dialog.exec_()

    def atualizar_lista_categorias(self):
        self.pagina_inicio.lista_categorias.clear()
        for categoria in self.gerenciador_despesas.categorias:
            self.pagina_inicio.lista_categorias.addItem(categoria.nome)

    def mostrar_mensagem(self, mensagem):
        msg_box = QMessageBox()
        msg_box.setText(mensagem)
        msg_box.exec_()

    def estilizar_botao(self, botao):
        botao.setStyleSheet("QPushButton {"
                            "background-color: #444;"
                            "border: 2px solid #555;"
                            "border-radius: 5px;"
                            "color: white;"
                            "padding: 5px 10px;"
                            "}"
                            "QPushButton:hover {"
                            "background-color: #555;"
                            "}"
                            "QPushButton:pressed {"
                            "background-color: #666;"
                            "}")

class AdicionarItemDialog(QDialog):
    def __init__(self, gerenciador_despesas):
        super().__init__()
        self.setWindowTitle("Adicionar Item")
        self.gerenciador_despesas = gerenciador_despesas
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.combo_categorias = QComboBox()
        layout.addWidget(QLabel("Categoria:"))
        layout.addWidget(self.combo_categorias)
        self.input_item = QLineEdit()
        self.input_valor = QLineEdit()
        layout.addWidget(QLabel("Item:"))
        layout.addWidget(self.input_item)
        layout.addWidget(QLabel("Valor:"))
        layout.addWidget(self.input_valor)
        btn_adicionar = QPushButton("Adicionar")
        btn_adicionar.clicked.connect(self.adicionar_item)
        layout.addWidget(btn_adicionar)
        self.atualizar_combo_categorias()

    def atualizar_combo_categorias(self):
        self.combo_categorias.clear()
        for categoria in self.gerenciador_despesas.categorias:
            self.combo_categorias.addItem(categoria.nome)

    def adicionar_item(self):
        categoria_selecionada = self.combo_categorias.currentText()
        item = self.input_item.text()
        valor = float(self.input_valor.text().replace(",", "."))
        self.gerenciador_despesas.adicionar_item(categoria_selecionada, item, valor)
        self.accept()

class RemoverItemDialog(QDialog):
    def __init__(self, gerenciador_despesas):
        super().__init__()
        self.setWindowTitle("Remover Item")
        self.gerenciador_despesas = gerenciador_despesas
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.combo_categorias = QComboBox()
        layout.addWidget(QLabel("Categoria:"))
        layout.addWidget(self.combo_categorias)
        self.combo_itens = QComboBox()
        layout.addWidget(QLabel("Item:"))
        layout.addWidget(self.combo_itens)
        btn_remover = QPushButton("Remover")
        btn_remover.clicked.connect(self.remover_item)
        layout.addWidget(btn_remover)
        self.atualizar_combo_categorias()
        self.combo_categorias.currentIndexChanged.connect(self.atualizar_combo_itens)

    def atualizar_combo_categorias(self):
        self.combo_categorias.clear()
        for categoria in self.gerenciador_despesas.categorias:
            self.combo_categorias.addItem(categoria.nome)

    def atualizar_combo_itens(self):
        self.combo_itens.clear()
        categoria_selecionada = self.combo_categorias.currentText()
        for item, _ in self.gerenciador_despesas.categorias[self.combo_categorias.currentIndex()].itens:
            self.combo_itens.addItem(item)

    def remover_item(self):
        categoria_selecionada = self.combo_categorias.currentText()
        item_selecionado = self.combo_itens.currentText()
        self.gerenciador_despesas.remover_item(categoria_selecionada, item_selecionado)
        self.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
