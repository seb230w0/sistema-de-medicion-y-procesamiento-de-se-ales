from machine import ADC, Pin, Timer, PWM
import time

# CONFIGURACIÓN DE HARDWARE 
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB) 
led_adq = Pin(2, Pin.OUT)
# Configuramos el buzzer en el pin 13 (puedes cambiarlo)
buzzer = PWM(Pin(13))
buzzer.duty(0) # Iniciamos en silencio

# VARIABLES Y BUFFERS 
raw_val = 0
buffer_mediana = []
history_prom = []
last_exp = 0
umbral_alerta = 2500 # Valor para activar el buzzer (ajustable de 0-4095)

# Filtros por consola
usa_mediana = False
usa_promedio = False
usa_exponencial = False

# FILTROS 
def filtro_mediana(dato):
    buffer_mediana.append(dato)
    if len(buffer_mediana) > 5: buffer_mediana.pop(0)
    return sorted(buffer_mediana)[len(buffer_mediana)//2]

def filtro_promedio(dato):
    history_prom.append(dato)
    if len(history_prom) > 5: history_prom.pop(0)
    return sum(history_prom) / len(history_prom)

def filtro_exponencial(dato, alpha=0.2):
    global last_exp
    last_exp = (alpha * dato) + (1 - alpha) * last_exp
    return last_exp

#  TIMER HARDWARE 
def cb_muestreo(t):
    global raw_val
    led_adq.value(1)
    raw_val = adc.read()
    led_adq.value(0)

# MENÚ DE CONFIGURACIÓN 
print("--- SISTEMA DE MEDICIÓN CON ALERTAS ---")
freq = int(input("Frecuencia de muestreo (Hz): "))

print("\n¿Habilitar filtros en cascada? (si/no)")
usa_mediana = input("1. Mediana: ").lower() == "si"
usa_promedio = input("2. Promedio: ").lower() == "si"
usa_exponencial = input("3. Exponencial: ").lower() == "si"

tim = Timer(0)
tim.init(freq=freq, mode=Timer.PERIODIC, callback=cb_muestreo)

# Encabezado para archivo .txt 
with open("datos_reflejos.txt", "w") as f:
    f.write("Tiempo_ms,Crudo,Filtrado\n")

print("\nEjecutando... Crudo,Filtrado")

# BUCLE PRINCIPAL 
try:
    while True:
        # Cascada de procesamiento [cite: 34, 35]
        procesado = raw_val
        if usa_mediana: procesado = filtro_mediana(procesado)
        if usa_promedio: procesado = filtro_promedio(procesado)
        if usa_exponencial: procesado = filtro_exponencial(procesado)
            
        # Salida Serial Plotter [cite: 22, 36]
        print(f"{raw_val},{procesado}")
        
        # Lógica de Buzzer y Alertas 
        if procesado > umbral_alerta:
            buzzer.freq(1000) # Tono de 1kHz
            buzzer.duty(512)  # 50% volumen
            led_adq.value(1)  # Refuerzo visual
        else:
            buzzer.duty(0)    # Silencio
            
        # Guardado en memoria interna 
        with open("datos_reflejos.txt", "a") as f:
            f.write(f"{time.ticks_ms()},{raw_val},{procesado}\n")
            
        time.sleep(0.1) 

except KeyboardInterrupt:
    tim.deinit()
    buzzer.duty(0)
    print("\nSistema apagado.")k