# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

# Log Penggunaan AI

| No | Siapa | Prompt / tugas (ringkas) | Hasil | Alasan | Cara verifikasi |
| 1 | Irham | Analisis penyebab `ParseError` pada ekspresi perbandingan `<>` di `test_matrix_laporan_penjualan` saat parsing file SQL. | Diterima | AI mengidentifikasi bahwa Lexer memecah operator `<>` menjadi dua token terpisah (`<` dan `>`) sehingga Parser gagal mengenali ekspresi. | Menjalankan `pytest tests/test_analyzer.py` hingga `ParseError` teratasi. |
| 2 | Irham | Analisis ketidaksesuaian hasil matriks CRUD pada klausa `UPDATE` di mana tabel referensi pada `WHERE` teridentifikasi sebagai `U` (Update) bukannya `R` (Read). | Diterima | Membantu memvalidasi logika penelusuran AST agar subquery dan kondisi `WHERE` pada perintah `UPDATE` dikategorikan sebagai pembacaan (Read). | Menjalankan `pytest tests/test_analyzer.py` hingga seluruh 5 test unit lulus (*passed*). |
| 3 | Irham | Identifikasi penyebab kegagalan `test_kolom_tanpa_qualifier_satu_tabel` pada komponen Resolver ketika merujuk kolom tanpa alias/tabel. | Diubah | Penjelasan AI memberikan gambaran mekanisme penanganan *scope* pada Resolver, namun perbaikan kode disesuaikan dengan alokasi tugas tim. | Menjalankan `pytest tests/test_resolver.py` untuk mengisolasi kasus pengujian yang gagal. |
| 4 | Irham | Evaluasi hasil eksekusi `evaluate.py` untuk mengukur presisi ekstraksi dan mendeteksi penyebab *False Negative* pada file `campuran_error.sql`. | Diterima | AI membantu mengonfirmasi perolehan presisi 1.00 serta menjelaskan keterbatasan *panic mode recovery* pada Parser terhadap statement rusak. | Membandingkan nilai presisi/F1-score parser terhadap baseline regex dan memeriksa log *error*. |
| 5 | Irham | Troubleshooting error `OSError: [Errno 22] Invalid argument` saat menjalankan perintah CLI dengan argumen `*.sql` di PowerShell Windows. | Diterima | AI menjelaskan batasan ekspansi *wildcard* pada terminal Windows/PowerShell dan memberikan alternatif perintah eksekusi CLI yang valid. | Eksekusi CLI berhasil dan menghasilkan file keluaran `crud_matrix.csv`, `detail.csv`, dan `kolom.csv`. |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
