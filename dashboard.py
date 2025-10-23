# crime_dashboard_final.py
import os
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import calendar

from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# =========================
# CONFIG & WORKDIR
# =========================
base_path = r"D:\crime_dashboard"
# os.makedirs(base_path, exist_ok=True)
# os.chdir(base_path)

# GDrive file IDs (ubah jika perlu)
detail_file_id = "1mnGy6EMP9P-ukX-xRfbM12kMXgktGNWs"   # dataset detail (cases)
agg_file_id    = "1l1ZfgMdK667qkLALpk0LI3eJxDbHv5lP"   # dataset aggregated (area)

# def gdrive_to_download_url(file_id):
#     return f"https://drive.google.com/uc?id={file_id}"

# detail_url = gdrive_to_download_url(detail_file_id)
# agg_url    = gdrive_to_download_url(agg_file_id)

# =========================
# READ DATA (FROM DRIVE)
# =========================
def safe_read_csv(url):
    try:
        df = pd.read_csv(url)
        print(f"✅ Loaded {url} -> {df.shape}")
        return df
    except Exception as e:
        print(f"❌ Fail load {url}: {e}")
        return pd.DataFrame()

# df_agg = safe_read_csv('/Police_Crime.csv')
# df_detail = safe_read_csv('/Crime_Data_with_Binning.csv')
df_agg = pd.read_csv(r'C:\Users\pc\Downloads\crime_dashboard\Police_Crime.csv')
df_detail = pd.read_csv(r'C:\Users\pc\Downloads\crime_dashboard\Crime_Data_with_Binning.csv')

# =========================
# NORMALIZE COLUMN NAMES
# =========================
def normalize_cols(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    # map original -> normalized
    new_names = {orig: orig.strip().lower().replace(' ', '_').replace('-', '_') for orig in df.columns}
    df = df.rename(columns=new_names)
    return df

if not df_agg.empty:
    df_agg = normalize_cols(df_agg)
if not df_detail.empty:
    df_detail = normalize_cols(df_detail)

# =========================
# Ensure area_name exists & clean
# =========================
def ensure_area_name(df):
    df = df.copy()
    if 'area_name' not in df.columns:
        candidates = [c for c in df.columns if 'area' in c]
        if candidates:
            df['area_name'] = df[candidates[0]]
        else:
            df['area_name'] = "Unknown"
    df['area_name'] = df['area_name'].astype(str).str.title().str.strip()
    return df

if not df_agg.empty:
    df_agg = ensure_area_name(df_agg)
if not df_detail.empty:
    df_detail = ensure_area_name(df_detail)

# =========================
# PARSE DATES (robust)
# =========================
def try_parse_dates(df, cols):
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors='coerce', infer_datetime_format=True)
    return df

df_agg = try_parse_dates(df_agg, ['date'])
df_detail = try_parse_dates(df_detail, ['date_time_occ', 'date_rptd', 'date_rptd_time', 'date_occ'])

# derive useful time fields in detail
if not df_detail.empty and 'date_time_occ' in df_detail.columns:
    df_detail['hour_occ'] = df_detail['date_time_occ'].dt.hour
    df_detail['day_name'] = df_detail['date_time_occ'].dt.day_name()
    df_detail['day_of_week'] = df_detail['date_time_occ'].dt.weekday  # Mon=0
    df_detail['year_occ'] = df_detail['date_time_occ'].dt.year

# =========================
# Ensure lat/lon numeric
# =========================
for coord in ['lat', 'lon', 'latitude', 'longitude']:
    if coord in df_detail.columns:
        df_detail[coord] = pd.to_numeric(df_detail[coord], errors='coerce')

# =========================
# POLICE / TOTAL CRIMES in aggregated (safe)
# =========================
if not df_agg.empty:
    police_col = None
    for c in ['police_count', 'police', 'count', 'police_count_']:
        if c in df_agg.columns:
            police_col = c
            break
    if police_col:
        df_agg['police_count'] = pd.to_numeric(df_agg[police_col], errors='coerce').fillna(0).astype(int)
    else:
        df_agg['police_count'] = 0

    if 'total_crimes' not in df_agg.columns:
        candidates = [c for c in df_agg.columns if 'total' in c and 'crime' in c]
        if candidates:
            df_agg['total_crimes'] = pd.to_numeric(df_agg[candidates[0]], errors='coerce').fillna(0).astype(int)
        else:
            if not df_detail.empty:
                agg_from_detail = df_detail.groupby('area_name').size().reset_index(name='total_crimes_from_detail')
                df_agg = pd.merge(df_agg, agg_from_detail, on='area_name', how='left')
                if 'total_crimes_from_detail' in df_agg.columns:
                    df_agg['total_crimes'] = df_agg['total_crimes_from_detail'].fillna(0).astype(int)
                else:
                    df_agg['total_crimes'] = 0
            else:
                df_agg['total_crimes'] = 0

    if 'crimes_per_police' not in df_agg.columns:
        # compute crimes per police (cases / police) if possible
        df_agg['crimes_per_police'] = df_agg.apply(
            lambda r: (r['total_crimes'] / r['police_count']) if (r.get('police_count', 0) and r['police_count'] > 0) else np.nan,
            axis=1
        )

# =========================
# SUMMARY DF from aggregated
# =========================
if not df_agg.empty:
    # pick only expected cols (if exist)
    keep_cols = [c for c in ['area_name', 'year_occ', 'total_crimes', 'police_count', 'crimes_per_police'] if c in df_agg.columns]
    # ensure at least area_name present
    if 'area_name' not in keep_cols:
        df_summary = pd.DataFrame(columns=['area_name', 'year_occ', 'total_crimes', 'police_count', 'crimes_per_police'])
    else:
        # add missing columns with defaults
        df_summary = df_agg.copy()
        for col in ['year_occ', 'total_crimes', 'police_count', 'crimes_per_police']:
            if col not in df_summary.columns:
                if col == 'year_occ':
                    df_summary[col] = pd.NA
                elif col in ['total_crimes', 'police_count']:
                    df_summary[col] = 0
                else:
                    df_summary[col] = np.nan
        df_summary = df_summary[['area_name', 'year_occ', 'total_crimes', 'police_count', 'crimes_per_police']].copy()
        df_summary['total_crimes'] = pd.to_numeric(df_summary['total_crimes'], errors='coerce').fillna(0).astype(int)
        df_summary['police_count'] = pd.to_numeric(df_summary['police_count'], errors='coerce').fillna(0).astype(int)
else:
    df_summary = pd.DataFrame(columns=['area_name', 'year_occ', 'total_crimes', 'police_count', 'crimes_per_police'])

# =========================
# DASH APP LAYOUT (final: only area filter)
# =========================
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Crime Dashboard (Area Dynamic)"

areas = sorted(df_summary['area_name'].dropna().unique()) if not df_summary.empty else (sorted(df_detail['area_name'].dropna().unique()) if not df_detail.empty else [])
default_area = areas[0] if areas else None

preferred_cols = ['date_rptd', 'date_time_occ', 'area_name', 'rpt_dist_no', 'part_1_2', 'crm', 'vict_age', 'vict_sex', 'vict_descent', 'premis', 'status', 'location', 'cross_street', 'lat', 'lon', 'district', 'vict_age_bin']
table_cols = [c for c in preferred_cols if c in df_detail.columns]
if not table_cols and not df_detail.empty:
    table_cols = list(df_detail.columns[:8])

app.layout = dbc.Container([
    html.H1("🚨 Crime Monitoring Dashboard Dinamis", className="text-center my-3"),
    html.P("Pilih satu wilayah. Semua grafik dan insight akan menyesuaikan otomatis.", className="text-center", style={'color': '#444'}),

    # Filters: only area
    dbc.Row([
        dbc.Col(html.Label("🏙️ Pilih Wilayah:"), width=2),
        dbc.Col(dcc.Dropdown(id='area-select',
                             options=[{'label': a, 'value': a} for a in areas],
                             value=default_area,
                             clearable=False), width=6),
    ], className="mb-3"),

    # Insight Umum (national) - 3 cards (will be filled by callback)
    dbc.Row(id='insight-umum-row', className="mb-3"),

    # Insight Wilayah
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Insight Wilayah (Filter saat ini)"),
            dbc.CardBody(html.Div(id='insight-text-top'))
        ]), width=12)
    ], className="mb-3"),

    # Visuals: Police vs Crimes
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Perbandingan: Jumlah Kejahatan vs jumlah polisi per area"), dbc.CardBody(dcc.Graph(id='police-vs-crime-fig', config={'displayModeBar': False}))]), width=12)
    ], className="mb-3"),

    # Heatmap (prominent) right after police-vs-crime
    dbc.Row([
        dbc.Col(dcc.Graph(id='heatmap-day-hour', style={'height': '520px'}), width=12)
    ], className="mb-3"),

    # Map + Crime Chart
    dbc.Row([
        dbc.Col(dcc.Graph(id='map-chart', style={'height': '480px'}), width=6),
        dbc.Col(dcc.Graph(id='crime-chart', style={'height': '480px'}), width=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='premis-chart'), width=6),
        dbc.Col(dcc.Graph(id='age-chart'), width=6)
    ]),

    html.Hr(),
    html.H3("📋 Data Detail (interaktif)"),
    dash_table.DataTable(
        id='data-table',
        columns=[{"name": c, "id": c} for c in table_cols],
        page_size=10,
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        row_selectable='multi',
        style_table={'overflowX': 'auto', 'maxHeight': '400px'},
        style_cell={'textAlign': 'left', 'padding': '6px', 'fontFamily': 'Arial'},
        style_header={'backgroundColor': '#6f42c1', 'color': 'white', 'fontWeight': 'bold'}
    )
], fluid=True)

# =========================
# CALLBACKS (single input: area-select)
# =========================
@app.callback(
    [Output('insight-umum-row', 'children'),
     Output('insight-text-top', 'children'),
     Output('police-vs-crime-fig', 'figure'),
     Output('heatmap-day-hour', 'figure'),
     Output('map-chart', 'figure'),
     Output('crime-chart', 'figure'),
     Output('premis-chart', 'figure'),
     Output('age-chart', 'figure'),
     Output('data-table', 'data')],
    [Input('area-select', 'value')]
)
def update_all(selected_area):
    def empty_fig(title="Tidak ada data"):
        fig = go.Figure()
        fig.update_layout(title=title, paper_bgcolor='white', plot_bgcolor='white')
        return fig

    # --- Insight Umum (national) ---
    total_all = int(len(df_detail)) if not df_detail.empty else 0

    # --- MODIFY: take top area from aggregated df (df_summary / df_agg) used by police vs crimes chart
    if not df_summary.empty and 'total_crimes' in df_summary.columns and df_summary['total_crimes'].sum() > 0:
        try:
            top_area_all = df_summary.sort_values('total_crimes', ascending=False).iloc[0]['area_name']
        except Exception:
            top_area_all = df_detail['area_name'].value_counts().idxmax() if (not df_detail.empty and 'area_name' in df_detail.columns) else "-"
    else:
        top_area_all = df_detail['area_name'].value_counts().idxmax() if (not df_detail.empty and 'area_name' in df_detail.columns) else "-"

    top_crime_all = df_detail['crm'].mode()[0] if ('crm' in df_detail.columns and not df_detail['crm'].dropna().empty) else "-"

    # Build three colored cards (pastel palette)
    card_style_common = {
        'borderRadius': '10px',
        'boxShadow': '0 4px 8px rgba(0,0,0,0.08)',
        'padding': '6px'
    }
    card_total = dbc.Card([
        dbc.CardBody([
            html.H6("Total Kasus Semua Wilayah", className="fw-bold"),
            html.H3(f"{total_all}", className="mb-0")
        ])
    ], style={**card_style_common, 'backgroundColor': '#A5D8FF', 'color': '#05233B'})

    card_topcrime = dbc.Card([
        dbc.CardBody([
            html.H6("Jenis Kejahatan Terbanyak Nasional", className="fw-bold"),
            html.H4(f"{top_crime_all}", className="mb-0")
        ])
    ], style={**card_style_common, 'backgroundColor': '#C3FAE8', 'color': '#053028'})

    card_toparea = dbc.Card([
        dbc.CardBody([
            html.H6("Wilayah dengan Kasus Terbanyak", className="fw-bold"),
            html.H4(f"{top_area_all}", className="mb-0")
        ])
    ], style={**card_style_common, 'backgroundColor': '#E5DBFF', 'color': '#2B1B4A'})

    insight_umum_row = [
        dbc.Col(card_total, width=4),
        dbc.Col(card_topcrime, width=4),
        dbc.Col(card_toparea, width=4)
    ]

    # --- Filter detail by selected area (all visuals driven by this) ---
    dff = df_detail.copy()
    if selected_area is not None and selected_area != "":
        dff = dff[dff['area_name'] == selected_area]

    # --- Insight Wilayah ---
    total_kasus = int(len(dff)) if not dff.empty else 0
    top_crime = dff['crm'].mode()[0] if ('crm' in dff.columns and not dff['crm'].dropna().empty) else "-"
    peak_day = dff['day_name'].mode()[0] if ('day_name' in dff.columns and not dff['day_name'].dropna().empty) else "-"
    peak_hour = int(dff['hour_occ'].mode()[0]) if ('hour_occ' in dff.columns and not dff['hour_occ'].dropna().empty) else "-"
    if 'vict_age' in dff.columns and not dff['vict_age'].dropna().empty:
        avg_age = pd.to_numeric(dff['vict_age'], errors='coerce').mean()
        avg_age_int = int(round(avg_age)) if not np.isnan(avg_age) else "-"
    else:
        avg_age_int = "-"

    # compute ratio (cases per police) for the selected area using df_summary if possible
    ratio_display = "-"
    if not df_summary.empty and selected_area is not None:
        row = df_summary[df_summary['area_name'] == selected_area]
        if not row.empty:
            val = row['crimes_per_police'].values[0]
            if not pd.isna(val):
                ratio_display = f"{val:.2f}"
    # fallback: compute using police_count and total_kasus if available
    if ratio_display == "-" and not df_summary.empty and selected_area is not None:
        row = df_summary[df_summary['area_name'] == selected_area]
        if not row.empty:
            police_cnt_val = row['police_count'].values[0]
            police_cnt = int(police_cnt_val) if (not pd.isna(police_cnt_val)) else 0
            if police_cnt > 0:
                ratio_display = f"{(total_kasus / police_cnt):.2f}"

    insight_lines = [
        html.P(f"Wilayah: {selected_area}"),
        html.P(f"Total Kasus wilayah: {total_kasus}"),
        html.P(f"Jenis kejahatan terbanyak: {top_crime}"),
        html.P(f"Hari Puncak: {peak_day}"),
        html.P(f"Jam Puncak: {str(peak_hour) + '.00' if peak_hour != '-' else '-'}"),
        html.P(f"Rata-rata Umur Korban: {avg_age_int} tahun"),
        html.P(f"Rasio kasus per polisi: {ratio_display}")
    ]
    insight_wilayah = html.Div(insight_lines)

    # --- Visuals ---
    # police vs crime (global comparison) - highlight selected by opacity
    if not df_summary.empty:
        tmp = df_summary[['area_name', 'total_crimes', 'police_count']].copy()
        tmp = tmp.fillna(0)
        tmp = tmp.rename(columns={'area_name': 'Area', 'total_crimes': 'Total Crimes', 'police_count': 'Police Count'})
        df_melt = tmp.melt(id_vars='Area', value_vars=['Total Crimes', 'Police Count'], var_name='Metric', value_name='Value')
        df_melt['Selected'] = df_melt['Area'] == selected_area
        police_vs_fig = px.bar(df_melt, x='Area', y='Value', color='Metric', barmode='group', title="Jumlah Kejahatan vs jumlah polisi per area", height=420)
        for i, d in enumerate(police_vs_fig.data):
            mask = (df_melt['Metric'] == d.name)
            # build opacity list aligned with mask order
            sel_series = df_melt[mask]['Selected'].values
            police_vs_fig.data[i].marker.opacity = [1.0 if sel else 0.35 for sel in sel_series]
        police_vs_fig.update_layout(xaxis={'categoryorder': 'total descending'}, margin=dict(t=50))
    else:
        police_vs_fig = empty_fig("Tidak ada data ringkasan")

    # Heatmap Day x Hour (prominent)
    if (('day_name' in dff.columns or 'day_of_week' in dff.columns) and 'hour_occ' in dff.columns and not dff.empty):
        heat = dff.dropna(subset=['hour_occ'])
        if 'day_of_week' in heat.columns:
            pivot = heat.groupby(['day_of_week', 'hour_occ']).size().reset_index(name='count')
            full = pd.MultiIndex.from_product([range(0,7), range(0,24)], names=['day_of_week','hour_occ']).to_frame(index=False)
            pivot = pd.merge(full, pivot, on=['day_of_week','hour_occ'], how='left').fillna(0)
            pivot['day_name'] = pivot['day_of_week'].apply(lambda d: calendar.day_name[d])
            day_order = [calendar.day_name[i] for i in range(0,7)]
            heatmat = pivot.pivot_table(index='day_name', columns='hour_occ', values='count').reindex(day_order)
        else:
            pivot = heat.groupby(['day_name','hour_occ']).size().reset_index(name='count')
            hours = list(range(0,24))
            days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            full = pd.MultiIndex.from_product([days, hours], names=['day_name','hour_occ']).to_frame(index=False)
            pivot = pd.merge(full, pivot, on=['day_name','hour_occ'], how='left').fillna(0)
            heatmat = pivot.pivot_table(index='day_name', columns='hour_occ', values='count').reindex(days)

        fig_heat = px.imshow(heatmat.values, x=list(range(0,24)), y=heatmat.index,
                             labels=dict(x="Hour of Day", y="Day", color="Count"),
                             title="Heatmap Hari × Jam (Time Hotspot)", aspect='auto')
        fig_heat.update_xaxes(dtick=1)
        fig_heat.update_layout(height=520)
    else:
        fig_heat = empty_fig("Tidak ada informasi hari/jam")

    # Map
    lat_col = 'lat' if 'lat' in dff.columns else ('latitude' if 'latitude' in dff.columns else None)
    lon_col = 'lon' if 'lon' in dff.columns else ('longitude' if 'longitude' in dff.columns else None)
    if lat_col and lon_col and not dff[[lat_col, lon_col]].dropna().empty:
        pts = dff.dropna(subset=[lat_col, lon_col])
        if pts.shape[0] >= 200:
            fig_map = px.density_mapbox(pts, lat=lat_col, lon=lon_col, radius=8,
                                       center=dict(lat=pts[lat_col].mean(), lon=pts[lon_col].mean()),
                                       zoom=11, title=f"Sebaran Kejahatan di {selected_area}" if selected_area else "Sebaran Kejahatan",
                                       color_continuous_scale='OrRd')
            fig_map.update_layout(mapbox_style="carto-positron", margin=dict(t=50))
        else:
            fig_map = px.scatter_mapbox(pts, lat=lat_col, lon=lon_col,
                                       hover_data=[c for c in ['crm','vict_age','status'] if c in pts.columns],
                                       title=f"Lokasi Kejahatan di {selected_area}" if selected_area else "Lokasi Kejahatan",
                                       zoom=11, height=480)
            fig_map.update_layout(mapbox_style="carto-positron", margin=dict(t=50))
    else:
        fig_map = empty_fig("Tidak ada data koordinat")

    # Crime chart (top 12) - dynamic by area
    if 'crm' in dff.columns and not dff['crm'].dropna().empty:
        crime_counts = dff['crm'].value_counts().nlargest(12).reset_index()
        crime_counts.columns = ['Jenis', 'Jumlah']
        fig_crime = px.bar(crime_counts, x='Jenis', y='Jumlah', title="12 Jenis Kejahatan teratas")
    else:
        fig_crime = empty_fig("Tidak ada data jenis kejahatan")

    # Premis chart (top 10)
    premis_col = None
    for c in ['premis', 'premis_desc', 'location', 'premise']:
        if c in dff.columns:
            premis_col = c
            break
    if premis_col and not dff[premis_col].dropna().empty:
        premis_counts = dff[premis_col].value_counts().nlargest(10).reset_index()
        premis_counts.columns = ['Lokasi', 'Jumlah']
        fig_premis = px.bar(premis_counts, x='Lokasi', y='Jumlah', title="Tempat / Premis Kejadian (Top 10)")
    else:
        fig_premis = empty_fig("Tidak ada data lokasi/premis")

    # Age chart
    if 'vict_age' in dff.columns and not dff['vict_age'].dropna().empty:
        fig_age = px.histogram(dff, x='vict_age', nbins=20, title="Distribusi Umur Korban")
    elif 'vict_age_bin' in dff.columns and not dff['vict_age_bin'].dropna().empty:
        age_counts = dff['vict_age_bin'].value_counts().reset_index().rename(columns={'index': 'Age Group', 'vict_age_bin': 'Count'})
        fig_age = px.bar(age_counts, x='Age Group', y='Count', title="Distribusi Kelompok Umur Korban")
    else:
        fig_age = empty_fig("Tidak ada data umur korban")

    # Table data (limit for responsiveness)
    table_data = dff[table_cols].head(200).to_dict('records') if not dff.empty else []

    return insight_umum_row, insight_wilayah, police_vs_fig, fig_heat, fig_map, fig_crime, fig_premis, fig_age, table_data

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    print("🚀 Dashboard running at http://127.0.0.1:8050")
    app.run(debug=True)
