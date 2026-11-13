"""
SuratKu - Generator Surat & Arsip Digital untuk Sekolah dan Kantor
Flask + SQLite (file suratku.db dibuat otomatis)
"""
import json
import os
import sqlite3
from datetime import date

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, url_for)

app = Flask(__name__)
app.secret_key = "ganti-kunci-rahasia-ini"
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suratku.db")
ROMAWI = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# Kolom umum yang ada di semua surat
COMMON = [
    ("instansi", "Nama instansi / sekolah (kop surat)", "text"),
    ("alamat", "Alamat instansi", "text"),
    ("kota", "Kota", "text"),
    ("tanggal", "Tanggal surat", "date"),
    ("ttd_nama", "Nama penandatangan", "text"),
    ("ttd_jabatan", "Jabatan penandatangan", "text"),
]

# Template surat. Placeholder {nama_kolom} akan diisi otomatis.
SURAT = {
    "izin": {
        "nama": "Surat Izin Tidak Masuk", "kategori": "Sekolah", "ikon": "bi-mortarboard-fill",
        "kode": "SI", "hal": "Permohonan Izin", "kepada": "Wali Kelas {kelas}\n{instansi}",
        "fields": [("nama", "Nama siswa", "text"), ("kelas", "Kelas", "text"),
                   ("tgl_izin", "Mulai tanggal", "date"), ("lama", "Lama izin (hari)", "number"),
                   ("alasan", "Alasan izin", "text")],
        "defaults": {"instansi": "SMA Negeri 1 Contoh", "alamat": "Jl. Pendidikan No. 10", "kota": "Jakarta",
                     "ttd_nama": "Hendra Saputra", "ttd_jabatan": "Orang Tua/Wali Murid",
                     "nama": "Andi Saputra", "kelas": "XI IPA 2", "lama": "2", "alasan": "sakit demam"},
        "isi": "Dengan hormat,\n\nYang bertanda tangan di bawah ini, orang tua/wali dari:\n\nNama : {nama}\nKelas : {kelas}\n\nmemohon izin agar putra/putri kami tidak dapat mengikuti kegiatan belajar mengajar selama {lama} hari, mulai tanggal {tgl_izin}, karena {alasan}.\n\nDemikian surat ini kami sampaikan. Atas perhatian dan pengertian Bapak/Ibu, kami ucapkan terima kasih.",
    },
    "undangan": {
        "nama": "Surat Undangan Rapat", "kategori": "Kantor & Sekolah", "ikon": "bi-calendar-event-fill",
        "kode": "SU", "hal": "Undangan Rapat", "kepada": "Bapak/Ibu {peserta}\ndi Tempat",
        "fields": [("peserta", "Peserta undangan", "text"), ("tgl_rapat", "Tanggal rapat", "date"),
                   ("waktu", "Waktu", "text"), ("tempat", "Tempat", "text"), ("agenda", "Agenda rapat", "text")],
        "defaults": {"instansi": "PT Maju Bersama", "alamat": "Jl. Sudirman No. 45", "kota": "Jakarta",
                     "ttd_nama": "Ratna Dewi, S.E.", "ttd_jabatan": "Manajer Operasional",
                     "peserta": "Seluruh Kepala Divisi", "waktu": "09.00 WIB - selesai",
                     "tempat": "Ruang Rapat Lantai 3", "agenda": "Evaluasi kinerja triwulan"},
        "isi": "Dengan hormat,\n\nSehubungan dengan agenda {agenda}, kami mengundang Bapak/Ibu untuk hadir pada:\n\nHari/Tanggal : {tgl_rapat}\nWaktu : {waktu}\nTempat : {tempat}\nAgenda : {agenda}\n\nMengingat pentingnya acara tersebut, kami mohon kehadiran Bapak/Ibu tepat waktu. Atas perhatian dan kehadirannya, kami ucapkan terima kasih.",
    },
    "keterangan": {
        "nama": "Surat Keterangan Kerja", "kategori": "Kantor", "ikon": "bi-briefcase-fill",
        "kode": "SKK", "hal": "Surat Keterangan Kerja", "kepada": "Yang Berkepentingan",
        "fields": [("nama", "Nama karyawan", "text"), ("nik", "NIK/NIP", "text"),
                   ("jabatan", "Jabatan", "text"), ("tgl_masuk", "Tanggal mulai bekerja", "date")],
        "defaults": {"instansi": "PT Maju Bersama", "alamat": "Jl. Sudirman No. 45", "kota": "Jakarta",
                     "ttd_nama": "Ratna Dewi, S.E.", "ttd_jabatan": "Manajer HRD",
                     "nama": "Budi Prasetyo", "nik": "2021-0457", "jabatan": "Staf Administrasi"},
        "isi": "Yang bertanda tangan di bawah ini menerangkan bahwa:\n\nNama : {nama}\nNIK/NIP : {nik}\nJabatan : {jabatan}\n\nadalah benar karyawan {instansi} yang bekerja sejak {tgl_masuk} sampai dengan surat ini dibuat, dan selama bekerja yang bersangkutan menunjukkan kinerja yang baik.\n\nDemikian surat keterangan ini dibuat untuk dipergunakan sebagaimana mestinya.",
    },
    "permohonan": {
        "nama": "Surat Permohonan Resmi", "kategori": "Kantor & Sekolah", "ikon": "bi-envelope-paper-fill",
        "kode": "SP", "hal": "{hal}", "kepada": "{tujuan}\ndi Tempat",
        "fields": [("tujuan", "Ditujukan kepada", "text"), ("hal", "Perihal", "text"),
                   ("uraian", "Isi permohonan", "textarea")],
        "defaults": {"instansi": "SMK Teknologi Nusantara", "alamat": "Jl. Merdeka No. 7", "kota": "Jakarta",
                     "ttd_nama": "Drs. Slamet Riyadi", "ttd_jabatan": "Kepala Sekolah",
                     "tujuan": "Direktur PT Maju Bersama", "hal": "Permohonan Izin Kunjungan Industri",
                     "uraian": "kami bermaksud mengadakan kunjungan industri bagi siswa kelas XII pada bulan depan guna menambah wawasan dunia kerja. Untuk itu kami mohon kesediaan Bapak/Ibu menerima rombongan kami."},
        "isi": "Dengan hormat,\n\nDengan surat ini {uraian}\n\nDemikian permohonan ini kami sampaikan. Atas perhatian dan kerja sama Bapak/Ibu, kami ucapkan terima kasih.",
    },
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_e):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""CREATE TABLE IF NOT EXISTS letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nomor TEXT NOT NULL, jenis TEXT NOT NULL,
        judul TEXT NOT NULL, data TEXT NOT NULL, dibuat TEXT NOT NULL)""")
    db.commit()
    db.close()


@app.route("/")
def index():
    db = get_db()
    bulan = date.today().strftime("%Y-%m")
    total = db.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
    bulan_ini = db.execute("SELECT COUNT(*) FROM letters WHERE substr(dibuat,1,7)=?", (bulan,)).fetchone()[0]
    per_jenis = {r["jenis"]: r["n"] for r in db.execute("SELECT jenis, COUNT(*) n FROM letters GROUP BY jenis")}
    terbaru = db.execute("SELECT * FROM letters ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("index.html", surat=SURAT, total=total, bulan_ini=bulan_ini,
                           per_jenis=per_jenis, terbaru=terbaru)


@app.route("/buat/<jenis>")
def buat(jenis):
    tpl = SURAT.get(jenis) or abort(404)
    nilai = dict(tpl["defaults"], tanggal=date.today().isoformat())
    return render_template("form.html", jenis=jenis, tpl=tpl, common=COMMON, nilai=nilai)


@app.route("/simpan/<jenis>", methods=["POST"])
def simpan(jenis):
    tpl = SURAT.get(jenis) or abort(404)
    data = {k: request.form.get(k, "").strip() for k, _, _ in COMMON + tpl["fields"]}
    if not all(data[k] for k, _, _ in tpl["fields"]) or not data["ttd_nama"]:
        flash("Lengkapi semua kolom isian surat terlebih dahulu.", "danger")
        return redirect(url_for("buat", jenis=jenis))
    db = get_db()
    tgl = date.fromisoformat(data["tanggal"] or date.today().isoformat())
    urut = db.execute("SELECT COUNT(*) FROM letters WHERE jenis=? AND substr(dibuat,1,4)=?",
                      (jenis, str(tgl.year))).fetchone()[0] + 1
    data["nomor"] = f"{urut:03d}/{tpl['kode']}/{ROMAWI[tgl.month - 1]}/{tgl.year}"
    cur = db.execute("INSERT INTO letters (nomor, jenis, judul, data, dibuat) VALUES (?,?,?,?,?)",
                     (data["nomor"], jenis, tpl["nama"], json.dumps(data), tgl.isoformat()))
    db.commit()
    flash(f"Surat tersimpan dengan nomor {data['nomor']}.", "success")
    return redirect(url_for("lihat", sid=cur.lastrowid))


@app.route("/surat/<int:sid>")
def lihat(sid):
    row = get_db().execute("SELECT * FROM letters WHERE id=?", (sid,)).fetchone() or abort(404)
    return render_template("view.html", row=row, tpl=SURAT[row["jenis"]], data=json.loads(row["data"]))


@app.route("/surat/<int:sid>/hapus", methods=["POST"])
def hapus(sid):
    db = get_db()
    db.execute("DELETE FROM letters WHERE id=?", (sid,))
    db.commit()
    flash("Surat dihapus dari arsip.", "warning")
    return redirect(url_for("arsip"))


@app.route("/arsip")
def arsip():
    q = request.args.get("q", "").strip()
    jenis = request.args.get("jenis", "")
    rows = get_db().execute(
        """SELECT * FROM letters WHERE (? = '' OR jenis = ?)
           AND (nomor LIKE ? OR judul LIKE ? OR data LIKE ?) ORDER BY id DESC""",
        (jenis, jenis, f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return render_template("arsip.html", rows=rows, q=q, jenis=jenis, surat=SURAT)


init_db()  # pastikan tabel selalu ada, bagaimanapun aplikasi dijalankan

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")