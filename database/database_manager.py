# database_manager.py
import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self):
        # Konfigurasi disesuaikan dengan profil default Laragon
        self.config = {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '',
            'database': 'db_ankle_analysis'
        }

    def _get_connection(self):
        """Membuka koneksi baru ke instance MySQL."""
        return mysql.connector.connect(**self.config)

    # 1. READ / GET ALL RESPONDENTS
    def get_all_respondents(self):
        """Mengambil semua data responden dari MySQL."""
        query = "SELECT uid, nama, tanggal_lahir, jenis_kelamin, status FROM responden"
        respondents = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True) # Mengembalikan data dalam bentuk dict Python
            cursor.execute(query)
            respondents = cursor.fetchall()
        except Error as e:
            print(f"Error Database (GET): {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()
        return respondents

    # 2. CREATE / POST NEW RESPONDENT
    def add_respondent(self, uid, nama, tanggal_lahir, jenis_kelamin, status='Normal'):
        """Menambahkan row responden baru ke database."""
        query = """
            INSERT INTO responden (uid, nama, tanggal_lahir, jenis_kelamin, status) 
            VALUES (%s, %s, %s, %s, %s)
        """
        success = False
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (uid, nama, tanggal_lahir, jenis_kelamin, status))
            conn.commit()
            success = True
        except Error as e:
            print(f"Error Database (POST): {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()
        return success

    # 3. UPDATE RESPONDENT STATUS
    def update_respondent_status(self, uid, new_status):
        """Memperbarui status kesehatan ankle responden berdasarkan UID."""
        query = "UPDATE responden SET status = %s WHERE uid = %s"
        success = False
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (new_status, uid))
            conn.commit()
            success = True
        except Error as e:
            print(f"Error Database (UPDATE): {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()
        return success

    # 4. DELETE RESPONDENT
    def delete_respondent(self, uid):
        """Menghapus data responden berdasarkan UID (Cascades ke tabel transaksi)."""
        query = "DELETE FROM responden WHERE uid = %s"
        success = False
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (uid,))
            conn.commit()
            success = True
        except Error as e:
            print(f"Error Database (DELETE): {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()
        return success