import sys
import json
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (
    QMessageBox, QComboBox, QTableWidgetItem, QHBoxLayout,
    QWidget, QPushButton, QLineEdit, QHeaderView, QLabel
)
from PyQt5.QtCore import Qt, QDate, QSize
import pymysql

# ===================== CỠ CHỮ (px) =====================
CO_CHU_THUONG = 15
CO_CHU_TIEU_DE = 28
CO_CHU_MENU = 16
CO_CHU_BANG = 15
CAO_DONG_BANG = 52
# ========================================================

def them_style(widget, qss):
    """Nối thêm style, không ghi đè style gốc trong file .ui."""
    cu = widget.styleSheet().strip()
    if cu and "{" not in cu:
        cu = "* { " + cu + " }"
    widget.setStyleSheet(cu + "\n" + qss)

class NhapNguyenLieuWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Lấy đường dẫn tuyệt đối của thư mục chứa file main.py hiện tại
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ui_path = os.path.join(base_dir, "cafe.ui")
        self.draft_path = os.path.join(base_dir, "draft.json")
        
        # Đưa thư mục làm việc về đúng thư mục chứa script để load ảnh/icon trong UI
        os.chdir(base_dir)
        uic.loadUi(self.ui_path, self)
        
        # Đồng bộ giao diện
        self.chinh_giao_dien()
        
        # Cấu hình bảng 6 cột
        self.tableChiTiet.setColumnCount(6)
        self.tableChiTiet.setHorizontalHeaderLabels([
            "STT", "Nguyên liệu", "Số lượng",
            "Đơn giá nhập", "Thành tiền", "Thao tác"
        ])
        self.tableChiTiet.verticalHeader().setVisible(False)
        self.tableChiTiet.setAlternatingRowColors(True)
        self.tableChiTiet.setShowGrid(True)
        self.tableChiTiet.setWordWrap(False)
        self.tableChiTiet.setMinimumHeight(300)
        
        them_style(self.tableChiTiet, f"""
            QTableWidget {{ font-size: {CO_CHU_BANG}px; }}
            QHeaderView::section {{ font-size: {CO_CHU_BANG}px; }}
            QTableWidget::item {{ padding: 5px; border-bottom: 1px solid #EFE7DE; }}
            QTableWidget::item:selected {{ background-color: #E8D8C6; color: #49372B; }}
        """)
        self.cau_hinh_do_rong_cot()
        
        # Gắn sự kiện cho các nút chức năng
        self.btnThemDong.clicked.connect(self.them_dong_moi)
        self.btnLamMoi.clicked.connect(self.lam_moi_form)
        self.btnLuuPhieuNhap.clicked.connect(self.luu_phieu_nhap)
        
        # Gắn sự kiện mở màn hình Tìm kiếm đơn hàng từ menu bên trái
        for btn in self.findChildren(QPushButton):
            text = btn.text().strip().lower()
            if text in ("tìm kiếm", "tìm kiếm đơn hàng"):
                btn.clicked.connect(self.mo_tim_kiem)
            elif text in ("đơn hàng", "lập đơn hàng"):
                btn.clicked.connect(self.mo_lap_don_hang)

        # Lắng nghe sự kiện để tự động lưu nháp
        self.txtMaPhieuNhap.textChanged.connect(self.save_draft)
        self.dateNgayNhap.dateChanged.connect(self.save_draft)
        self.cbNhaCungCap.currentIndexChanged.connect(self.save_draft)
        self.cbNhanVienNhap.currentIndexChanged.connect(self.save_draft)

        # Load dữ liệu danh mục từ database
        self.load_combobox_data()
        self.danh_sach_nguyen_lieu = self.lay_danh_sach_nguyen_lieu()

        # Khôi phục lại bản nháp cũ nếu có
        self.load_draft()

    def mo_tim_kiem(self):
        """Mở màn Tìm kiếm đơn hàng và đóng màn hình nhập nguyên liệu hiện tại."""
        from tim_kiem_don_hang import TimKiemDonHangWindow
        self.cua_so = TimKiemDonHangWindow()
        self.cua_so.show()
        self.close()

    def mo_lap_don_hang(self):
        """Mở màn hình Lập đơn hàng và đồng bộ kích thước cửa sổ."""
        from lap_don_hang import LapDonHangWindow
        self.cua_so = LapDonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()
    def chinh_giao_dien(self):
        """Đồng bộ giao diện theo tông kem - nâu cà phê."""
        them_style(self, f"""
            QMainWindow, QWidget {{
                font-family: "Segoe UI";
                color: #49372B;
            }}
            QMainWindow {{ background-color: #F7F3ED; }}
            QLabel {{ color: #604936; font-size: {CO_CHU_THUONG}px; }}
            QLineEdit, QComboBox, QDateEdit {{
                background-color: #FFFEFC;
                border: 1px solid #DFD2C3;
                border-radius: 7px;
                padding: 6px 9px;
                min-height: 28px;
                font-size: {CO_CHU_THUONG}px;
            }}
            QPushButton {{
                background-color: #F0E6D9;
                color: #604936;
                border: none;
                border-radius: 7px;
                padding: 8px 12px;
                min-height: 28px;
                font-size: {CO_CHU_THUONG}px;
            }}
            QPushButton:hover {{ background-color: #E4D3C0; }}
        """)
        
        for label in self.findChildren(QLabel):
            text = label.text().strip().lower()
            if text == "nhập nguyên liệu / phiếu nhập":
                them_style(label, f"QLabel {{ font-size: {CO_CHU_TIEU_DE}px; font-weight: 700; color: #3E2C20; }}")

        for button in self.findChildren(QPushButton):
            text = button.text().strip().lower()
            if text in ("lưu phiếu nhập", "lưu"):
                them_style(button, f"QPushButton {{ background: #79583F; color: white; border-radius: 7px; padding: 9px 15px; font-weight: 600; }}")
            elif text in ("xóa dòng", "xóa"):
                them_style(button, f"QPushButton {{ background: #F9E3E0; color: #A33C35; border-radius: 7px; padding: 7px 12px; }}")
            elif text == "sửa":
                them_style(button, f"QPushButton {{ background: #EADBC9; color: #604936; border-radius: 6px; padding: 6px 10px; }}")
            elif text in ("đơn hàng", "nguyên liệu", "tìm kiếm", "báo cáo", "doanh thu"):
                button.setMinimumHeight(46)
                them_style(button, f"QPushButton {{ background: transparent; color: #604936; text-align: left; border-radius: 7px; padding: 9px 14px; font-size: {CO_CHU_MENU}px; }} QPushButton:hover {{ background: #EAE0D3; }}")

    def cau_hinh_do_rong_cot(self):
        header = self.tableChiTiet.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 64)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 175)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 160)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 145)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.resizeSection(5, 170)

    def connect_db(self):
        try:
            return pymysql.connect(
                host='localhost', user='root', password='123456789',
                database='Cafe', charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối đến cơ sở dữ liệu:\n{e}")
            return None

    def load_combobox_data(self):
        conn = self.connect_db()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT MaNCC, TenNCC FROM nha_cung_cap")
                self.cbNhaCungCap.blockSignals(True)
                self.cbNhaCungCap.clear()
                self.cbNhaCungCap.addItem("-- Chọn nhà cung cấp --", None)
                for ncc in cur.fetchall():
                    self.cbNhaCungCap.addItem(ncc['TenNCC'], ncc['MaNCC'])
                self.cbNhaCungCap.blockSignals(False)

                cur.execute("SELECT MaNV, HoTen FROM nhan_vien")
                self.cbNhanVienNhap.blockSignals(True)
                self.cbNhanVienNhap.clear()
                self.cbNhanVienNhap.addItem("-- Chọn nhân viên nhập --", None)
                for nv in cur.fetchall():
                    self.cbNhanVienNhap.addItem(nv['HoTen'], nv['MaNV'])
                self.cbNhanVienNhap.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tải dữ liệu danh mục:\n{e}")
        finally:
            conn.close()

    def lay_danh_sach_nguyen_lieu(self):
        conn = self.connect_db()
        if not conn: return []
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT MaNL, TenNL, DonViTinh FROM nguyen_lieu")
                return cur.fetchall()
        except Exception:
            return []
        finally:
            conn.close()

    def cap_nhat_stt(self):
        for row in range(self.tableChiTiet.rowCount()):
            item_stt = QTableWidgetItem(f"{row + 1:02d}")
            item_stt.setTextAlignment(Qt.AlignCenter)
            item_stt.setFlags(item_stt.flags() ^ Qt.ItemIsEditable)
            self.tableChiTiet.setItem(row, 0, item_stt)

    def tao_o_so_luong(self, dong):
        khung = QWidget()
        layout = QHBoxLayout(khung)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(5)

        o_so_luong = QLineEdit()
        o_so_luong.setPlaceholderText("Số lượng")
        o_so_luong.setAlignment(Qt.AlignCenter)
        o_so_luong.setStyleSheet(f"QLineEdit {{ font-size: {CO_CHU_BANG}px; }}")
        o_so_luong.textChanged.connect(lambda _, r=dong: self.tinh_thanh_tien_row(r))
        o_so_luong.textChanged.connect(self.save_draft)

        cb_don_vi = QComboBox()
        cb_don_vi.addItems(["kg", "g", "lít", "gói", "chai"])
        cb_don_vi.setStyleSheet(f"QComboBox {{ font-size: {CO_CHU_BANG}px; }}")
        cb_don_vi.currentIndexChanged.connect(self.save_draft)

        layout.addWidget(o_so_luong, 2)
        layout.addWidget(cb_don_vi, 1)
        self.tableChiTiet.setCellWidget(dong, 2, khung)

    def chon_nguyen_lieu_change(self, row, combo):
        data = combo.currentData()
        if data:
            _, don_vi = data
            widget_sl = self.tableChiTiet.cellWidget(row, 2)
            if widget_sl:
                cb_don_vi = widget_sl.layout().itemAt(1).widget()
                index = cb_don_vi.findText(don_vi)
                if index >= 0:
                    cb_don_vi.setCurrentIndex(index)
        self.save_draft()

    def tinh_thanh_tien_row(self, row):
        try:
            widget_sl = self.tableChiTiet.cellWidget(row, 2)
            txt_dongia = self.tableChiTiet.cellWidget(row, 3)
            if widget_sl and txt_dongia:
                o_so_luong = widget_sl.layout().itemAt(0).widget()
                sl_val = float(o_so_luong.text().strip()) if o_so_luong.text().strip() else 0
                dg_val = float(txt_dongia.text().strip()) if txt_dongia.text().strip() else 0
                thanh_tien = sl_val * dg_val
                thanh_tien_str = f"{thanh_tien:,.0f}".replace(",", ".")
                item_tt = self.tableChiTiet.item(row, 4)
                if not item_tt:
                    item_tt = QTableWidgetItem(thanh_tien_str)
                    self.tableChiTiet.setItem(row, 4, item_tt)
                else:
                    item_tt.setText(thanh_tien_str)
        except ValueError:
            pass

    def them_dong_moi(self):
        row = self.tableChiTiet.rowCount()
        self.tableChiTiet.insertRow(row)
        self.tableChiTiet.setRowHeight(row, CAO_DONG_BANG)
        
        self.cap_nhat_stt()
        
        combo_nl = QComboBox()
        combo_nl.setStyleSheet(f"QComboBox {{ font-size: {CO_CHU_BANG}px; }}")
        combo_nl.addItem("-- Chọn nguyên liệu --", None)
        for nl in self.danh_sach_nguyen_lieu:
            combo_nl.addItem(nl['TenNL'], (nl['MaNL'], nl['DonViTinh']))
        combo_nl.currentIndexChanged.connect(lambda _, r=row, cb=combo_nl: self.chon_nguyen_lieu_change(r, cb))
        self.tableChiTiet.setCellWidget(row, 1, combo_nl)
        
        self.tao_o_so_luong(row)
        
        txt_dongia = QLineEdit()
        txt_dongia.setPlaceholderText("Đơn giá")
        txt_dongia.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        txt_dongia.setStyleSheet(f"QLineEdit {{ font-size: {CO_CHU_BANG}px; }}")
        txt_dongia.textChanged.connect(lambda _, r=row: self.tinh_thanh_tien_row(r))
        txt_dongia.textChanged.connect(self.save_draft)
        self.tableChiTiet.setCellWidget(row, 3, txt_dongia)
        
        item_tt = QTableWidgetItem("0")
        item_tt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_tt.setFlags(item_tt.flags() ^ Qt.ItemIsEditable)
        self.tableChiTiet.setItem(row, 4, item_tt)
        
        khung_nut = QWidget()
        layout_nut = QHBoxLayout(khung_nut)
        layout_nut.setContentsMargins(3, 3, 3, 3)
        layout_nut.setSpacing(5)
        btn_sua = QPushButton("Sửa")
        btn_xoa = QPushButton("Xóa")
        btn_sua.setStyleSheet("background-color: #E8D9CA; color: #68452D; border: none; border-radius: 5px; padding: 6px;")
        btn_xoa.setStyleSheet("background-color: #F9DDDD; color: #D94343; border: none; border-radius: 5px; padding: 6px;")

        btn_sua.clicked.connect(lambda _, r=row: self.sua_dong(r))
        btn_xoa.clicked.connect(lambda _, r=row: self.xoa_dong(r))

        layout_nut.addWidget(btn_sua)
        layout_nut.addWidget(btn_xoa)
        self.tableChiTiet.setCellWidget(row, 5, khung_nut)
        self.save_draft()

    def sua_dong(self, row):
        QMessageBox.information(self, "Thông báo", f"Đang thao tác chỉnh sửa dòng {row + 1}")

    def xoa_dong(self, row):
        self.tableChiTiet.removeRow(row)
        self.cap_nhat_stt()
        self.save_draft()

    def lam_moi_form(self):
        self.txtMaPhieuNhap.clear()
        self.dateNgayNhap.setDate(QDate.currentDate())
        if self.cbNhaCungCap.count() > 0: self.cbNhaCungCap.setCurrentIndex(0)
        if self.cbNhanVienNhap.count() > 0: self.cbNhanVienNhap.setCurrentIndex(0)
        self.tableChiTiet.setRowCount(0)
        if os.path.exists(self.draft_path):
            try: os.remove(self.draft_path)
            except Exception: pass

    def save_draft(self):
        try:
            draft_data = {
                "ma_phieu": self.txtMaPhieuNhap.text(),
                "ngay_nhap": self.dateNgayNhap.date().toString("yyyy-MM-dd"),
                "ncc_index": self.cbNhaCungCap.currentIndex(),
                "nv_index": self.cbNhanVienNhap.currentIndex(),
                "rows": []
            }
            for row in range(self.tableChiTiet.rowCount()):
                combo_nl = self.tableChiTiet.cellWidget(row, 1)
                nl_index = combo_nl.currentIndex() if combo_nl else 0
                widget_sl = self.tableChiTiet.cellWidget(row, 2)
                soluong, donvi_index = "", 0
                if widget_sl:
                    soluong = widget_sl.layout().itemAt(0).widget().text()
                    donvi_index = widget_sl.layout().itemAt(1).widget().currentIndex()
                txt_dg = self.tableChiTiet.cellWidget(row, 3)
                dongia = txt_dg.text() if txt_dg else ""
                draft_data["rows"].append({"nl_index": nl_index, "soluong": soluong, "donvi_index": donvi_index, "dongia": dongia})
            with open(self.draft_path, "w", encoding="utf-8") as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Lỗi lưu nháp:", e)

    def closeEvent(self, event):
        self.save_draft()
        event.accept()

    def load_draft(self):
        if not os.path.exists(self.draft_path): return
        try:
            with open(self.draft_path, "r", encoding="utf-8") as f:
                draft_data = json.load(f)
            self.txtMaPhieuNhap.setText(draft_data.get("ma_phieu", ""))
            ngay_str = draft_data.get("ngay_nhap", "")
            if ngay_str: self.dateNgayNhap.setDate(QDate.fromString(ngay_str, "yyyy-MM-dd"))
            if self.cbNhaCungCap.count() > draft_data.get("ncc_index", 0):
                self.cbNhaCungCap.setCurrentIndex(draft_data.get("ncc_index", 0))
            if self.cbNhanVienNhap.count() > draft_data.get("nv_index", 0):
                self.cbNhanVienNhap.setCurrentIndex(draft_data.get("nv_index", 0))
            for row_data in draft_data.get("rows", []):
                self.them_dong_moi()
                row = self.tableChiTiet.rowCount() - 1
                combo_nl = self.tableChiTiet.cellWidget(row, 1)
                if combo_nl and combo_nl.count() > row_data.get("nl_index", 0):
                    combo_nl.setCurrentIndex(row_data.get("nl_index", 0))
                widget_sl = self.tableChiTiet.cellWidget(row, 2)
                if widget_sl:
                    widget_sl.layout().itemAt(0).widget().setText(row_data.get("soluong", ""))
                    cb_dv = widget_sl.layout().itemAt(1).widget()
                    if cb_dv.count() > row_data.get("donvi_index", 0):
                        cb_dv.setCurrentIndex(row_data.get("donvi_index", 0))
                txt_dg = self.tableChiTiet.cellWidget(row, 3)
                if txt_dg: txt_dg.setText(row_data.get("dongia", ""))
        except Exception as e:
            print("Lỗi load nháp:", e)

    def luu_phieu_nhap(self):
        ma_phieu = self.txtMaPhieuNhap.text().strip()
        ngay_nhap = self.dateNgayNhap.date().toString("yyyy-MM-dd")
        ma_ncc = self.cbNhaCungCap.currentData()
        ma_nv = self.cbNhanVienNhap.currentData()

        if not ma_phieu:
            QMessageBox.warning(self, "Cảnh báo", "Mã phiếu nhập không được để trống!")
            self.txtMaPhieuNhap.setFocus()
            return
        if not ma_ncc:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Nhà cung cấp hợp lệ!")
            self.cbNhaCungCap.setFocus()
            return
        if not ma_nv:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Nhân viên nhập hợp lệ!")
            self.cbNhanVienNhap.setFocus()
            return

        row_count = self.tableChiTiet.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Cảnh báo", "Phiếu nhập phải có ít nhất một dòng nguyên liệu chi tiết!")
            return

        chi_tiet_list = []
        tong_tien_phieu = 0

        for row in range(row_count):
            combo_nl = self.tableChiTiet.cellWidget(row, 1)
            ma_nl_data = combo_nl.currentData() if combo_nl else None
            ma_nl = ma_nl_data[0] if ma_nl_data else None
            widget_sl = self.tableChiTiet.cellWidget(row, 2)
            o_so_luong = widget_sl.layout().itemAt(0).widget() if widget_sl else None
            txt_dongia = self.tableChiTiet.cellWidget(row, 3)

            if not ma_nl:
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Vui lòng chọn nguyên liệu!")
                return
            if not o_so_luong or not o_so_luong.text().strip():
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Số lượng không được để trống!")
                return
            if not txt_dongia or not txt_dongia.text().strip():
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Đơn giá nhập không được để trống!")
                return

            try:
                so_luong = float(o_so_luong.text().strip())
                don_gia = float(txt_dongia.text().strip())
                if so_luong <= 0 or don_gia < 0:
                    QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Số lượng phải > 0 và đơn giá không được âm!")
                    return
            except ValueError:
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Định dạng số không hợp lệ!")
                return

            tong_tien_phieu += so_luong * don_gia
            chi_tiet_list.append({"MaNL": ma_nl, "SoLuong": so_luong, "DonGiaNhap": don_gia})

        connection = self.connect_db()
        if not connection: return

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT MaPN FROM phieu_nhap WHERE MaPN = %s", (ma_phieu,))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Cảnh báo", f"Mã phiếu nhập '{ma_phieu}' đã tồn tại trong hệ thống!")
                    return

                sql_phieu = "INSERT INTO phieu_nhap (MaPN, NgayNhap, MaNCC, MaNV, TongTien, GhiChu) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_phieu, (ma_phieu, ngay_nhap, ma_ncc, ma_nv, tong_tien_phieu, "Nhập kho nguyên liệu"))

                sql_ct = "INSERT INTO chi_tiet_phieu_nhap (MaPN, MaNL, SoLuong, DonGiaNhap) VALUES (%s, %s, %s, %s)"
                for ct in chi_tiet_list:
                    cursor.execute(sql_ct, (ma_phieu, ct['MaNL'], ct['SoLuong'], ct['DonGiaNhap']))
                    cursor.execute("UPDATE nguyen_lieu SET SoLuongTon = SoLuongTon + %s, DonGia = %s WHERE MaNL = %s", 
                                   (ct['SoLuong'], ct['DonGiaNhap'], ct['MaNL']))

            connection.commit()
            self.save_draft()
            QMessageBox.information(self, "Thành công", f"Đã lưu phiếu nhập [{ma_phieu}] thành công vào CSDL!")
        except Exception as e:
            connection.rollback()
            QMessageBox.critical(self, "Lỗi Database", f"Đã xảy ra lỗi khi lưu:\n{str(e)}")
        finally:
            connection.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = NhapNguyenLieuWindow()
    window.show()
    sys.exit(app.exec_())