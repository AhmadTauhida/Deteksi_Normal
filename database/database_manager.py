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
        """Menambahkan responden baru ke database MySQL dengan status berbasis teks VARCHAR."""
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

    # 3. DELETE RESPONDENT
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

    # ── DATA LOGGER TRANSACTIONS ──────────────────────────────────────────────

    def get_session_count(self, uid):
        """Menghitung total sesi yang sudah diselesaikan oleh responden untuk auto-increment UI."""
        query = "SELECT COUNT(*) as total FROM gait_sessions WHERE responden_uid = %s"
        count = 0
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (uid,))
            result = cursor.fetchone()
            if result:
                count = result['total']
        except Error as e:
            print(f"Error Database (COUNT SESSIONS): {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()
        return count

    def save_session_with_logs(self, uid, sesi_ke, jarak, waktu_total, avg_angle, max_angle, min_angle, list_sudut):
        """
        Menyimpan ringkasan data ke gait_sessions, lalu mem-bulk insert raw data logger ke gait_logs.
        Murni merekam data tanpa melakukan modifikasi pada tabel master responden.
        """
        query_session = """
            INSERT INTO gait_sessions 
            (responden_uid, sesi_ke, jarak_meter, waktu_detik_total, sudut_rata_rata, sudut_maksimum, sudut_minimum) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        query_logs = """
            INSERT INTO gait_logs 
            (session_id, frame_ke, waktu_relatif, sudut_ankle) 
            VALUES (%s, %s, %s, %s)
        """
        
        success = False
        conn = None
        try:
            conn = self._get_connection()
            conn.autocommit = False # Transaksi manual (Atomic)
            cursor = conn.cursor()

            # 1. Simpan Ringkasan Sesi ke tabel gait_sessions
            cursor.execute(query_session, (uid, sesi_ke, jarak, waktu_total, avg_angle, max_angle, min_angle))
            
            # 2. Dapatkan ID session yang baru saja terbuat
            session_id = cursor.lastrowid
            
            # 3. Bentuk data tuple array untuk logger per frame
            total_frames = len(list_sudut)
            interval_waktu = waktu_total / total_frames if total_frames > 0 else 0
            
            log_data_tuples = []
            for i, sudut in enumerate(list_sudut):
                frame_ke = i + 1
                waktu_relatif = frame_ke * interval_waktu
                log_data_tuples.append((session_id, frame_ke, waktu_relatif, float(sudut)))

            # 4. Bulk Insert ke tabel gait_logs
            cursor.executemany(query_logs, log_data_tuples)

            # 5. Commit transaksi
            conn.commit()
            success = True
            print(f"Berhasil logging sesi #{sesi_ke} dengan {total_frames} frame raw data.")

        except Error as e:
            if conn:
                conn.rollback()
            print(f"Error Database Transaction Data Logger: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
                
        return success

    def get_raw_gait_logs(self, uid):
        """
        Mengambil seluruh data logger mentah (per frame) dari tabel gait_logs 
        yang terhubung dengan semua sesi milik suatu responden tertentu untuk ekspor CSV.
        """
        query = """
            SELECT 
                s.sesi_ke, 
                l.frame_ke, 
                l.waktu_relatif, 
                l.sudut_ankle, 
                s.waktu_ambil
            FROM gait_logs l
            JOIN gait_sessions s ON l.session_id = s.id
            WHERE s.responden_uid = %s
            ORDER BY s.sesi_ke ASC, l.frame_ke ASC
        """
        logs = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (uid,))
            logs = cursor.fetchall()
        except Error as e:
            print(f"Error Database (GET RAW LOGS): {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        return logs