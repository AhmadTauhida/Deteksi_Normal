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

    # ── RESPONDENT CRUD ───────────────────────────────────────────────────────

    # 1. READ / GET ALL RESPONDENTS
    def get_all_respondents(self):
        """Mengambil semua data responden dari MySQL."""
        query = "SELECT uid, nama, tanggal_lahir, jenis_kelamin, status FROM responden"
        respondents = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
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

    def save_session_with_logs(self, uid, sesi_ke, jarak, waktu_total,
                               avg_angle, max_angle, min_angle, list_sudut):
        """
        Menyimpan ringkasan sesi ke gait_sessions, lalu bulk insert raw data
        logger ke gait_logs.

        Parameter list_sudut berisi list of tuple: (sudut: float, waktu_ambil: datetime).
        waktu_ambil diambil tepat saat frame diterima di UI thread (bukan dihitung mundur),
        sehingga timestamp mencerminkan waktu perekaman yang sesungguhnya.
        """
        query_session = """
            INSERT INTO gait_sessions 
            (responden_uid, sesi_ke, jarak_meter, waktu_detik_total,
             sudut_rata_rata, sudut_maksimum, sudut_minimum) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        # waktu_ambil diisi eksplisit dari Python (bukan DEFAULT MySQL)
        # agar timestamp mencerminkan waktu aktual saat frame diproses.
        query_logs = """
            INSERT INTO gait_logs 
            (session_id, frame_ke, sudut_ankle, waktu_ambil) 
            VALUES (%s, %s, %s, %s)
        """

        success = False
        conn = None
        try:
            conn = self._get_connection()
            conn.autocommit = False  # Transaksi manual (Atomic)
            cursor = conn.cursor()

            # 1. Simpan ringkasan sesi ke tabel gait_sessions
            cursor.execute(
                query_session,
                (uid, sesi_ke, jarak, waktu_total, avg_angle, max_angle, min_angle)
            )

            # 2. Dapatkan ID session yang baru saja terbuat
            session_id = cursor.lastrowid

            # 3. Bentuk data tuple array untuk bulk insert
            #    list_sudut adalah list of (sudut: float, waktu_ambil: datetime)
            log_data_tuples = []
            for i, item in enumerate(list_sudut):
                frame_ke = i + 1

                # Unpack tuple — sudut dan timestamp aktual dari UI thread
                if isinstance(item, tuple):
                    sudut, waktu_ambil = item
                else:
                    # Fallback backward-compatible jika masih float biasa
                    sudut = item
                    waktu_ambil = None

                log_data_tuples.append(
                    (session_id, frame_ke, float(sudut), waktu_ambil)
                )

            # 4. Bulk insert ke tabel gait_logs
            cursor.executemany(query_logs, log_data_tuples)

            # 5. Commit seluruh transaksi sekaligus
            conn.commit()
            success = True
            print(
                f"[DB] Berhasil logging sesi #{sesi_ke} "
                f"dengan {len(log_data_tuples)} frame raw data."
            )

        except Error as e:
            if conn:
                conn.rollback()
            print(f"[DB] Error Transaction Data Logger: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

        return success

    def get_raw_gait_logs(self, uid, sesi_ke=None):
        """
        Mengambil data logger mentah (per frame) dari tabel gait_logs
        yang terhubung dengan sesi milik suatu responden untuk ekspor CSV.

        Parameter:
          - uid     : UID responden (wajib)
          - sesi_ke : nomor sesi yang ingin diambil; jika None, ambil semua sesi

        Kolom yang dikembalikan:
          - sesi_ke         : nomor urut sesi
          - frame_ke        : nomor urut frame dalam sesi
          - sudut_ankle     : sudut terukur (float)
          - waktu_ambil     : timestamp aktual saat frame direkam (TIMESTAMP(3))
          - waktu_sesi      : timestamp saat sesi dibuat (dari gait_sessions.waktu_ambil)
        """
        if sesi_ke is not None:
            query = """
                SELECT
                    s.sesi_ke,
                    l.frame_ke,
                    l.sudut_ankle,
                    l.waktu_ambil,
                    s.waktu_ambil AS waktu_sesi
                FROM gait_logs l
                JOIN gait_sessions s ON l.session_id = s.id
                WHERE s.responden_uid = %s
                  AND s.sesi_ke = %s
                ORDER BY l.frame_ke ASC
            """
            params = (uid, sesi_ke)
        else:
            query = """
                SELECT
                    s.sesi_ke,
                    l.frame_ke,
                    l.sudut_ankle,
                    l.waktu_ambil,
                    s.waktu_ambil AS waktu_sesi
                FROM gait_logs l
                JOIN gait_sessions s ON l.session_id = s.id
                WHERE s.responden_uid = %s
                ORDER BY s.sesi_ke ASC, l.frame_ke ASC
            """
            params = (uid,)

        logs = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            logs = cursor.fetchall()
        except Error as e:
            print(f"[DB] Error GET RAW LOGS: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        return logs