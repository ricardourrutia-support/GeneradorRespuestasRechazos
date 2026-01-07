import streamlit as st
import pandas as pd
import re

# Configuración de la página
st.set_page_config(page_title="Generador de Respuestas Zendesk", page_icon="🚕", layout="wide")

st.title("🚕 Generador de Respuestas para Zendesk")
st.markdown("""
Sube la nómina de rechazos. El sistema detectará automáticamente:
* **Empresa vs Persona:** Basado en si el RUT base es > 70.000.000.
* **Error de Tarjeta:** Si el número de cuenta tiene 15 o más dígitos.
""")

# --- BARRA LATERAL (INPUTS DEL AGENTE) ---
st.sidebar.header("Datos del Agente")
nombre_agente = st.sidebar.text_input("Tu Nombre", value="Ricardo")
pie_firma = st.sidebar.text_input("Tu Firma / Cargo", value="Cabify Support")

# --- FUNCIONES DE LÓGICA ---

def limpiar_rut(rut_raw):
    """
    Recibe un RUT (ej: '76.123.456-K' o '15469746-2') y devuelve el número base entero.
    """
    try:
        rut_str = str(rut_raw).upper()
        # Quitamos puntos y guión
        rut_limpio = rut_str.replace(".", "").replace("-", "")
        # Quitamos el dígito verificador (el último caracter)
        cuerpo_rut = rut_limpio[:-1]
        
        # Convertimos a entero para comparar
        return int(cuerpo_rut)
    except:
        return 0 # Si falla, retornamos 0

def procesar_saludo(row):
    """
    Define el saludo basado en el RUT.
    RUT > 70.000.000 -> Empresa (Usa razón social completa).
    RUT < 70.000.000 -> Persona (Usa primer nombre).
    """
    rut_val = limpiar_rut(row.get('Rut', 0))
    nombre_completo = str(row.get('Nombre / Razón social', 'Colaborador')).strip()
    
    if rut_val > 70000000:
        # Es Empresa
        return nombre_completo.title()
    else:
        # Es Persona Natural
        partes = nombre_completo.split()
        if len(partes) > 0:
            return partes[0].capitalize()
        return "Colaborador"

def formatear_cuenta(cuenta_raw):
    """
    Maneja números que vienen como flotantes o notación científica (ej: 5.33E+15).
    Devuelve un string limpio.
    """
    try:
        # Si es un número (float o int), lo convertimos a string sin decimales .0
        if isinstance(cuenta_raw, (float, int)):
            return "{:.0f}".format(cuenta_raw)
        return str(cuenta_raw)
    except:
        return str(cuenta_raw)

def generar_aviso_tarjeta(cuenta_str):
    """
    Verifica longitud de la cuenta ya convertida a string.
    """
    # Limpiamos espacios por seguridad
    cuenta_clean = cuenta_str.replace(" ", "")
    if len(cuenta_clean) >= 15:
        return "\n⚠️ **Nota Importante:** Hemos notado que el número registrado tiene 15 o más dígitos. Te recordamos cordialmente verificar que estés ingresando tu **número de cuenta bancaria** y no el número que aparece impreso en tu tarjeta (plástico), ya que suelen ser diferentes.\n"
    return ""

def crear_texto_correo(row, agente, firma):
    nombre_saludo = procesar_saludo(row)
    motivo = row.get('Motivo del rechazo', 'Motivo no especificado')
    institucion = row.get('Institución', 'Banco no especificado')
    
    # Formatear la cuenta para evitar el "5.33e+15"
    cuenta_str = formatear_cuenta(row.get('Cuenta', 'N/A'))
    
    aviso_tarjeta = generar_aviso_tarjeta(cuenta_str)
    
    mensaje = f"""Hola {nombre_saludo},

Mi nombre es {agente} y seré el encargado de ayudarte con tu caso.

Junto con saludarte, te comento que tus pagos han sido rechazados por tu banco debido al siguiente motivo:
Motivo de rechazo: {motivo}

Cuenta registrada al momento del rechazo:
Institución: {institucion}
N° de cuenta: {cuenta_str}
{aviso_tarjeta}
Para poder continuar con los abonos pendientes, te pedimos por favor verificar si esta información es correcta o bien ingresar una nueva cuenta bancaria con los siguientes datos:

Nombre:
RUT:
Banco:
Tipo de cuenta (vista o corriente):
Número de cuenta:

👉 En caso de que ya hayas actualizado correctamente tu información bancaria, puedes ignorar este mensaje.

Te recordamos que los datos bancarios deben estar registrados a tu nombre. No es posible generar pagos a cuentas de terceros, salvo que se adjunte un certificado notarial que autorice el uso de dicha cuenta.

Quedamos atentos a tu respuesta para poder ayudarte a la brevedad.

Ante cualquier duda adicional, no dudes en volver a contactarnos o visitar nuestro Centro de Ayuda: https://help.cabify.com/hc/es

Un saludo cordial,

{agente}
{firma}"""
    return mensaje

# --- INTERFAZ PRINCIPAL ---

uploaded_file = st.file_uploader("Sube tu archivo (Excel o CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Detectar si es CSV o Excel por la extensión
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Normalizar nombres de columnas (eliminar espacios extra al inicio/final por seguridad)
        df.columns = df.columns.str.strip()
        
        # Verificar columnas críticas del archivo que enviaste
        cols_requeridas = ['Rut', 'Nombre / Razón social', 'Institución', 'Cuenta', 'email']
        
        # Filtrar solo si faltan columnas
        missing = [c for c in cols_requeridas if c not in df.columns]
        
        if missing:
            st.error(f"Faltan las siguientes columnas en tu archivo: {', '.join(missing)}")
            st.info("Asegúrate de que los encabezados sean: 'Rut', 'Nombre / Razón social', 'Institución', 'Cuenta', 'email'")
        else:
            st.success(f"Archivo cargado con {len(df)} registros. Mostrando vista para Zendesk:")
            
            # Iterar sobre cada fila para mostrar el bloque de copia
            for index, row in df.iterrows():
                email_usuario = row['email']
                if pd.isna(email_usuario):
                    email_usuario = "Correo no disponible en tabla"
                
                texto_final = crear_texto_correo(row, nombre_agente, pie_firma)
                
                # Diseño de "Tarjeta" para cada caso
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.subheader(f"Caso #{index + 1}")
                        st.info(f"📧 **Enviar a:**\n\n{email_usuario}")
                        
                        # Mostrar datos clave para referencia rápida del agente
                        st.text(f"RUT: {row['Rut']}")
                        cuenta_display = formatear_cuenta(row['Cuenta'])
                        st.caption(f"Cuenta: {cuenta_display}")
                        if len(cuenta_display) >= 15:
                            st.warning("⚠️ Detectado posible N° Tarjeta")
                    
                    with col2:
                        st.write("**Copiar el siguiente mensaje:**")
                        # st.code genera un bloque con botón de copiado automático
                        st.code(texto_final, language="markdown")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
