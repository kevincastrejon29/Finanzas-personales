import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control Financiero Pro", page_icon="💰", layout="wide")

# --- 🔒 SISTEMA DE AUTENTICACIÓN ---
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
# --- FIN DEL SISTEMA DE AUTENTICACIÓN ---

# Conexión principal a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Extracción de Datos (Tablas Transacciones y Prestamos)
def cargar_transacciones():
    try:
        df = conn.read(worksheet="Transacciones", usecols=list(range(6)), ttl=0)
        df = df.dropna(how="all")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["Fecha", "Cuenta", "Tipo", "Categoría", "Monto", "Descripción"])

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

st.title("📊 Sistema de Inteligencia Financiera Personal")
st.markdown("---")

tab_registro, tab_dashboard = st.tabs(["📝 Registrar Movimiento", "📈 Dashboard e Indicadores Pro"])

# --- PESTAÑA 1: FORMULARIO DE REGISTRO OPTIMIZADO ---
with tab_registro:
    st.subheader("Registrar Nueva Transacción")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", date.today())
        tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto", "Transferencia", "Préstamo Otorgado", "Cobro de Préstamo"])
        monto = st.number_input("Monto (S/)", min_value=0.0, format="%.2f", step=5.0)

    with col2:
        if tipo == "Ingreso":
            cuenta = st.selectbox("Cuenta Destino", ["Tarjeta Sueldo", "Tarjeta Gastos", "Cuenta CTS"])
            categoria = st.selectbox("Categoría", ["Sueldo", "Devoluciones", "Otros ingresos"])
            descripcion = st.text_input("Descripción / Notas Cortas")
            
        elif tipo == "Gasto":
            cuenta = st.selectbox("Cuenta Origen", ["Tarjeta Sueldo", "Tarjeta Gastos"])
            categoria = st.selectbox("Categoría", ["Alimentación", "Transporte", "Aseo y Cuidado Personal", "Deporte y Hobbies", "Suscripciones entertainment", "Educación", "Otros Gastos"])
            descripcion = st.text_input("Descripción / Notas Cortas")
            
        elif tipo == "Transferencia":
            cuenta_origen = st.selectbox("Desde la Cuenta", ["Tarjeta Sueldo", "Tarjeta Gastos", "Cuenta CTS"])
            cuenta = st.selectbox("Hacia la Cuenta", ["Tarjeta Sueldo", "Tarjeta Gastos", "Cuenta CTS"])
            categoria = "Transferencia"
            descripcion = st.text_input("Descripción / Notas Cortas", "Traspaso de fondos propio")
            
        elif tipo == "Préstamo Otorgado":
            cuenta = st.selectbox("Cuenta Origen (De donde sale el dinero)", ["Tarjeta Sueldo", "Tarjeta Gastos"])
            persona = st.text_input("¿A quién le prestas? (Nombre)")
            interes = st.number_input("Porcentaje de Interés (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            fecha_dev = st.date_input("Fecha estimada de devolución", date.today())
            categoria = "Préstamo Otorgado"
            descripcion = st.text_input("Descripción", f"Préstamo a {persona}")
            
        elif tipo == "Cobro de Préstamo":
            df_p_pendientes = df_p[df_p["Estado"] == "Pendiente"]
            if df_p_pendientes.empty:
                st.warning("No registras préstamos pendientes por cobrar.")
                st.stop()
            
            # Formatear opciones legibles para el selector
            opciones_p = df_p_pendientes.apply(lambda x: f"{x['Persona']} | S/ {x['Monto']} (Vence: {x['Fecha_Devolucion']})", axis=1).tolist()
            prestamo_sel = st.selectbox("Selecciona el préstamo a cobrar", opciones_p)
            
            # Extraer fila seleccionada
            idx_sel = opciones_p.index(prestamo_sel)
            p_registro = df_p_pendientes.iloc[idx_sel]
            
            cuenta = st.selectbox("Cuenta Destino (Donde ingresa el dinero)", ["Tarjeta Sueldo", "Tarjeta Gastos"])
            categoria = "Préstamo Cobrado"
            # Calcular el monto final considerando si se pactó interés
            monto_final = float(p_registro['Monto']) * (1 + (float(p_registro['Interes']) / 100))
            st.success(f"Monto calculado a recibir (con interés si aplica): S/ {monto_final:,.2f}")
            descripcion = st.text_input("Descripción", f"Cobro devuelto por {p_registro['Persona']}")

    if st.button("Guardar en base de datos", type="primary", use_container_width=True):
        # LÓGICA DE ESCRITURA SEGÚN EL TIPO
        if tipo == "Transferencia":
            nuevo_trans = pd.DataFrame([
                {"Fecha": fecha, "Cuenta": cuenta_origen, "Tipo": "Gasto", "Categoría": "Transferencia", "Monto": monto, "Descripción": descripcion},
                {"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Ingreso", "Categoría": "Transferencia", "Monto": monto, "Descripción": descripcion}
            ])
            df = pd.concat([df, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df)
            
        elif tipo == "Préstamo Otorgado":
            # 1. Afecta el saldo restando el dinero de la cuenta elegida
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Gasto", "Categoría": "Préstamo Otorgado", "Monto": monto, "Descripción": descripcion}])
            df = pd.concat([df, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df)
            
            # 2. Crea el registro de control de deuda activa
            nuevo_p = pd.DataFrame([{"Fecha": fecha, "Persona": persona, "Monto": monto, "Interes": interes, "Fecha_Devolucion": fecha_dev, "Cuenta": cuenta, "Estado": "Pendiente"}])
            df_p = pd.concat([df_p, nuevo_p], ignore_index=True)
            conn.update(worksheet="Prestamos", data=df_p)
            
        elif tipo == "Cobro de Préstamo":
            # 1. Afecta el saldo sumando el dinero de vuelta
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Ingreso", "Categoría": "Préstamo Cobrado", "Monto": monto_final, "Descripción": descripcion}])
            df = pd.concat([df, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df)
            
            # 2. Actualiza el estado del préstamo original en la tabla de control
            # Encontrar el índice original exacto emparejando criterios básicos
            condicion = (df_p['Persona'] == p_registro['Persona']) & (df_p['Monto'] == p_registro['Monto']) & (df_p['Estado'] == 'Pendiente')
            df_p.loc[condicion, 'Estado'] = 'Cobrado'
            conn.update(worksheet="Prestamos", data=df_p)
        
        else: # Ingreso o Gasto normal
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": tipo, "Categoría": categoria, "Monto": monto, "Descripción": descripcion}])
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

        # Filtros Laterales
        hoy = date.today()
        año_actual = hoy.year
        mes_actual_nombre = meses_es[hoy.month]

        st.sidebar.header("🔍 Filtros de Tiempo")
        lista_años = sorted(list(df['Año'].unique()))
        if año_actual not in lista_años: lista_años.append(año_actual)
        filtro_año = st.sidebar.selectbox("Selecciona el Año", lista_años, index=lista_años.index(año_actual))
        
        lista_meses = list(meses_es.values())
        filtro_mes = st.sidebar.selectbox("Selecciona el Mes", lista_meses, index=lista_meses.index(mes_actual_nombre))

        # Cálculo de Saldos de Cuentas (Histórico Acumulado)
        df['Valor_Real'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
        
        saldo_sueldo = df[df["Cuenta"] == "Tarjeta Sueldo"]['Valor_Real'].sum()
        saldo_gastos = df[df["Cuenta"] == "Tarjeta Gastos"]['Valor_Real'].sum()
        saldo_cts = df[df["Cuenta"] == "Cuenta CTS"]['Valor_Real'].sum()
        
        liquidez_disponible = saldo_sueldo + saldo_gastos

        st.subheader("💰 Estado de Cuentas (Saldos Actuales)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("💳 Tarjeta Sueldo", f"S/ {saldo_sueldo:,.2f}")
        kpi2.metric("🛍️ Tarjeta Gastos", f"S/ {saldo_gastos:,.2f}")
        kpi3.metric("🔒 Fondo CTS", f"S/ {saldo_cts:,.2f}")
        kpi4.metric("💵 Liquidez para Gastar", f"S/ {liquidez_disponible:,.2f}")
        
        st.divider()

        # Análisis Mensual Filtrado
        df_filtrado = df[(df['Año'] == filtro_año) & (df['Mes'] == filtro_mes)]
        
        # EXCLUSIÓN CRÍTICA: Quitamos saldos iniciales, transferencias y préstamos para medir consumo real operativo
        exclusiones = ['Saldo Inicial', 'Transferencia', 'Préstamo Otorgado', 'Préstamo Cobrado']
        df_operativo = df_filtrado[~df_filtrado['Categoría'].isin(exclusiones)]
        
        ingresos_mes = df_operativo[df_operativo['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos_mes = df_operativo[df_operativo['Tipo'] == 'Gasto']['Monto'].sum()
        balance_mes = ingresos_mes - gastos_mes

        st.subheader(f"📈 Análisis Operativo - {filtro_mes} {filtro_año}")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📥 Ingresos del Mes", f"S/ {ingresos_mes:,.2f}")
        col_m2.metric("📤 Gastos Consumo", f"S/ {gastos_mes:,.2f}")
        col_m3.metric("⚖️ Balance Neto", f"S/ {balance_mes:,.2f}", delta=f"{balance_mes:,.2f}")

        # --- 🔍 NUEVA SECCIÓN: CONTROL DE PRÉSTAMOS ACTIVOS ---
        st.divider()
        st.subheader("🤝 Control de Préstamos y Cuentas por Cobrar")
        
        df_p_pendientes = df_p[df_p["Estado"] == "Pendiente"]
        
        if not df_p_pendientes.empty:
            total_prestado = df_p_pendientes["Monto"].sum()
            st.info(f"🚩 Tienes un total de **S/ {total_prestado:,.2f}** colocados en préstamos pendientes de cobro.")
            
            # Preparar tabla visual explicativa
            df_p_visual = df_p_pendientes[["Fecha", "Persona", "Monto", "Interes", "Fecha_Devolucion", "Cuenta"]].copy()
            df_p_visual["Días para el Cobro"] = df_p_visual["Fecha_Devolucion"].apply(lambda x: (x - date.today()).days)
            
            # Alertar visualmente si hay retrasos financieros
            retrasados = df_p_visual[df_p_visual["Días para el Cobro"] < 0]
            if not retrasados.empty:
                st.error(f"⚠️ ¡Atención! Hay {len(retrasados)} préstamo(s) que ya cumplieron su fecha estimada de retorno.")
                
            st.dataframe(df_p_visual, use_container_width=True)
        else:
            st.success("✅ No tienes capital fuera. Todos tus fondos están dentro de tus cuentas personales.")
        
        st.divider()

        # Gráficos Operativos
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 🍩 Composición del Gasto del Mes (Consumo Real)")
            df_gastos_mes = df_operativo[df_operativo['Tipo'] == 'Gasto']
            if not df_gastos_mes.empty:
                gastos_pie = df_gastos_mes.groupby("Categoría")["Monto"].sum().reset_index()
                fig_pie = px.pie(gastos_pie, values="Monto", names="Categoría", hole=0.4)
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sin consumos registrados en este periodo.")

        with col_g2:
            st.markdown("#### 📈 Tendencia Anual Operativa")
            df_año = df[(df['Año'] == filtro_año) & (~df['Categoría'].isin(exclusiones))]
            if not df_año.empty:
                tendencia = df_año.groupby(["Mes_Num", "Mes", "Tipo"])["Monto"].sum().reset_index().sort_values("Mes_Num")
                fig_line = px.line(tendencia, x="Mes", y="Monto", color="Tipo", markers=True,
                                   color_discrete_map={"Ingreso": "#00CC96", "Gasto": "#EF553B"})
                st.plotly_chart(fig_line, use_container_width=True)

        with st.expander(f"🔍 Ver Libro Diario Filtrado"):
            st.dataframe(df_filtrado.sort_values(by="Fecha", ascending=False)[["Fecha", "Cuenta", "Tipo", "Categoría", "Monto", "Descripción"]], use_container_width=True)