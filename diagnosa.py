"""Jalankan: python diagnosa.py  -> menampilkan penyebab Internal Server Error."""
import os
import sys
import traceback

base = os.path.dirname(os.path.abspath(__file__))
print("Python :", sys.version.split()[0])
print("Folder :", base)

wajib = ["base.html", "_kertas.html", "index.html", "form.html", "view.html", "arsip.html"]
ada = os.listdir(os.path.join(base, "templates")) if os.path.isdir(os.path.join(base, "templates")) else None
print("\n[1] Folder templates:", "TIDAK DITEMUKAN" if ada is None else "ada")
for f in wajib:
    print("   ", "OK     " if ada and f in ada else "HILANG ", f)
if ada:
    lain = [f for f in ada if f not in wajib]
    if lain:
        print("    File lain di templates (cek nama salah):", lain)

print("\n[2] Menguji halaman...")
try:
    import app as A
    A.app.testing = True
    c = A.app.test_client()
    form = {k: "x" for k, _, _ in A.COMMON + A.SURAT["undangan"]["fields"]}
    form.update(tanggal="2026-10-18", tgl_rapat="2026-10-20")
    for m, url, kw in [("get", "/", {}), ("get", "/buat/izin", {}), ("get", "/buat/undangan", {}),
                       ("get", "/buat/keterangan", {}), ("get", "/buat/permohonan", {}),
                       ("get", "/arsip", {}), ("post", "/simpan/undangan", {"data": form}),
                       ("get", "/surat/1", {})]:
        try:
            r = getattr(c, m)(url, **kw)
            print("    OK  ", m.upper(), url, r.status_code)
        except Exception:
            print("    ERROR", m.upper(), url)
            traceback.print_exc()
            print("-" * 60)
except Exception:
    print("    Gagal memuat app.py:")
    traceback.print_exc()
