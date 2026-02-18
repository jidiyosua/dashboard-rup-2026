"""
═══════════════════════════════════════════════════════════════════════════════
  DASHBOARD RENCANA UMUM PENGADAAN (RUP) 2026
  Telkomsel Enterprise | Bid Management - Data Science
  
  Dashboard untuk C-Level Executives
  Analisis SI Channel — Peluang Pengadaan Pemerintah 2026
  ICT & Non-ICT Classification
═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import textwrap
import re
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# KONFIGURASI HALAMAN
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Dashboard RUP 2026 - Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# CSS — BACKGROUND PUTIH, TEKS HITAM TEBAL KONTRAS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* === GLOBAL — TEKS HITAM JELAS DI BACKGROUND PUTIH === */
    .stApp { background-color: #FFFFFF; }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        color: #111111 !important;
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background-color: #F5F5F5;
        border-right: 3px solid #DDD;
    }
    section[data-testid="stSidebar"] * { color: #111 !important; }

    /* === HEADER MERAH TELKOMSEL === */
    .main-header {
        background: linear-gradient(135deg, #ED1C24 0%, #9B1B1F 100%);
        padding: 30px 40px; border-radius: 16px; margin-bottom: 30px;
        box-shadow: 0 6px 24px rgba(237,28,36,0.2);
    }
    .main-header h1 { color:#FFF!important;font-size:34px!important;font-weight:800!important;margin:0!important; }
    .main-header p { color:#FFCCCC!important;font-size:16px!important;margin:6px 0 0!important; }

    /* === METRIC CARDS === */
    .mc {
        background:#FFF; border:2px solid #DDD; border-radius:14px;
        padding:20px 16px; text-align:center; box-shadow:0 3px 12px rgba(0,0,0,0.05);
    }
    .mc .lb { color:#444!important;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px; }
    .mc .vl { color:#111!important;font-size:26px;font-weight:800;line-height:1.1; }
    .mc .sb { color:#666!important;font-size:11px;margin-top:6px; }

    /* === SECTION HEADERS === */
    .sh {
        background:#F5F5F5; border-left:6px solid #ED1C24;
        padding:16px 24px; margin:32px 0 20px; border-radius:0 10px 10px 0;
    }
    .sh h2 { color:#111!important;font-size:24px!important;font-weight:800!important;margin:0!important; }
    .sh p { color:#555!important;font-size:14px!important;margin:6px 0 0!important; }

    /* === INFO BOX === */
    .ib {
        background:#E8F0FE; border:2px solid #4285F4; border-radius:10px;
        padding:16px 20px; margin:14px 0; font-size:15px; color:#1A3A5C!important; font-weight:500;
    }

    /* === EXPANDER === */
    .streamlit-expanderHeader { font-size:16px!important;font-weight:700!important;color:#111!important; }

    /* === TABS === */
    .stTabs [data-baseweb="tab"] { font-weight:700;font-size:15px;padding:12px 24px;color:#111!important; }

    /* === LABELS === */
    .stSelectbox label, .stMultiSelect label, .stRadio label,
    .stTextInput label, .stFileUploader label {
        color:#111!important; font-weight:700!important; font-size:14px!important;
    }

    /* === DOWNLOAD === */
    .stDownloadButton>button {
        background:#1A1A2E!important;color:#FFF!important;font-weight:700!important;
        border-radius:10px!important;border:none!important;
    }
    .stDownloadButton>button:hover { background:#ED1C24!important; }

    /* === HIDE BRANDING === */
    #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ICT CLASSIFICATION — WHITELIST + BLACKLIST
# ═══════════════════════════════════════════════════════════════════════════

ICT_WHITELIST = {
    'Connectivity': [
        r'\bINTERNET\b', r'\bBANDWIDTH\b', r'\bBROADBAND\b',
        r'\bFIBER\s*OPTI[CK]\b', r'\bFIBER\b(?!\s*GLASS)',
        r'\bMPLS\b', r'\bVPN\b', r'\bVSAT\b',
        r'\bWI[\s\-]?FI\b', r'\bWIFI\b', r'\bWIRELESS\b', r'\bHOTSPOT\b',
    ],
    'Cloud & Data Center': [
        r'\bCLOUD\b(?!\s*NINE)', r'\bDATA\s*CENTER\b',
        r'\bCOLOCATION\b', r'\bHOSTING\b',
        r'\bVIRTUAL\s+SERVER\b', r'\bVPS\b',
    ],
    'Telekomunikasi': [
        r'\bPULSA\b', r'\bPAKET\s+DATA\b', r'\bSIM\s*CARD\b',
        r'\bTELEKOMUNIKASI\b', r'\bPABX\b', r'\bVOIP\b',
        r'\bIP\s+PHONE\b', r'\bCALL\s+CENTER\b',
    ],
    'Kolaborasi': [
        r'\bVIDEO\s*CONFERENCE\b', r'\bZOOM\b(?!\s*IN|\s*OUT)',
        r'\bWEBINAR\b', r'\bMICROSOFT\s+TEAMS\b',
    ],
    'IoT & Smart City': [
        r'\bIOT\b', r'\bGPS\s+TRACK(ER|ING)\b',
        r'\bTELEMATIC[S]?\b', r'\bSMART\s+CITY\b',
    ],
    'Surveillance & Security': [
        r'\bCCTV\b', r'\bSURVEILLANCE\b', r'\bIP\s+CAMERA\b',
        r'\bNVR\b', r'\bDVR\b(?!\s+PLAYER)',
        r'\bACCESS\s+CONTROL\b', r'\bBIOMETRIC\b',
        r'\bCYBER\s*SECURITY\b', r'\bNETWORK\s+SECURITY\b',
    ],
    'Hardware Komputer': [
        r'\bKOMPUTER\b', r'\bCOMPUTER\b', r'\bLAPTOP\b',
        r'\bNOTEBOOK\b', r'\bDESKTOP\b', r'\bWORKSTATION\b',
    ],
    'Hardware Server': [
        r'\bSERVER\b(?!\s+MAKANAN|\s+MINUMAN)',
        r'\bSTORAGE\b(?!\s+BOX|\s+RACK\s+BESI)',
        r'\bRACK\s+SERVER\b', r'\bUPS\b(?!\s+DELIVERY)',
    ],
    'Hardware Jaringan': [
        r'\bROUTER\b', r'\bSWITCH\b(?!\s+ON|\s+OFF)',
        r'\bFIREWALL\b', r'\bMODEM\b',
    ],
    'Software': [
        r'\bSOFTWARE\b', r'\bAPLIKASI\b(?!\s+LAMARAN)',
        r'\bSISTEM\s+INFORMASI\b', r'\bWEBSITE\b',
        r'\bDATABASE\b', r'\bERP\b', r'\bANTIVIRUS\b',
        r'\bLISENSI\b', r'\bLICENSE\b',
    ],
    'IT Services': [
        r'\bMAINTENANCE\s+(JARINGAN|SERVER|IT|NETWORK)\b',
        r'\bSYSTEM\s+INTEGRAT(OR|ION)\b',
        r'\bMANAGED\s+SERVICE\b',
    ],
}

BLACKLIST_PATTERNS = [
    r'\bBUKU\b', r'\bPRINTER\b', r'\bTONER\b', r'\bBANGUNAN\b',
    r'\bKONSTRUKSI\b', r'\bTINTA\b', r'\bOBAT\b', r'\bVAKSIN\b',
    r'\bALAT\s+KESEHATAN\b', r'\bMEDIS\b', r'\bELEKTROMEDI[CKS]?\b',
    r'\bPATIENT\s+MONITOR\b', r'\bVENTILATOR\b', r'\bINCUBATOR\b',
    r'\bENDOSCOP[EY]\b', r'\bCT\s+SCAN\b', r'\bMRI\b', r'\bUSG\b',
    r'\bMAKANAN\b', r'\bMINUMAN\b', r'\bKATERING\b', r'\bATK\b',
    r'\bSERAGAM\b', r'\bMOBIL\b(?!\s+APP)', r'\bKENDARAAN\b',
]

# Compile regex sekali (performa)
_all_ict = []
for pats in ICT_WHITELIST.values():
    _all_ict.extend(pats)
_ict_re = re.compile("|".join(_all_ict), re.IGNORECASE)
_bl_re = re.compile("|".join(BLACKLIST_PATTERNS), re.IGNORECASE)

# Per-category compiled regex
_cat_re = {cat: re.compile("|".join(pats), re.IGNORECASE) for cat, pats in ICT_WHITELIST.items()}


def classify_ict(nama_paket):
    """True = ICT, False = Non-ICT."""
    if pd.isna(nama_paket):
        return False
    text = str(nama_paket)
    return bool(_ict_re.search(text) and not _bl_re.search(text))


def get_ict_category(nama_paket):
    """Return ICT category name or None."""
    if pd.isna(nama_paket):
        return None
    text = str(nama_paket)
    if _bl_re.search(text):
        return None
    for cat, regex in _cat_re.items():
        if regex.search(text):
            return cat
    return None


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def fmt_rp(v):
    """Format Rupiah."""
    if pd.isna(v) or v == 0:
        return "Rp 0"
    a = abs(v)
    if a >= 1e12: return f"Rp {v/1e12:,.2f} T"
    if a >= 1e9:  return f"Rp {v/1e9:,.2f} M"
    if a >= 1e6:  return f"Rp {v/1e6:,.1f} Jt"
    return f"Rp {v:,.0f}"


def fmt_s(v):
    """Format singkat chart."""
    if pd.isna(v) or v == 0:
        return "0"
    a = abs(v)
    if a >= 1e12: return f"{v/1e12:.2f} T"
    if a >= 1e9:  return f"{v/1e9:.1f} M"
    if a >= 1e6:  return f"{v/1e6:.0f} Jt"
    return f"{v:,.0f}"


def fmt_n(v):
    """Format angka ribuan."""
    if pd.isna(v):
        return "0"
    return f"{int(v):,}".replace(",", ".")


def mc_html(lb, vl, sb=""):
    """Render metric card HTML."""
    s = f'<div class="sb">{sb}</div>' if sb else ""
    return f'<div class="mc"><div class="lb">{lb}</div><div class="vl">{vl}</div>{s}</div>'


def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def parse_lokasi(lokasi_str):
    """
    Parse 'Lampung, Way Kanan (Kab.)' → (Provinsi, Daerah, Tipe)
    Parse 'DKI Jakarta, Jakarta Pusat (Kota)' → (DKI Jakarta, Jakarta Pusat, Kota)
    Handle multi-lokasi: 'A | B' → take first
    """
    if pd.isna(lokasi_str):
        return "Lainnya", "Lainnya", "Lainnya"
    # Ambil lokasi pertama jika ada multi
    text = str(lokasi_str).split("|")[0].strip()
    # Parse: "Provinsi, Daerah (Tipe)"
    m = re.match(r'^(.+?),\s*(.+?)\s*\((Kab\.|Kota)\)\s*$', text)
    if m:
        prov = m.group(1).strip()
        daerah = m.group(2).strip()
        tipe_raw = m.group(3).strip()
        tipe = "Kabupaten" if tipe_raw == "Kab." else "Kota"
        return prov, daerah, tipe
    # Fallback: coba parse tanpa tipe
    m2 = re.match(r'^(.+?),\s*(.+)$', text)
    if m2:
        return m2.group(1).strip(), m2.group(2).strip(), "Lainnya"
    return text, text, "Lainnya"


# ═══════════════════════════════════════════════════════════════════════════
# CHART FUNCTION — COMPATIBLE SEABORN 0.12.x
# ═══════════════════════════════════════════════════════════════════════════

def hbar(data, x_col, y_col, title, subtitle, colors, total_universe=None,
         figsize=(14, 7.5)):
    """
    Horizontal bar chart — C-Level standard.
    TANPA hue dan legend (kompatibel seaborn lama).
    Teks hitam tebal, angka exact, total semesta.
    """
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    d = data.copy()
    n = len(d)
    if n == 0:
        ax.text(0.5, 0.5, "Tidak ada data", ha="center", va="center",
                fontsize=18, color="#999")
        return fig

    # Wrap label panjang supaya tidak overlap
    d[y_col] = d[y_col].apply(lambda t: "\n".join(textwrap.wrap(str(t), 40)))

    # Barplot TANPA hue (kompatibel seaborn 0.12.x)
    sns.barplot(
        data=d, x=x_col, y=y_col,
        palette=colors[:n], ax=ax, edgecolor="none",
    )

    # Title
    ax.set_title(title, fontsize=22, fontweight="bold", color="#111111",
                 loc="left", pad=24)
    if subtitle:
        ax.text(0, 1.03, subtitle, transform=ax.transAxes,
                fontsize=13, color="#555555", ha="left", va="bottom")

    # Exact values pada setiap bar
    mx = d[x_col].max() if n > 0 else 1
    for i, val in enumerate(d[x_col]):
        lb = fmt_s(val)
        if total_universe and total_universe > 0:
            lb += f"  ({val/total_universe*100:.1f}%)"
        ax.text(val + mx * 0.012, i, lb,
                va="center", ha="left",
                fontsize=13, fontweight="bold", color="#111111")

    # Total semesta annotation
    if total_universe:
        ax.text(1.0, -0.07,
                f"TOTAL SEMESTA: {fmt_rp(total_universe)}",
                transform=ax.transAxes, fontsize=13, fontweight="bold",
                color="#ED1C24", ha="right", va="top")

    # Styling
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=13, labelcolor="#111111", width=0)
    ax.tick_params(axis="x", labelsize=11, labelcolor="#777777")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_s(x)))
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#DDD")
    ax.spines["left"].set_color("#DDD")

    # Extend x-axis supaya label tidak terpotong
    if mx > 0:
        ax.set_xlim(0, mx * 1.45)

    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_rup_data(db_path):
    """Load RUP data dari SQLite. Auto-detect tabel dan kolom."""
    conn = sqlite3.connect(db_path)

    # Auto-detect nama tabel
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    if len(tables) == 0:
        conn.close()
        return pd.DataFrame()

    # Cari tabel yang mengandung 'rup' atau pakai yang pertama
    tbl = tables.iloc[0]["name"]
    for t in tables["name"]:
        if "rup" in t.lower():
            tbl = t
            break

    df = pd.read_sql(f'SELECT * FROM [{tbl}]', conn)
    conn.close()

    # ── Auto-detect kolom ──
    cols = df.columns.tolist()
    col_lower = {c.lower().replace(" ", "_").replace("(", "").replace(")", ""): c for c in cols}

    # Mapping kolom — flexible
    def find_col(*candidates):
        for c in candidates:
            cl = c.lower().replace(" ", "_")
            if cl in col_lower:
                return col_lower[cl]
            for k, v in col_lower.items():
                if cl in k or k in cl:
                    return v
        return None

    # Identifikasi kolom-kolom penting
    col_paket = find_col("Paket", "Nama_Paket", "nama_paket", "paket")
    col_pagu = find_col("Pagu_Rp", "Pagu", "pagu_rp", "pagu")
    col_jenis = find_col("Jenis_Pengadaan", "Jenis Pengadaan", "jenis_pengadaan")
    col_metode = find_col("Metode", "Metode_Pemilihan", "metode")
    col_klpd = find_col("K/L/PD", "KLPD", "klpd", "Instansi", "K_L_PD")
    col_satker = find_col("Satuan_Kerja", "Satuan Kerja", "satuan_kerja")
    col_lokasi = find_col("Lokasi", "lokasi")
    col_pemilihan = find_col("Pemilihan", "pemilihan", "Waktu_Pemilihan")
    col_id = find_col("ID", "id", "ID_RUP", "No")
    col_uk = find_col("Usaha_Kecil", "Usaha Kecil/Koperasi", "usaha_kecil")
    col_pdn = find_col("Produk_Dalam_Negeri", "Produk Dalam Negeri", "produk_dalam_negeri")

    # Standardize column names
    rename_map = {}
    if col_paket: rename_map[col_paket] = "Nama_Paket"
    if col_pagu: rename_map[col_pagu] = "Pagu_Rp"
    if col_jenis: rename_map[col_jenis] = "Jenis_Pengadaan"
    if col_metode: rename_map[col_metode] = "Metode"
    if col_klpd: rename_map[col_klpd] = "KLPD"
    if col_satker: rename_map[col_satker] = "Satuan_Kerja"
    if col_lokasi: rename_map[col_lokasi] = "Lokasi"
    if col_pemilihan: rename_map[col_pemilihan] = "Pemilihan"
    if col_id: rename_map[col_id] = "ID_RUP"
    if col_uk: rename_map[col_uk] = "Usaha_Kecil"
    if col_pdn: rename_map[col_pdn] = "Produk_DN"

    df = df.rename(columns=rename_map)

    # Parse Pagu
    if "Pagu_Rp" in df.columns:
        df["Pagu_Rp"] = (df["Pagu_Rp"].astype(str)
                         .str.replace(r'[^\d.]', '', regex=True))
        df["Pagu_Rp"] = pd.to_numeric(df["Pagu_Rp"], errors="coerce").fillna(0)

    # Parse Lokasi → Provinsi, Daerah, Tipe_Daerah
    if "Lokasi" in df.columns:
        parsed = df["Lokasi"].apply(lambda x: pd.Series(parse_lokasi(x)))
        df["Provinsi"] = parsed[0]
        df["Daerah"] = parsed[1]
        df["Tipe_Daerah"] = parsed[2]
    else:
        df["Provinsi"] = "Tidak Diketahui"
        df["Daerah"] = "Tidak Diketahui"
        df["Tipe_Daerah"] = "Lainnya"

    # ICT classification
    if "Nama_Paket" in df.columns:
        df["Is_ICT"] = df["Nama_Paket"].apply(classify_ict)
        df["Kategori_ICT"] = df["Nama_Paket"].apply(get_ict_category)
    else:
        df["Is_ICT"] = False
        df["Kategori_ICT"] = None

    # Sektor label
    df["Sektor"] = df["Is_ICT"].map({True: "ICT", False: "Non-ICT"})

    return df


# ═══════════════════════════════════════════════════════════════════════════
# REUSABLE RENDER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def render_ringkasan(df_sect, total_pagu_sect, label, key_prefix):
    """Render Ringkasan Nasional: Top Provinsi, Top KLPD, Top Satker, Distribusi."""

    # ── A. TOP 10 PROVINSI ──
    st.markdown(f"""
    <div class="sh">
        <h2>🗺️ Top 10 Provinsi — Nilai Pagu Terbesar ({label})</h2>
        <p>Total Pagu per Provinsi — peluang pengadaan terbesar</p>
    </div>""", unsafe_allow_html=True)

    df_prov = (df_sect.groupby("Provinsi")
               .agg(Total_Pagu=("Pagu_Rp", "sum"),
                    Jumlah_Paket=("Pagu_Rp", "count"),
                    Jumlah_Satker=("Satuan_Kerja", "nunique"))
               .sort_values("Total_Pagu", ascending=False)
               .head(10).reset_index())

    if len(df_prov) > 0:
        cp = df_prov.copy()
        cp["Label"] = cp["Provinsi"].apply(lambda x: str(x)[:42])
        fig = hbar(cp, "Total_Pagu", "Label",
                   f"Top 10 Provinsi — {label}",
                   f"Dari {fmt_n(df_sect['Provinsi'].nunique())} provinsi",
                   sns.color_palette("Reds_r", 10), total_pagu_sect)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # Expander detail
        st.markdown("#### 📋 Detail: Top 5 K/L/PD per Provinsi")
        for _, row in df_prov.iterrows():
            prov = row["Provinsi"]
            with st.expander(f"🗺️ **{prov}** — {fmt_rp(row['Total_Pagu'])} ({fmt_n(row['Jumlah_Paket'])} paket)"):
                detail = (df_sect[df_sect["Provinsi"] == prov]
                          .groupby("KLPD")
                          .agg(Pagu=("Pagu_Rp", "sum"), Paket=("Pagu_Rp", "count"))
                          .sort_values("Pagu", ascending=False).head(5).reset_index())
                if len(detail) > 0:
                    detail["Pagu"] = detail["Pagu"].apply(fmt_rp)
                    detail.columns = ["K/L/PD", "Total Pagu (Rp)", "Jumlah Paket"]
                    st.dataframe(detail, use_container_width=True, hide_index=True)

        raw = df_sect[df_sect["Provinsi"].isin(df_prov["Provinsi"].tolist())]
        st.download_button(f"📥 CSV Top 10 Provinsi ({label})", to_csv(raw),
                           f"Top10_Provinsi_{label}_{datetime.now():%Y%m%d}.csv",
                           "text/csv", key=f"dl_prov_{key_prefix}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── B. TOP 10 K/L/PD ──
    st.markdown(f"""
    <div class="sh">
        <h2>🏛️ Top 10 K/L/PD — Nilai Pagu Terbesar ({label})</h2>
        <p>Kementerian / Lembaga / Pemerintah Daerah dengan rencana pengadaan terbesar</p>
    </div>""", unsafe_allow_html=True)

    if "KLPD" in df_sect.columns:
        df_klpd = (df_sect.groupby("KLPD")
                   .agg(Total_Pagu=("Pagu_Rp", "sum"),
                        Jumlah_Paket=("Pagu_Rp", "count"),
                        Jumlah_Satker=("Satuan_Kerja", "nunique"))
                   .sort_values("Total_Pagu", ascending=False)
                   .head(10).reset_index())

        if len(df_klpd) > 0:
            ck = df_klpd.copy()
            ck["Label"] = ck["KLPD"].apply(lambda x: str(x)[:38])
            fig = hbar(ck, "Total_Pagu", "Label",
                       f"Top 10 K/L/PD — {label}",
                       f"Dari {fmt_n(df_sect['KLPD'].nunique())} K/L/PD",
                       sns.color_palette("Blues_r", 10), total_pagu_sect)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.markdown("""
            <div class="ib">
                💡 <strong>Insight:</strong> K/L/PD dengan banyak satuan kerja (≥5 satker) 
                menunjukkan potensi engagement yang luas untuk penawaran solusi Telkomsel.
            </div>""", unsafe_allow_html=True)

            st.markdown("#### 📋 Detail: Top 5 Satuan Kerja per K/L/PD")
            for _, row in df_klpd.iterrows():
                klpd = row["KLPD"]
                badge = "🌟" if row["Jumlah_Satker"] >= 5 else "🔹"
                with st.expander(f"{badge} **{klpd}** — {fmt_rp(row['Total_Pagu'])} ({fmt_n(row['Jumlah_Satker'])} satker)"):
                    detail = (df_sect[df_sect["KLPD"] == klpd]
                              .groupby("Satuan_Kerja")
                              .agg(Pagu=("Pagu_Rp", "sum"), Paket=("Pagu_Rp", "count"))
                              .sort_values("Pagu", ascending=False).head(5).reset_index())
                    if len(detail) > 0:
                        detail["Pagu"] = detail["Pagu"].apply(fmt_rp)
                        detail.columns = ["Satuan Kerja", "Total Pagu (Rp)", "Jumlah Paket"]
                        st.dataframe(detail, use_container_width=True, hide_index=True)

            raw = df_sect[df_sect["KLPD"].isin(df_klpd["KLPD"].tolist())]
            st.download_button(f"📥 CSV Top 10 K/L/PD ({label})", to_csv(raw),
                               f"Top10_KLPD_{label}_{datetime.now():%Y%m%d}.csv",
                               "text/csv", key=f"dl_klpd_{key_prefix}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── C. TOP 10 SATUAN KERJA ──
    st.markdown(f"""
    <div class="sh">
        <h2>🏢 Top 10 Satuan Kerja — Nilai Pagu Terbesar ({label})</h2>
        <p>Satker dengan rencana anggaran pengadaan terbesar</p>
    </div>""", unsafe_allow_html=True)

    if "Satuan_Kerja" in df_sect.columns:
        df_sk = (df_sect.groupby("Satuan_Kerja")
                 .agg(Total_Pagu=("Pagu_Rp", "sum"),
                      Jumlah_Paket=("Pagu_Rp", "count"),
                      KLPD_Induk=("KLPD", "first"))
                 .sort_values("Total_Pagu", ascending=False)
                 .head(10).reset_index())

        if len(df_sk) > 0:
            cs = df_sk.copy()
            cs["Label"] = cs["Satuan_Kerja"].apply(lambda x: str(x)[:42])
            fig = hbar(cs, "Total_Pagu", "Label",
                       f"Top 10 Satuan Kerja — {label}",
                       f"Dari {fmt_n(df_sect['Satuan_Kerja'].nunique())} satker",
                       sns.color_palette("Oranges_r", 10), total_pagu_sect)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.markdown("#### 📋 Detail Paket per Satker")
            for _, row in df_sk.iterrows():
                sk = row["Satuan_Kerja"]
                with st.expander(f"🏢 **{sk}** — {fmt_rp(row['Total_Pagu'])} ({fmt_n(row['Jumlah_Paket'])} paket)"):
                    detail = (df_sect[df_sect["Satuan_Kerja"] == sk]
                              [["Nama_Paket", "Pagu_Rp", "Jenis_Pengadaan", "Metode"]]
                              .sort_values("Pagu_Rp", ascending=False).head(10))
                    detail_show = detail.copy()
                    detail_show["Pagu_Rp"] = detail_show["Pagu_Rp"].apply(fmt_rp)
                    detail_show.columns = ["Nama Paket", "Pagu (Rp)", "Jenis", "Metode"]
                    st.dataframe(detail_show, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── D. DISTRIBUSI ──
    st.markdown(f"""
    <div class="sh">
        <h2>📊 Distribusi ({label})</h2>
        <p>Per jenis pengadaan, metode, dan timeline pemilihan</p>
    </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        if "Jenis_Pengadaan" in df_sect.columns:
            dj = (df_sect.groupby("Jenis_Pengadaan")
                  .agg(Total_Pagu=("Pagu_Rp", "sum"))
                  .sort_values("Total_Pagu", ascending=False).head(8).reset_index())
            if len(dj) > 0:
                fig = hbar(dj, "Total_Pagu", "Jenis_Pengadaan",
                           "Per Jenis Pengadaan", "",
                           sns.color_palette("Greens_r", len(dj)),
                           total_pagu_sect, figsize=(8, 4))
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

    with col_b:
        if "Metode" in df_sect.columns:
            dm = (df_sect.groupby("Metode")
                  .agg(Total_Pagu=("Pagu_Rp", "sum"))
                  .sort_values("Total_Pagu", ascending=False).head(8).reset_index())
            if len(dm) > 0:
                fig = hbar(dm, "Total_Pagu", "Metode",
                           "Per Metode Pemilihan", "",
                           sns.color_palette("Purples_r", len(dm)),
                           total_pagu_sect, figsize=(8, 4))
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

    # Timeline Pemilihan
    if "Pemilihan" in df_sect.columns:
        dt = (df_sect.groupby("Pemilihan")
              .agg(Total_Pagu=("Pagu_Rp", "sum"), Jumlah_Paket=("Pagu_Rp", "count"))
              .reset_index())

        # Sort by month order
        month_order = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        dt["sort_key"] = dt["Pemilihan"].apply(
            lambda x: next((v * 100 + (int(str(x).split()[-1]) if str(x).split()[-1].isdigit() else 0)
                           for k, v in month_order.items() if k in str(x)), 999))
        dt = dt.sort_values("sort_key").head(15)

        if len(dt) > 0:
            st.markdown(f'<div class="sh"><h2>📅 Timeline Pemilihan ({label})</h2><p>Rencana waktu pelaksanaan pengadaan</p></div>', unsafe_allow_html=True)
            fig = hbar(dt, "Total_Pagu", "Pemilihan",
                       f"Pagu per Waktu Pemilihan — {label}",
                       f"Total: {fmt_rp(total_pagu_sect)}",
                       sns.color_palette("YlOrRd_r", len(dt)),
                       total_pagu_sect, figsize=(14, 6))
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)


def render_deepdive(df_sect, total_pagu_sect, label, key_prefix):
    """Deep Dive: pilih Provinsi → lihat detail Kab/Kota, Satker, Paket."""

    st.markdown(f"""
    <div class="sh">
        <h2>🔎 Deep Dive per Wilayah — {label}</h2>
        <p>Pilih provinsi untuk melihat detail per kabupaten/kota dan satuan kerja</p>
    </div>""", unsafe_allow_html=True)

    # Selector
    col1, col2 = st.columns([1, 2])

    prov_ranked = (df_sect.groupby("Provinsi")["Pagu_Rp"].sum()
                   .sort_values(ascending=False).reset_index())
    prov_opts = prov_ranked["Provinsi"].tolist() if len(prov_ranked) > 0 else ["Tidak ada data"]

    with col1:
        tipe_f = st.selectbox("📍 Filter Tipe Daerah",
                              ["Semua", "Kabupaten", "Kota", "Lainnya"],
                              key=f"tf_{key_prefix}")
    with col2:
        sel_prov = st.selectbox("🗺️ Pilih Provinsi", prov_opts,
                                key=f"sp_{key_prefix}")

    if sel_prov and sel_prov != "Tidak ada data":
        df_wil = df_sect[df_sect["Provinsi"] == sel_prov].copy()
        if tipe_f != "Semua":
            df_wil = df_wil[df_wil["Tipe_Daerah"] == tipe_f]

        wp = df_wil["Pagu_Rp"].sum()
        wk = len(df_wil)
        ws = df_wil["Satuan_Kerja"].nunique() if "Satuan_Kerja" in df_wil.columns else 0
        wl = df_wil["KLPD"].nunique() if "KLPD" in df_wil.columns else 0

        st.markdown(f'<div style="background:#FFF3F3;border:3px solid #ED1C24;border-radius:14px;padding:20px 28px;margin:16px 0"><h3 style="color:#B71C1C!important;margin:0;font-size:24px;font-weight:800">📍 {sel_prov} — {label}</h3></div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        pct = f"{(wp/total_pagu_sect*100):.2f}% dari semesta" if total_pagu_sect > 0 else ""
        with c1: st.markdown(mc_html("Total Pagu", fmt_rp(wp), pct), unsafe_allow_html=True)
        with c2: st.markdown(mc_html("Jumlah Paket", fmt_n(wk)), unsafe_allow_html=True)
        with c3: st.markdown(mc_html("K/L/PD", fmt_n(wl)), unsafe_allow_html=True)
        with c4: st.markdown(mc_html("Satuan Kerja", fmt_n(ws)), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Top 10 Kab/Kota
        st.markdown(f'<div class="sh"><h2>🏘️ Top 10 Kab/Kota — {sel_prov}</h2><p>Berdasarkan total Pagu per daerah | {label}</p></div>', unsafe_allow_html=True)

        if "Daerah" in df_wil.columns:
            dd = (df_wil.groupby(["Daerah", "Tipe_Daerah"])
                  .agg(Total_Pagu=("Pagu_Rp", "sum"), Jumlah_Paket=("Pagu_Rp", "count"))
                  .sort_values("Total_Pagu", ascending=False).head(10).reset_index())
            dd["Label"] = dd.apply(lambda r: f"{r['Daerah']} ({r['Tipe_Daerah'][:3]}.)", axis=1)

            if len(dd) > 0:
                fig = hbar(dd, "Total_Pagu", "Label",
                           f"Top 10 Kab/Kota — {sel_prov}",
                           f"Total pagu provinsi: {fmt_rp(wp)}",
                           sns.color_palette("RdYlGn_r", 10), wp)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                st.markdown("#### 📋 Detail per Kab/Kota")
                for _, row in dd.iterrows():
                    dr = row["Daerah"]
                    with st.expander(f"🏘️ **{row['Label']}** — {fmt_rp(row['Total_Pagu'])} ({fmt_n(row['Jumlah_Paket'])} paket)"):
                        detail = (df_wil[df_wil["Daerah"] == dr]
                                  .groupby("Satuan_Kerja")
                                  .agg(Pagu=("Pagu_Rp", "sum"), Paket=("Pagu_Rp", "count"))
                                  .sort_values("Pagu", ascending=False).head(5).reset_index())
                        if len(detail) > 0:
                            detail["Pagu"] = detail["Pagu"].apply(fmt_rp)
                            detail.columns = ["Satuan Kerja", "Total Pagu (Rp)", "Jumlah Paket"]
                            st.dataframe(detail, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Top 10 Satker di Wilayah
        st.markdown(f'<div class="sh"><h2>🏢 Top 10 Satuan Kerja — {sel_prov}</h2><p>Satker dengan anggaran terbesar | {label}</p></div>', unsafe_allow_html=True)

        if "Satuan_Kerja" in df_wil.columns:
            dsk = (df_wil.groupby("Satuan_Kerja")
                   .agg(Total_Pagu=("Pagu_Rp", "sum"), Jumlah_Paket=("Pagu_Rp", "count"))
                   .sort_values("Total_Pagu", ascending=False).head(10).reset_index())

            if len(dsk) > 0:
                cs = dsk.copy()
                cs["Label"] = cs["Satuan_Kerja"].apply(lambda x: str(x)[:42])
                fig = hbar(cs, "Total_Pagu", "Label",
                           f"Top 10 Satker — {sel_prov}",
                           f"Dari {fmt_n(ws)} satker",
                           sns.color_palette("Oranges_r", 10), wp)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                st.markdown("#### 📋 Detail Paket per Satker")
                for _, row in dsk.iterrows():
                    sk = row["Satuan_Kerja"]
                    with st.expander(f"🏢 **{sk}** — {fmt_rp(row['Total_Pagu'])} ({fmt_n(row['Jumlah_Paket'])} paket)"):
                        pkts = (df_wil[df_wil["Satuan_Kerja"] == sk]
                                [["Nama_Paket", "Pagu_Rp", "Jenis_Pengadaan", "Metode"]]
                                .sort_values("Pagu_Rp", ascending=False).head(10))
                        ps = pkts.copy()
                        ps["Pagu_Rp"] = ps["Pagu_Rp"].apply(fmt_rp)
                        ps.columns = ["Nama Paket", "Pagu (Rp)", "Jenis", "Metode"]
                        st.dataframe(ps, use_container_width=True, hide_index=True)

                st.download_button(f"📥 CSV Data {sel_prov} ({label})", to_csv(df_wil),
                                   f"RUP_{sel_prov}_{label}_{datetime.now():%Y%m%d}.csv",
                                   "text/csv", key=f"dl_wil_{key_prefix}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Distribusi Wilayah
        st.markdown(f'<div class="sh"><h2>📊 Komposisi — {sel_prov}</h2><p>Distribusi pagu | {label}</p></div>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            if "Jenis_Pengadaan" in df_wil.columns:
                dj = (df_wil.groupby("Jenis_Pengadaan")
                      .agg(Total_Pagu=("Pagu_Rp", "sum"))
                      .sort_values("Total_Pagu", ascending=False).head(6).reset_index())
                if len(dj) > 0:
                    fig = hbar(dj, "Total_Pagu", "Jenis_Pengadaan", "Per Jenis Pengadaan",
                               "", sns.color_palette("Greens_r", len(dj)), wp, figsize=(8, 4))
                    st.pyplot(fig, use_container_width=True); plt.close(fig)
        with cb:
            if "Metode" in df_wil.columns:
                dm = (df_wil.groupby("Metode")
                      .agg(Total_Pagu=("Pagu_Rp", "sum"))
                      .sort_values("Total_Pagu", ascending=False).head(6).reset_index())
                if len(dm) > 0:
                    fig = hbar(dm, "Total_Pagu", "Metode", "Per Metode",
                               "", sns.color_palette("Purples_r", len(dm)), wp, figsize=(8, 4))
                    st.pyplot(fig, use_container_width=True); plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard Rencana Umum Pengadaan (RUP) 2026</h1>
    <p>Analisis SI Channel • ICT & Non-ICT • Peluang Pengadaan Pemerintah • Telkomsel Enterprise</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — KONFIGURASI & FILTERS
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚙️ Konfigurasi Database")
    st.markdown("---")

    DB_DEFAULT = "RUP.db"
    db_path = st.text_input("📁 Path Database SQLite", value=DB_DEFAULT,
                            help="Lokasi file RUP.db")

    if not os.path.exists(db_path):
        st.error(f"⚠️ File `{db_path}` tidak ditemukan.\n\n"
                 f"Letakkan file RUP.db di folder yang sama dengan script ini.")
        st.stop()

    with st.spinner("⏳ Memuat data RUP 2026..."):
        df = load_rup_data(db_path)

    if df.empty:
        st.error("❌ Database kosong atau tidak dapat dibaca.")
        st.stop()

    st.success(f"✅ **{fmt_n(len(df))}** record dimuat")
    st.markdown("---")

    # ── FILTER PROVINSI ──
    st.markdown("### 🗺️ Filter Provinsi")
    prov_all = sorted(df["Provinsi"].dropna().unique().tolist())
    sel_prov_filter = st.multiselect("Provinsi", prov_all, prov_all, key="f_prov")

    # ── FILTER TIPE DAERAH ──
    st.markdown("### 🏘️ Filter Tipe Daerah")
    tipe_all = sorted(df["Tipe_Daerah"].dropna().unique().tolist())
    sel_tipe = st.multiselect("Tipe", tipe_all, tipe_all, key="f_tipe")

    # ── FILTER JENIS PENGADAAN ──
    st.markdown("### 📋 Filter Jenis Pengadaan")
    jenis_all = sorted(df["Jenis_Pengadaan"].dropna().unique().tolist()) if "Jenis_Pengadaan" in df.columns else []
    sel_jenis = st.multiselect("Jenis Pengadaan", jenis_all, jenis_all, key="f_jenis")

    # ── FILTER METODE ──
    st.markdown("### 🔍 Filter Metode")
    metode_all = sorted(df["Metode"].dropna().unique().tolist()) if "Metode" in df.columns else []
    sel_metode = st.multiselect("Metode", metode_all, metode_all, key="f_metode")

    # ── FILTER SATUAN KERJA ──
    st.markdown("### 🏢 Filter Satuan Kerja")
    if "Satuan_Kerja" in df.columns:
        satker_all = sorted(df["Satuan_Kerja"].dropna().unique().tolist())
        # Searchable selectbox karena bisa ribuan
        st.caption(f"Total: {fmt_n(len(satker_all))} satker")
        sel_satker = st.multiselect(
            "Satuan Kerja",
            satker_all,
            default=[],  # Default kosong = semua
            key="f_satker",
            help="Kosongkan = tampilkan semua. Pilih satker spesifik untuk filter."
        )
    else:
        sel_satker = []

    st.markdown("---")
    st.caption(f"Telkomsel Enterprise | Bid Management\n{datetime.now():%d %B %Y}")


# ═══════════════════════════════════════════════════════════════════════════
# APPLY FILTERS
# ═══════════════════════════════════════════════════════════════════════════

mask = (
    df["Provinsi"].isin(sel_prov_filter) &
    df["Tipe_Daerah"].isin(sel_tipe)
)
if "Jenis_Pengadaan" in df.columns and sel_jenis:
    mask = mask & df["Jenis_Pengadaan"].isin(sel_jenis)
if "Metode" in df.columns and sel_metode:
    mask = mask & df["Metode"].isin(sel_metode)
if sel_satker:  # Jika user memilih satker spesifik
    mask = mask & df["Satuan_Kerja"].isin(sel_satker)

df_filtered = df[mask].copy()

# Sector splits
df_ict = df_filtered[df_filtered["Is_ICT"] == True].copy()
df_non = df_filtered[df_filtered["Is_ICT"] == False].copy()


# ═══════════════════════════════════════════════════════════════════════════
# METRIC CARDS UTAMA
# ═══════════════════════════════════════════════════════════════════════════

total_pagu = df_filtered["Pagu_Rp"].sum()
total_paket = len(df_filtered)
total_ict_pagu = df_ict["Pagu_Rp"].sum()
total_non_pagu = df_non["Pagu_Rp"].sum()
total_satker = df_filtered["Satuan_Kerja"].nunique() if "Satuan_Kerja" in df_filtered.columns else 0
total_klpd = df_filtered["KLPD"].nunique() if "KLPD" in df_filtered.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(mc_html("Total Pagu RUP", fmt_rp(total_pagu), f"{fmt_n(total_paket)} paket"), unsafe_allow_html=True)
with c2:
    pct_ict = f"{total_ict_pagu/total_pagu*100:.1f}%" if total_pagu > 0 else "0%"
    st.markdown(mc_html("Pagu ICT", fmt_rp(total_ict_pagu), f"{fmt_n(len(df_ict))} paket ({pct_ict})"), unsafe_allow_html=True)
with c3:
    pct_non = f"{total_non_pagu/total_pagu*100:.1f}%" if total_pagu > 0 else "0%"
    st.markdown(mc_html("Pagu Non-ICT", fmt_rp(total_non_pagu), f"{fmt_n(len(df_non))} paket ({pct_non})"), unsafe_allow_html=True)
with c4:
    st.markdown(mc_html("K/L/PD", fmt_n(total_klpd), f"{fmt_n(df_filtered['Provinsi'].nunique())} provinsi"), unsafe_allow_html=True)
with c5:
    st.markdown(mc_html("Satuan Kerja", fmt_n(total_satker)), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Info filter satker aktif
if sel_satker:
    st.markdown(f'<div class="ib">🏢 <strong>Filter Satuan Kerja Aktif:</strong> {len(sel_satker)} satker dipilih — '
                f'{fmt_n(total_paket)} paket ({fmt_rp(total_pagu)})</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TABS UTAMA — SEMUA / ICT / NON-ICT
# ═══════════════════════════════════════════════════════════════════════════

t_all, t_ict, t_ni = st.tabs(["📊  SEMUA SEKTOR", "💻  SEKTOR ICT", "📦  SEKTOR NON-ICT"])

# ─── TAB SEMUA SEKTOR ───
with t_all:
    sub1, sub2 = st.tabs(["🏠 Ringkasan Nasional", "🔎 Deep Dive per Wilayah"])
    with sub1:
        render_ringkasan(df_filtered, total_pagu, "Semua Sektor", "all_n")
    with sub2:
        render_deepdive(df_filtered, total_pagu, "Semua Sektor", "all_d")

# ─── TAB SEKTOR ICT ───
with t_ict:
    st.markdown("""
    <div class="ib">
        💻 <strong>SEKTOR ICT</strong> — Paket mengandung keyword: Internet, Bandwidth, 
        Fiber Optic, Cloud, Server, CCTV, Software, Laptop, Router, dll.<br>
        <em>False positive difilter: Obat, Vaksin, Konstruksi, Makanan, ATK, Kendaraan, dll.</em>
    </div>""", unsafe_allow_html=True)

    # ICT Breakdown per Kategori
    st.markdown('<div class="sh"><h2>📊 Breakdown Kategori ICT</h2><p>Pagu per kategori (Connectivity, Cloud, Hardware, Software, dll)</p></div>', unsafe_allow_html=True)

    df_cat = (df_ict.groupby("Kategori_ICT")
              .agg(Total_Pagu=("Pagu_Rp", "sum"), Jumlah_Paket=("Pagu_Rp", "count"))
              .sort_values("Total_Pagu", ascending=False).reset_index())
    df_cat = df_cat[df_cat["Total_Pagu"] > 0]

    if len(df_cat) > 0:
        fig = hbar(df_cat, "Total_Pagu", "Kategori_ICT",
                   "Pagu per Kategori ICT",
                   f"Total ICT: {fmt_rp(total_ict_pagu)}",
                   sns.color_palette("coolwarm_r", len(df_cat)),
                   total_ict_pagu, figsize=(14, 6))
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    sub1i, sub2i = st.tabs(["🏠 Ringkasan Nasional ICT", "🔎 Deep Dive per Wilayah ICT"])
    with sub1i:
        render_ringkasan(df_ict, total_ict_pagu, "Sektor ICT", "ict_n")
    with sub2i:
        render_deepdive(df_ict, total_ict_pagu, "Sektor ICT", "ict_d")

# ─── TAB SEKTOR NON-ICT ───
with t_ni:
    st.markdown("""
    <div class="ib">
        📦 <strong>SEKTOR NON-ICT</strong> — Semua paket yang <em>tidak</em> terklasifikasi ICT.<br>
        <em>Berguna untuk cross-selling: vendor non-ICT yang punya relasi kuat dengan pemerintah 
        bisa ditawari solusi Telkomsel.</em>
    </div>""", unsafe_allow_html=True)

    sub1n, sub2n = st.tabs(["🏠 Ringkasan Nasional Non-ICT", "🔎 Deep Dive per Wilayah Non-ICT"])
    with sub1n:
        render_ringkasan(df_non, total_non_pagu, "Sektor Non-ICT", "ni_n")
    with sub2n:
        render_deepdive(df_non, total_non_pagu, "Sektor Non-ICT", "ni_d")


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;padding:20px 0;color:#999!important;font-size:12px;">
    Dashboard Rencana Umum Pengadaan (RUP) 2026<br>
    Telkomsel Enterprise | Bid Management — Data Science<br>
    ICT/Non-ICT Classification • Seaborn + Streamlit | {datetime.now():%Y}
</div>
""", unsafe_allow_html=True)
