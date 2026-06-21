import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control Financiero Pro", page_icon="", layout="wide")

# ---SISTEMA DE AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Acceso Seguro")
        st.write("Por favor, identifícate para ver tus finanzas.")
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password") 
            ingresar = st.form_submit_button("Ingresar", use_container_width=True)
            if ingresar:
                if usuario == st.secrets["credenciales"]["usuario"] and password == st.secrets["credenciales"]["password"]:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")
    st.stop() 

# --- ÁRBOL DE JERARQUÍAS (DICCIONARIOS MAESTROS) ---
SUBCATEGORIAS_GASTO = {
    "Alimentación": ["Supermercado", "Restaurantes y delivery", "Cafés y snacks", "Agua, bebidas, suplementos alimenticios"],
    "Vivienda": ["Arriendo / hipoteca", "Servicios básicos (agua, luz, gas)", "Internet y TV", "Mantenimiento y reparaciones", "Muebles y electrodomésticos"],
    "Transporte": ["Transporte público", "Combustible", "Mantenimiento vehicular", "Estacionamientos y peajes", "Apps de transporte (Uber, InDrive, Didi, etc)"],
    "Salud y bienestar": ["Seguro médico", "Consultas y medicamentos", "Terapias", "Gimnasio", "Exámenes médicos"],
    "Aseo y cuidado personal": ["Productos de aseo", "Barbería / peluquería", "Cosmética", "Ropa interior y cuidado personal"],
    "Ropa y accesorios": ["Ropa diaria", "Calzado", "Accesorios", "Reparaciones de ropa"],
    "Educación y desarrollo": ["Cursos y certificaciones", "Libros", "Plataformas educativas", "Idiomas", "Eventos académicos"],
    "Deportes y hobbies": ["Equipamiento deportivo", "Inscripciones", "Clases", "Materiales de hobby"],
    "Suscripciones y entretenimiento": ["Streaming (Netflix, Spotify, etc.)", "Videojuegos", "Cine y espectáculos", "Suscripciones digitales"],
    "Finanzas y obligaciones": ["Créditos y préstamos", "Tarjetas de crédito", "Intereses", "Comisiones bancarias", "Impuestos"],
    "Ahorro e inversión": ["Ahorro programado", "Inversiones", "Fondo de emergencia", "Jubilación"],
    "Regalos y donaciones": ["Regalos", "Donaciones", "Eventos sociales"],
    "Tecnología y comunicación": ["Teléfono móvil", "Equipos electrónicos", "Software no recurrente", "Accesorios tecnológicos"]
}

SUBCATEGORIAS_INGRESO = {
    "Sueldo": ["Pago regular", "Bono / Gratificación", "Adelanto"],
    "Devoluciones": ["Reembolso de tienda", "Devolución de terceros"],
    "Otros ingresos": ["Cachuelo / Freelance", "Venta de cosas", "Rendimientos / Intereses"]
}

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_transacciones():
    try:
        df = conn.read(worksheet="Transacciones", usecols=list(range(7)), ttl=0)
        df = df.dropna(how="all")
        # Rellenar con "General" si hay filas antiguas creadas antes de insertar la columna
        if 'Subcategoría' not in df.columns: df['Subcategoría'] = "General"
        df['Subcategoría'] = df['Subcategoría'].fillna("General")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["Fecha", "Cuenta", "Tipo", "Categoría", "Subcategoría", "Monto", "Descripción"])

def cargar_prestamos():
    try:
        df = conn.read(worksheet="Prestamos", usecols=list(range(7)), ttl=0)
        df = df.dropna(how="all")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        df['Fecha_Devolucion'] = pd.to_datetime(df['Fecha_Devolucion']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["Fecha", "Persona", "Monto", "Interes", "Fecha_Devolucion", "Cuenta", "Estado"])

df = cargar_transacciones()
df_p = cargar_prestamos()

st.title("Sistema de Inteligencia Financiera Personal")
st.markdown("---")

tab_registro, tab_dashboard = st.tabs(["Registrar movimiento", "Dashboard e Indicadores"])

# --- PESTAÑA 1: FORMULARIO DE REGISTRO CON CASCADA DOBLE ---
with tab_registro:
    st.subheader("Registrar Nueva Transacción")
    cuentas_todas = ["Tarjeta Sueldo", "Tarjeta Gastos", "Efectivo", "Cuenta CTS"]
    cuentas_operativas = ["Tarjeta Sueldo", "Tarjeta Gastos", "Efectivo"]
    
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", date.today())
        tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto", "Transferencia", "Préstamo Otorgado", "Cobro de Préstamo"])
        monto = st.number_input("Monto (S/)", min_value=0.0, format="%.2f", step=5.0)

    with col2:
        if tipo == "Ingreso":
            cuenta = st.selectbox("Cuenta Destino", cuentas_todas)
            categoria = st.selectbox("Categoría", list(SUBCATEGORIAS_INGRESO.keys()))
            subcategoria = st.selectbox("Subcategoría", SUBCATEGORIAS_INGRESO[categoria])
            descripcion = st.text_input("Descripción / Notas Cortas")
            
        elif tipo == "Gasto":
            cuenta = st.selectbox("Cuenta Origen", cuentas_operativas)
            categoria = st.selectbox("Categoría", list(SUBCATEGORIAS_GASTO.keys()))
            subcategoria = st.selectbox("Subcategoría", SUBCATEGORIAS_GASTO[categoria])
            descripcion = st.text_input("Descripción / Notas Cortas")
            
        elif tipo == "Transferencia":
            cuenta_origen = st.selectbox("Desde la Cuenta (Sale el dinero)", cuentas_todas)
            cuenta = st.selectbox("Hacia la Cuenta (Entra el dinero)", cuentas_todas)
            categoria = "Transferencia"
            subcategoria = "Traspaso interno"
            descripcion = st.text_input("Descripción / Notas Cortas", "Traspaso de fondos")
            
        elif tipo == "Préstamo Otorgado":
            cuenta = st.selectbox("Cuenta Origen (De donde sale el dinero)", cuentas_operativas)
            persona = st.text_input("¿A quién le prestas? (Nombre)")
            interes = st.number_input("Porcentaje de Interés (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            fecha_dev = st.date_input("Fecha estimada de devolución", date.today())
            categoria = "Préstamo Otorgado"
            subcategoria = f"A: {persona}"
            descripcion = st.text_input("Descripción", f"Préstamo a {persona}")
            
        elif tipo == "Cobro de Préstamo":
            df_p_pendientes = df_p[df_p["Estado"] == "Pendiente"]
            if df_p_pendientes.empty:
                st.warning("No registras préstamos pendientes por cobrar.")
                st.stop()
            opciones_p = df_p_pendientes.apply(lambda x: f"{x['Persona']} | S/ {x['Monto']} (Vence: {x['Fecha_Devolucion']})", axis=1).tolist()
            prestamo_sel = st.selectbox("Selecciona el préstamo a cobrar", opciones_p)
            idx_sel = opciones_p.index(prestamo_sel)
            p_registro = df_p_pendientes.iloc[idx_sel]
            cuenta = st.selectbox("Cuenta Destino (Donde ingresa el dinero)", cuentas_operativas)
            categoria = "Préstamo Cobrado"
            subcategoria = f"De: {p_registro['Persona']}"
            monto_final = float(p_registro['Monto']) * (1 + (float(p_registro['Interes']) / 100))
            st.success(f"Monto calculado a recibir: S/ {monto_final:,.2f}")
            descripcion = st.text_input("Descripción", f"Cobro devuelto por {p_registro['Persona']}")

    if st.button("Guardar en base de datos", type="primary", use_container_width=True):
        if tipo == "Transferencia":
            nuevo_trans = pd.DataFrame([
                {"Fecha": fecha, "Cuenta": cuenta_origen, "Tipo": "Gasto", "Categoría": "Transferencia", "Subcategoría": subcategoria, "Monto": monto, "Descripción": descripcion},
                {"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Ingreso", "Categoría": "Transferencia", "Subcategoría": subcategoria, "Monto": monto, "Descripción": descripcion}
            ])
        elif tipo == "Préstamo Otorgado":
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Gasto", "Categoría": "Préstamo Otorgado", "Subcategoría": subcategoria, "Monto": monto, "Descripción": descripcion}])
            nuevo_p = pd.DataFrame([{"Fecha": fecha, "Persona": persona, "Monto": monto, "Interes": interes, "Fecha_Devolucion": fecha_dev, "Cuenta": cuenta, "Estado": "Pendiente"}])
            df_p = pd.concat([df_p, nuevo_p], ignore_index=True)
            conn.update(worksheet="Prestamos", data=df_p)
        elif tipo == "Cobro de Préstamo":
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Ingreso", "Categoría": "Préstamo Cobrado", "Subcategoría": subcategoria, "Monto": monto_final, "Descripción": descripcion}])
            condicion = (df_p['Persona'] == p_registro['Persona']) & (df_p['Monto'] == p_registro['Monto']) & (df_p['Estado'] == 'Pendiente')
            df_p.loc[condicion, 'Estado'] = 'Cobrado'
            conn.update(worksheet="Prestamos", data=df_p)
        else:
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": tipo, "Categoría": categoria, "Subcategoría": subcategoria, "Monto": monto, "Descripción": descripcion}])
            
        df = pd.concat([df, nuevo_trans], ignore_index=True)
        conn.update(worksheet="Transacciones", data=df)
        st.success("¡Operación procesada y sincronizada correctamente!")
        st.rerun()

# --- PESTAÑA 2: DASHBOARD FINANCIERO PROFESIONAL ---
with tab_dashboard:
    if df.empty:
        st.info("No hay datos operativos registrados.")
    else:
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'])
        df['Año'] = df['Fecha_DT'].dt.year
        df['Mes_Num'] = df['Fecha_DT'].dt.month
        
        meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                    7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        hoy = date.today()
        año_actual = hoy.year
        mes_actual_nombre = meses_es[hoy.month]

        # Barra Lateral
        st.sidebar.header("🔍 Filtros de Visualización")
        lista_años = sorted(list(df['Año'].unique()))
        if año_actual not in lista_años: lista_años.append(año_actual)
        filtro_año = st.sidebar.selectbox("Selecciona el Año", lista_años, index=lista_años.index(año_actual))
        
        lista_meses = list(meses_es.values())
        filtro_mes = st.sidebar.selectbox("Selecciona el Mes", lista_meses, index=lista_meses.index(mes_actual_nombre))

        # Filtro de Categoría Inteligente
        df_filtrado_mes = df[(df['Año'] == filtro_año) & (df['Mes'] == filtro_mes)]
        exclusiones_filtro = ['Saldo Inicial', 'Transferencia', 'Préstamo Otorgado', 'Préstamo Cobrado']
        categorias_disponibles = sorted(list(df_filtrado_mes[~df_filtrado_mes['Categoría'].isin(exclusiones_filtro)]['Categoría'].unique()))
        
        opciones_categorias = ["Todas las categorías"] + categorias_disponibles
        filtro_categoria = st.sidebar.selectbox("Enfocar en Categoría", opciones_categorias)

        # Saldos Globales
        df['Valor_Real'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
        saldo_sueldo = df[df["Cuenta"] == "Tarjeta Sueldo"]['Valor_Real'].sum()
        saldo_gastos = df[df["Cuenta"] == "Tarjeta Gastos"]['Valor_Real'].sum()
        saldo_efectivo = df[df["Cuenta"] == "Efectivo"]['Valor_Real'].sum()
        saldo_cts = df[df["Cuenta"] == "Cuenta CTS"]['Valor_Real'].sum()
        liquidez_disponible = saldo_sueldo + saldo_gastos + saldo_efectivo

        st.subheader("Estado de Cuentas (Saldos Actuales)")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("💳 Tarjeta Sueldo", f"S/ {saldo_sueldo:,.2f}")
        kpi2.metric("🛍️ Tarjeta Gastos", f"S/ {saldo_gastos:,.2f}")
        kpi3.metric("💵 Efectivo", f"S/ {saldo_efectivo:,.2f}")
        kpi4.metric("🔒 Fondo CTS", f"S/ {saldo_cts:,.2f}")
        kpi5.metric("💰 Liquidez Total", f"S/ {liquidez_disponible:,.2f}")
        st.divider()

        # --- FÓRMULAS DE RIQUEZA (SEPARACIÓN DE CONSUMO VS INVERSIÓN) ---
        exclusiones_consumo = exclusiones_filtro + ['Ahorro e inversión']
        
        ingresos_mes = df_filtrado_mes[(df_filtrado_mes['Tipo'] == 'Ingreso') & (~df_filtrado_mes['Categoría'].isin(exclusiones_filtro))]['Monto'].sum()
        gastos_consumo = df_filtrado_mes[(df_filtrado_mes['Tipo'] == 'Gasto') & (~df_filtrado_mes['Categoría'].isin(exclusiones_consumo))]['Monto'].sum()
        ahorro_inversion_mes = df_filtrado_mes[(df_filtrado_mes['Tipo'] == 'Gasto') & (df_filtrado_mes['Categoría'] == 'Ahorro e inversión')]['Monto'].sum()
        
        flujo_libre = ingresos_mes - gastos_consumo - ahorro_inversion_mes

        st.subheader(f"Balance Operativo - {filtro_mes} {filtro_año}")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("📥 Ingresos", f"S/ {ingresos_mes:,.2f}")
        col_m2.metric("📤 Gastos Consumo", f"S/ {gastos_consumo:,.2f}", help="Dinero "quemado". Excluye lo que mandaste a ahorro.")
        col_m3.metric("💎 Ahorro / Inversión", f"S/ {ahorro_inversion_mes:,.2f}", help="Capital transferido para tu futuro.")
        col_m4.metric("⚖️ Flujo Libre", f"S/ {flujo_libre:,.2f}", help="Lo que te queda en la cuenta tras gastar e invertir.")
        st.divider()

        # Control de Préstamos
        st.subheader("Control de Préstamos y Cuentas por Cobrar")
        df_p_pendientes = df_p[df_p["Estado"] == "Pendiente"]
        if not df_p_pendientes.empty:
            total_prestado = df_p_pendientes["Monto"].sum()
            st.info(f"🚩 Tienes un total de **S/ {total_prestado:,.2f}** colocados en préstamos pendientes de cobro.")
            df_p_visual = df_p_pendientes[["Fecha", "Persona", "Monto", "Interes", "Fecha_Devolucion", "Cuenta"]].copy()
            df_p_visual["Días para el Cobro"] = df_p_visual["Fecha_Devolucion"].apply(lambda x: (x - date.today()).days)
            retrasados = df_p_visual[df_p_visual["Días para el Cobro"] < 0]
            if not retrasados.empty: st.error(f"⚠️ ¡Atención! Hay {len(retrasados)} préstamo(s) que ya cumplieron su fecha de retorno.")
            st.dataframe(df_p_visual, use_container_width=True)
        else:
            st.success("✅ No tienes capital fuera. Todos tus fondos están en tus cuentas.")
        st.divider()

        # --- GRÁFICOS DINÁMICOS CON DRILL-DOWN ---
        df_operativo_mes = df_filtrado_mes[~df_filtrado_mes['Categoría'].isin(exclusiones_filtro)]
        if filtro_categoria != "Todas las Categorías":
            df_graficos = df_operativo_mes[df_operativo_mes['Categoría'] == filtro_categoria]
            df_tabla_final = df_filtrado_mes[df_filtrado_mes['Categoría'] == filtro_categoria]
        else:
            df_graficos = df_operativo_mes
            df_tabla_final = df_filtrado_mes

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if filtro_categoria != "Todas las Categorías":
                st.markdown(f"#### Desglose de Subcategorías: {filtro_categoria}")
                df_pie = df_graficos
                if not df_pie.empty:
                    pie_data = df_pie.groupby("Subcategoría")["Monto"].sum().reset_index()
                    fig_pie = px.pie(pie_data, values="Monto", names="Subcategoría", hole=0.4)
                    fig_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.info("Sin movimientos.")
            else:
                st.markdown("#### Composición del Gasto (Por Categorías)")
                df_pie_general = df_graficos[(df_graficos['Tipo'] == 'Gasto') & (~df_graficos['Categoría'].isin(exclusiones_consumo))]
                if not df_pie_general.empty:
                    pie_data = df_pie_general.groupby("Categoría")["Monto"].sum().reset_index()
                    fig_pie = px.pie(pie_data, values="Monto", names="Categoría", hole=0.4)
                    fig_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.info("Sin gastos de consumo.")

        with col_g2:
            st.markdown("#### Tendencia Anual Operativa")
            df_año = df[(df['Año'] == filtro_año) & (~df['Categoría'].isin(exclusiones_filtro))]
            if not df_año.empty:
                tendencia = df_año.groupby(["Mes_Num", "Mes", "Tipo"])["Monto"].sum().reset_index().sort_values("Mes_Num")
                fig_line = px.line(tendencia, x="Mes", y="Monto", color="Tipo", markers=True,
                                   color_discrete_map={"Ingreso": "#00CC96", "Gasto": "#EF553B"})
                st.plotly_chart(fig_line, use_container_width=True)

        # Tabla de Detalles (Muestra las 7 columnas)
        titulo_tabla = f"🔍 Detalle Transaccional: {filtro_categoria}" if filtro_categoria != "Todas las Categorías" else f"🔍 Ver Libro Diario Completo ({filtro_mes})"
        with st.expander(titulo_tabla):
            if df_tabla_final.empty: st.write("No se encontraron registros.")
            else: st.dataframe(df_tabla_final.sort_values(by="Fecha", ascending=False)[["Fecha", "Cuenta", "Tipo", "Categoría", "Subcategoría", "Monto", "Descripción"]], use_container_width=True)