import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control Financiero Pro", page_icon="💰", layout="wide")

# Establecer la conexión con la API de Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función de extracción desde la nube
def cargar_datos():
    try:
        # Lee los datos directamente desde el sheet
        df = conn.read(worksheet="Transacciones", usecols=list(range(6)), ttl=0)
        df = df.dropna(how="all") # Limpia cualquier fila vacía al final del Excel
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Fecha", "Cuenta", "Tipo", "Categoría", "Monto", "Descripción"])

df = cargar_datos()

st.title("📊 Sistema de Inteligencia Financiera Personal")
st.markdown("---")

tab_registro, tab_dashboard = st.tabs(["📝 Registrar Movimiento", "📈 Dashboard e Indicadores Pro"])

# --- PESTAÑA 1: FORMULARIO DE REGISTRO ---
with tab_registro:
    st.subheader("Registrar Nueva Transacción")
    with st.form("formulario_finanzas", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", date.today())
            cuenta = st.selectbox("Cuenta / Destino", ["Tarjeta Sueldo", "Tarjeta Gastos", "Cuenta CTS"])
            tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto"])
        with col2:
            categoria = st.selectbox("Categoría", [
                "Sueldo", "Saldo Inicial", "Alimentación", "Transporte", 
                "Aseo y Cuidado", "Deportes y Hobbies", "Educación", "Entretenimiento", "Otros"
            ])
            monto = st.number_input("Monto (S/)", min_value=0.0, format="%.2f", step=5.0)
            descripcion = st.text_input("Descripción / Notas Cortas")
        
        guardar = st.form_submit_button("Guardar en base de datos")
        
        if guardar:
            nuevo_dato = pd.DataFrame([{
                "Fecha": fecha, "Cuenta": cuenta, "Tipo": tipo, 
                "Categoría": categoria, "Monto": monto, "Descripción": descripcion
            }])
            df = pd.concat([df, nuevo_dato], ignore_index=True)
            
            # Sobrescribir el Google Sheets con el nuevo dataframe actualizado
            conn.update(worksheet="Transacciones", data=df)
            
            st.success("¡Transacción registrada y sincronizada en Google Sheets!")
            st.rerun()


# --- PESTAÑA 2: DASHBOARD FINANCIERO PROFESIONAL ---
with tab_dashboard:
    if df.empty:
        st.info("Ingresa transacciones en la pestaña de registro para activar el análisis analítico.")
    else:
        # Preparación de columnas de tiempo para el análisis en Pandas
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'])
        df['Año'] = df['Fecha_DT'].dt.year
        df['Mes_Num'] = df['Fecha_DT'].dt.month
        
        # Mapeo de meses en español
        meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                    7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        # --- SECCIÓN 0: FILTROS LATERALES DINÁMICOS (Por defecto mes/año actual) ---
        hoy = date.today()
        año_actual = hoy.year
        mes_actual_nombre = meses_es[hoy.month]

        st.sidebar.header("🔍 Filtros de Tiempo")
        
        # Listas únicas para los selectores de la barra lateral
        lista_años = sorted(list(df['Año'].unique()))
        if año_actual not in lista_años:
            lista_años.append(año_actual)
            
        filtro_año = st.sidebar.selectbox("Selecciona el Año", lista_años, index=lista_años.index(año_actual))
        
        lista_meses = list(meses_es.values())
        filtro_mes = st.sidebar.selectbox("Selecciona el Mes", lista_meses, index=lista_meses.index(mes_actual_nombre))

        # --- CÁLCULO DE SALDOS GLOBALES EN VIVO (Histórico acumulado independiente del filtro de mes) ---
        df['Valor_Real'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
        
        saldo_sueldo = df[df["Cuenta"] == "Tarjeta Sueldo"]['Valor_Real'].sum()
        saldo_gastos = df[df["Cuenta"] == "Tarjeta Gastos"]['Valor_Real'].sum()
        saldo_cts = df[df["Cuenta"] == "Cuenta CTS"]['Valor_Real'].sum()
        
        liquidez_disponible = saldo_sueldo + saldo_gastos
        patrimonio_total = liquidez_disponible + saldo_cts

        # Mostrar KPIS de Saldos Reales (No mensuales, sino acumulados al día de hoy)
        st.subheader("💰 Estado de Cuentas (Saldos Actuales)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("💳 Tarjeta Sueldo", f"S/ {saldo_sueldo:,.2f}")
        kpi2.metric("🛍️ Tarjeta Gastos", f"S/ {saldo_gastos:,.2f}")
        kpi3.metric("🔒 Fondo CTS (Intangible)", f"S/ {saldo_cts:,.2f}")
        kpi4.metric("💵 Liquidez para Gastar", f"S/ {liquidez_disponible:,.2f}", 
                    help="Suma de tus tarjetas de uso diario. Excluye tu CTS por salud financiera.")
        
        st.divider()

        # --- APLICACIÓN DE FILTROS PARA EL ANÁLISIS MENSUAL ---
        df_filtrado = df[(df['Año'] == filtro_año) & (df['Mes'] == filtro_mes)]
        
        # Excluir Saldo Inicial de los cálculos de flujos operativos del mes
        df_operativo = df_filtrado[df_filtrado['Categoría'] != 'Saldo Inicial']
        
        ingresos_mes = df_operativo[df_operativo['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos_mes = df_operativo[df_operativo['Tipo'] == 'Gasto']['Monto'].sum()
        balance_mes = ingresos_mes - gastos_mes

        st.subheader(f"📈 Análisis Operativo de {filtro_mes} del {filtro_año}")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📥 Ingresos del Mes", f"S/ {ingresos_mes:,.2f}")
        col_m2.metric("📤 Gastos del Mes", f"S/ {gastos_mes:,.2f}")
        col_m3.metric("⚖️ Balance Neto", f"S/ {balance_mes:,.2f}", 
                      delta=f"{balance_mes:,.2f}" if balance_mes >= 0 else f"{balance_mes:,.2f}",
                      delta_color="normal")

        # --- SECCIÓN: ALERTAS DE CONTROL FINANCIERO Y TOMA DE DECISIONES ---
        st.markdown("#### 🚨 Semáforo de Control Presupuestal")
        
        if liquidez_disponible < 200:
            st.error(f"⚠️ **¡Alerta de Liquidez Crítica!** Tu saldo disponible en tarjetas es de S/ {liquidez_disponible:.2f}. Evita cualquier gasto no esencial inmediatamente.")
        
        if ingresos_mes > 0:
            tasa_ahorro = (balance_mes / ingresos_mes) * 100
            if balance_mes < 0:
                st.error(f"🛑 **Déficit Financiero:** Este mes estás gastando más de lo que ingresas (Déficit de S/ {abs(balance_mes):,.2f}). ¡Detén consumos innecesarios!")
            elif tasa_ahorro < 10:
                st.warning(f"⚠️ **Zona de Riesgo:** Tu tasa de ahorro es muy baja ({tasa_ahorro:.1f}%). Estás viviendo muy al límite de tus ingresos. Intenta ajustar el gasto de entretenimiento o alimentación.")
            elif tasa_ahorro >= 20:
                st.success(f"✅ **Salud Financiera Excelente:** Has ahorrado el {tasa_ahorro:.1f}% de tus ingresos este mes. ¡Vas por muy buen camino para tus metas!")
            else:
                st.info(f"💡 **Estabilidad:** Tu tasa de ahorro es del {tasa_ahorro:.1f}%. Cumples con el mínimo recomendado, pero evalúa si puedes optimizar algún servicio o gasto menor.")
        else:
            if gastos_mes > 0:
                st.warning("Aún no registras ingresos operativos este mes, pero ya reportas gastos. Monitorea tu balance.")
            else:
                st.info("Sin movimientos operativos registrados en este periodo de tiempo.")

        st.divider()

        # --- SECCIÓN: GRÁFICOS INTERACTIVOS ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### 🍩 Composición del Gasto del Mes")
            df_gastos_mes = df_operativo[df_operativo['Tipo'] == 'Gasto']
            if not df_gastos_mes.empty:
                gastos_pie = df_gastos_mes.groupby("Categoría")["Monto"].sum().reset_index()
                fig_pie = px.pie(gastos_pie, values="Monto", names="Categoría", 
                                 hole=0.4, title="¿A dónde se fue tu dinero?")
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay gastos registrados en este mes para generar el gráfico.")

        with col_g2:
            st.markdown("#### 📈 Comportamiento Anual (Ingresos vs Gastos)")
            # Agrupar todo el año operativo para ver la tendencia de los meses
            df_año = df[(df['Año'] == filtro_año) & (df['Categoría'] != 'Saldo Inicial')]
            if not df_año.empty:
                tendencia = df_año.groupby(["Mes_Num", "Mes", "Tipo"])["Monto"].sum().reset_index()
                tendencia = tendencia.sort_values("Mes_Num")
                
                fig_line = px.line(tendencia, x="Mes", y="Monto", color="Tipo",
                                   markers=True, title=f"Evolución Histórica - {filtro_año}",
                                   color_discrete_map={"Ingreso": "#00CC96", "Gasto": "#EF553B"})
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Datos insuficientes para trazar la tendencia anual.")

        # Tabla Transaccional Detallada del Mes
        with st.expander(f"🔍 Ver Transacciones Detalladas de {filtro_mes}"):
            st.dataframe(df_filtrado.sort_values(by="Fecha", ascending=False)[["Fecha", "Cuenta", "Tipo", "Categoría", "Monto", "Descripción"]], 
                         use_container_width=True)