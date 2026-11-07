"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud import ast_nodes as ast
from crud.analyzer import analyze_statement
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.pipeline import analyze_source
from crud.resolver import Resolver


def values(src):
    return [t.value for t in tokenize(src) if t.type != T.EOF]


def one(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    assert len(script.statements) == 1
    return script.statements[0]


def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script, Resolver().resolve_script(script)


def columns(node):
    return [n for n in ast.iter_nodes(node) if isinstance(n, ast.ColumnRef)]


def ops(sql):
    return analyze_statement(one(sql))


# ======================================================================
# A. Regresi bug / TODO
# ======================================================================

# ---- Lexer (SPESIFIKASI bagian 2) ----------------------------------------
def test_bug_keyword_case_insensitive_dan_dinormalisasi():
    toks = tokenize("Select x FrOm t")
    assert [(t.type, t.value) for t in toks[:4]] == [
        (T.KEYWORD, "SELECT"), (T.IDENT, "x"), (T.KEYWORD, "FROM"), (T.IDENT, "t")]


def test_bug_string_dua_kutip_berturut_turut_satu_token():
    toks = tokenize("'O''Brien'")
    assert [(t.type, t.value) for t in toks[:-1]] == [(T.STRING, "O'Brien")]


def test_bug_operator_tidak_sama_adalah_satu_token_maximal_munch():
    assert values("a <> b") == ["a", "<>", "b"]


def test_todo_komentar_blok_dilewati_dan_baris_tetap_terhitung():
    toks = tokenize("/* a\n b */ SELECT")
    assert toks[0].value == "SELECT" and (toks[0].line, toks[0].col) == (2, 7)


def test_komentar_blok_tidak_ditutup_adalah_lex_error():
    with pytest.raises(LexError):
        tokenize("SELECT /* tidak ditutup")


# ---- Parser (bagian 3 dan 6) ----------------------------------------------
def test_bug_presedensi_and_lebih_kuat_dari_or():
    # a = 1 OR b = 2 AND c = 3  ==>  a = 1 OR (b = 2 AND c = 3)
    where = one("SELECT x FROM t WHERE a = 1 OR b = 2 AND c = 3").where
    assert where.op == "OR"
    assert where.left.op == "="
    assert where.right.op == "AND"


def test_bug_and_di_kiri_or_tetap_dikelompokkan_benar():
    # a AND b OR c  ==>  (a AND b) OR c
    where = one("SELECT x FROM t WHERE a = 1 AND b = 2 OR c = 3").where
    assert where.op == "OR" and where.left.op == "AND"


def test_bug_left_outer_join_diterima():
    s = one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id")
    assert s.joins[0].kind == "LEFT" and s.joins[0].source.name == "b"


def test_bug_error_recovery_berhenti_di_titik_koma_dan_lanjut():
    script = parse_sql("SELECT id nama, FROM x; DELETE FROM y WHERE a = 1; UPDATE z SET a = 1")
    assert len(script.errors) == 1
    assert [type(s).__name__ for s in script.statements] == ["Delete", "Update"]


def test_todo_insert_select():
    s = one("INSERT INTO arsip (id) SELECT id FROM pesanan")
    assert s.values == [] and isinstance(s.query, ast.Select)


# ---- Resolver (bagian 4) ---------------------------------------------------
def test_bug_shadowing_alias_dalam_menutupi_alias_luar():
    # x di subquery harus menunjuk ke pesanan (scope terdalam), bukan pelanggan.
    script, diags = resolve(
        "SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x)")
    by_name = {c.name: c.resolved for c in columns(script)}
    assert by_name["pelanggan_id"] == "pesanan"
    assert by_name["id"] == "pelanggan"
    assert diags == []


def test_bug_delete_tidak_meninggalkan_scope_untuk_statement_berikutnya():
    # Bagian 4.5: alias 's' milik DELETE tidak boleh terlihat oleh SELECT berikutnya.
    _, diags = resolve("DELETE FROM sesi s WHERE s.id = 1; SELECT s.id FROM pengguna u")
    assert [d.level for d in diags] == ["error"]
    assert "'s'" in diags[0].message


def test_todo_kolom_tanpa_qualifier_tiga_kasus():
    script, diags = resolve("SELECT nama FROM pelanggan")
    assert columns(script)[0].resolved == "pelanggan" and diags == []

    script, diags = resolve("SELECT nama FROM pelanggan, pesanan")
    assert columns(script)[0].resolved is None
    assert [d.level for d in diags] == ["warning"]
    assert "kolom 'nama' ambigu tanpa skema" in diags[0].message

    script, diags = resolve("SELECT nama FROM (SELECT 1 FROM t)")
    assert columns(script)[0].resolved is None
    assert any(d.level == "warning" for d in diags)


# ---- Analyzer (bagian 5) ---------------------------------------------------
def test_bug_tabel_di_subquery_update_adalah_read_bukan_update():
    assert ops(
        "UPDATE a SET x = (SELECT MAX(y) FROM b) WHERE id IN (SELECT id FROM c)"
    ) == {"a": {"U"}, "b": {"R"}, "c": {"R"}}


# ======================================================================
# B. Lima kasus tepi
# ======================================================================

def test_tepi_error_terdeteksi_tepat_di_titik_koma():
    # Berisiko: kalau _synchronize memulai pengecekan ';' dari token SESUDAH error,
    # titik koma yang menjadi lokasi error terlewat dan statement valid berikutnya ikut terbuang.
    script = parse_sql("SELECT id FROM ;\nSELECT 1 FROM t;")
    assert len(script.errors) == 1 and script.errors[0].line == 1
    assert len(script.statements) == 1 and script.statements[0].line == 2


def test_tepi_komentar_blok_berisi_bintang_dan_kosong():
    # Berisiko: penutup dicari dengan "*/" saja; '*' di dalam komentar atau "/**/"
    # (penutup langsung menempel pada pembuka) bisa salah diproses.
    assert values("a /* x * y */ b /**/ c") == ["a", "b", "c"]


def test_tepi_correlated_subquery_tiga_tingkat():
    # Berisiko: lookup qualifier harus menelusuri seluruh rantai scope sampai terluar,
    # bukan hanya induk langsung.
    script, diags = resolve(
        "SELECT a FROM t1 WHERE a IN (SELECT b FROM t2 WHERE b IN "
        "(SELECT c FROM t3 WHERE c = t1.a))")
    outer_ref = [c for c in columns(script) if c.qualifier == "t1"][0]
    assert outer_ref.resolved == "t1" and diags == []


def test_tepi_nama_tabel_berbeda_skema_bentrok_di_scope_sama():
    # Berisiko: nama scope adalah bagian terakhir nama tabel, jadi crm.p dan hr.p
    # sama-sama bernama 'p' dan harus dilaporkan sebagai deklarasi ganda.
    _, diags = resolve("SELECT 1 FROM crm.p, hr.p")
    assert [d.level for d in diags] == ["error"]


def test_tepi_tabel_yang_sama_dibaca_dan_ditulis_urutan_crud():
    # Berisiko: operasi gabungan harus berurutan C, R, U, D ('CR', 'RD'), bukan urutan penemuan.
    res = analyze_source(
        "INSERT INTO a SELECT * FROM a;\nDELETE FROM a WHERE id IN (SELECT id FROM a);")
    assert [s.tables for s in res.statements] == [{"a": "CR"}, {"a": "RD"}]
    assert res.matrix() == {"a": "CRD"}