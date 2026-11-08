# Transceptor DSP de Voz: Cadena Completa de Comunicaciones

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Fase%201-Completada%20y%20Verificada-brightgreen.svg)]()
[![License](https://img.shields.io/badge/Curso-Comunicaciones%20I%20UTP-orange.svg)]()
[![Tests](https://img.shields.io/badge/Unit%20Tests-6%2F6%20Passed-success.svg)]()

Sistema integral en Python para el procesamiento de señales de audio (voz humana), análisis bajo el **Teorema de Nyquist-Shannon (NQS)**, digitalización PCM con resolución configurable en **[Byte / Bit]**, modulación analógica y digital pasabanda, demodulación de recuperación, reconstrucción analógica continua (DAC) y auditoría objetiva de fidelidad (MSE, SNR, PSNR, Pearson).

Diseñado con una arquitectura modular y desacoplada de servicios, lista para su posterior integración con interfaces gráficas de usuario (GUI).

---

## Estructura del Repositorio

```text
Proyecto_Comunicaciones_DSP/
│
├── .github/                               # Plantillas para GitHub
│   ├── ISSUE_TEMPLATE/
│   │   └── task_template.md               # Plantilla de asignación de tareas
│   └── pull_request_template.md           # Plantilla de Pull Request con checklist
│
├── audio_data/                            # Almacén de audios WAV, tramas .bin y figuras .png
│   ├── .gitkeep
│   ├── voz_original.wav                   # Audio original grabado o sintetizado
│   ├── trama_digital_8bits.bin            # Trama binaria cuantizada (1 Byte/muestra)
│   ├── trama_digital_8bits_metadata.json  # Metadatos del flujo digital
│   ├── 01_analisis_temporal_espectral.png # Gráfica tiempo y FFT
│   ├── 02_estudio_muestreo_nqs.png        # Gráfica Teorema de Nyquist-Shannon
│   └── 03_cuantizacion_8bits_ruido.png    # Gráfica de cuantización y ruido e[n]
│
├── docs/                                  # Documentación de ingeniería y planes
│   └── plan_fases_colaboracion.md         # Plan maestro por fases y matriz RACI
│
├── src/                                   # Paquete Python modular (Core DSP Engine)
│   ├── __init__.py
│   ├── core/                              # FASE 1: NÚCLEO IMPLEMENTADO Y VALIDADO
│   │   ├── __init__.py
│   │   ├── base.py                        # Dataclasses inmutables y contratos abstractos
│   │   ├── audio_io.py                    # Carga, guardado, grabación y reproducción
│   │   ├── analyzer.py                    # FFT, PSD, ancho de banda, f_max y Nyquist
│   │   └── quantization.py                # Muestreo NQS, cuantización Byte/Bit, SQNR
│   │
│   ├── modulation/                        # FASE 2: Asignada a Colaborador 1
│   │   ├── __init__.py
│   │   └── analog_digital_stubs.py        # Moduladores AM/FM y ASK/FSK/BPSK
│   │
│   ├── demodulation/                      # FASE 3: Asignada a Colaborador 2
│   │   ├── __init__.py
│   │   └── demod_stubs.py                 # Demoduladores coherentes, envolvente y LPF
│   │
│   └── reconstruction/                    # FASE 4: Asignada a Colaborador 3
│       ├── __init__.py
│       └── metrics_stubs.py               # Interpolación Sinc, ZOH, MSE y SNR
│
├── tests/                                 # Suite de Pruebas Unitarias Automatizadas
│   ├── __init__.py
│   └── test_fase1.py                      # Pruebas para Adquisición, FFT, Cuantización y NQS
│
├── fase1_demo.py                          # Script ejecutable de demostración y entrega Fase 1
├── requirements.txt                       # Dependencias mínimas (numpy, scipy, matplotlib)
├── .gitignore                             # Filtro de exclusión para Git
├── CONTRIBUTING.md                        # Protocolo de ramas, commits y Pull Requests
└── README.md                              # Documento principal de referencia
```

---

## Plan de Trabajo por Fases y Asignación del Equipo

| Fase | Título y Enfoque Técnico | Responsable | Estado |
| :---: | :--- | :---: | :---: |
| **Fase 1** | **Adquisición WAV, Análisis Temporal/FFT, Criterio NQS y Digitalización PCM [Byte/Bit]** | **Líder Técnico (Usuario)** | **COMPLETADA** |
| **Fase 2** | **Modulación Pasabanda (AM, FM, ASK, FSK, BPSK, QAM) y Escucha de Señal Modulada** | **Colaborador 1** | *Listo para iniciar* |
| **Fase 3** | **Demodulación, Detector Coherente / Envolvente y Recuperación Auditiva** | **Colaborador 2** | *Listo para iniciar* |
| **Fase 4** | **Reconstrucción DAC (Sinc / ZOH), Exportación de WAV y Métricas (MSE, SNR, Pearson)** | **Colaborador 3** | *Listo para iniciar* |
| **Fase 5** | **Orquestación CLI Integral, Pruebas End-to-End y Driver para Interfaz Gráfica (GUI)** | **Colaborador 4** | *Listo para iniciar* |

Para el detalle completo de responsabilidades, entradas/salidas de cada función y criterios de aceptación, consulta el documento técnico:  
[`docs/plan_fases_colaboracion.md`](docs/plan_fases_colaboracion.md)

---

## Puesta en Marcha Rápida (Quickstart)

### 1. Clonar el repositorio y preparar el entorno
```bash
git clone <URL_DEL_REPOSITORIO_GITHUB>
cd Proyecto_Comunicaciones_DSP

# Crear y activar entorno virtual (opcional pero recomendado)
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Suite de Pruebas Unitarias
Verifica que la base del sistema pase todos los tests automáticos:
```bash
python -m unittest discover tests
```
*Salida esperada:*
```text
Ran 6 tests in 0.065s
OK
```

### 3. Ejecutar la Fase 1 en Producción
Para correr la adquisición de voz, análisis espectral de Nyquist y cuantización PCM con exportación de archivos y gráficas:
```bash
# Cuantización estándar a 8 bits (1 Byte por muestra)
python fase1_demo.py --bits 8

# O especificando duración y reproducción de audio:
python fase1_demo.py --duration 3.5 --bits 8 --play

# O utilizando un archivo de audio WAV pregrabado:
python fase1_demo.py --audio mi_voz.wav --bits 4
```

---

## Fundamento Matemático Implementado en Fase 1

### 1. Espectro y Teorema de Nyquist-Shannon (NQS)
Para la señal continua de voz $s(t)$, se aplica la Transformada de Fourier con ventana Hann para evitar fugas espectrales (*spectral leakage*):
$$X(f) = \int_{-\infty}^{\infty} s(t) w(t) e^{-j 2\pi f t} dt$$

Se calcula el ancho de banda efectivo $f_{max}$ conteniendo el $99\%$ de la energía espectral acumulada:
$$E_{cum}(f_{max}) = \frac{\int_{0}^{f_{max}} |X(f)|^2 df}{\int_{0}^{f_s/2} |X(f)|^2 df} \ge 0.99$$

El teorema de Nyquist-Shannon exige:
$$f_s \ge 2 f_{max}$$

### 2. Cuantización Uniforme Lineal (Técnica [Byte / Bit])
Dada una resolución de $b$ bits por muestra ($L = 2^b$ niveles de cuantización en el rango $[V_{min}, V_{max}]$), el paso de cuantización es:
$$\Delta = \frac{V_{max} - V_{min}}{2^b - 1}$$

El índice discreto cuantizado $q[n]$ y la muestra reconstruida $x_q[n]$ corresponden a:
$$q[n] = \text{clip}\left(\left\lfloor \frac{x[n] - V_{min}}{\Delta} + 0.5 \right\rfloor, 0, 2^b - 1\right)$$
$$x_q[n] = V_{min} + q[n] \cdot \Delta$$

El error de cuantización $e[n] = x[n] - x_q[n]$ está acotado estrictamente en $[-\Delta/2, +\Delta/2]$, con una relación señal a ruido de cuantización teórica (Bennett):
$$\text{SQNR}_{teorico} \approx 6.02 \cdot b + 1.76 \text{ dB}$$

---

## Contratos de Integración para los Colaboradores

Cada colaborador debe importar las clases base de `src/core/base.py`:
```python
from src.core.base import AudioSignal, DigitalStream, ModulatedSignal, BaseModulator, BaseDemodulator, BaseReconstructor
```

* **Colaborador 1:** Hereda de `BaseModulator` y genera instancias de `ModulatedSignal`.
* **Colaborador 2:** Hereda de `BaseDemodulator` y genera instancias de `DemodulatedResult`.
* **Colaborador 3:** Hereda de `BaseReconstructor` y produce `PerformanceMetrics` (MSE, SNR, Pearson).
* **Colaborador 4:** Integra el pipeline completo en `pipeline_cli.py`.

---

## Flujo de Trabajo en Git

Para mantener la calidad del proyecto:
1. Nunca trabajar en la rama `main`.
2. Crear ramas de características desde `develop`: `git checkout -b feature/faseX-mi-tarea`.
3. Seguir la convención de commits: `feat:`, `fix:`, `test:`, `docs:`.
4. Abrir un Pull Request hacia `develop` utilizando el template interactivo.
5. Para más detalles, consultar [`CONTRIBUTING.md`](CONTRIBUTING.md).
