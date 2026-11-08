# Plan de Elaboración por Fases y Arquitectura de Colaboración

**Universidad Tecnológica de Pereira (UTP)**  
**Facultad de Ingenierías - Programa de Ingeniería Eléctrica / Electrónica / Sistemas**  
**Asignatura:** Comunicaciones I  
**Equipo:** 5 Integrantes (1 Líder de Arquitectura + 4 Colaboradores de Especialidad)

---

## 1. Visión y Alcance Técnico

El proyecto consiste en el diseño, implementación y validación experimental de una **cadena completa de transmisión y recepción de señales de audio (DSP Transceiver)** en Python. El sistema abarca desde la captura acústica de voz, caracterización de espectro bajo el Teorema de Nyquist-Shannon (NQS), digitalización PCM (técnica de resolución Byte/Bit), hasta esquemas de modulación analógica y digital pasabanda, demodulación, filtrado de recuperación, reconstrucción analógica continua (DAC) y auditoría cuantitativa de fidelidad (MSE, SNR, PSNR, Pearson).

La arquitectura ha sido diseñada con **estricto desacoplamiento de capas (Decoupled Service Layer)** para permitir que los módulos matemáticos de Python funcionen como un motor independiente que posteriormente se conectará a la interfaz gráfica (GUI) sin modificar una sola línea de lógica DSP.

---

## 2. Matriz de Roles y Asignación de Responsabilidades (RACI)

| Rol | Responsable | Fase Asignada | Módulos Clave | Entregables Principales |
| :--- | :--- | :--- | :--- | :--- |
| **Líder Técnico / Arquitecto** | *Tú (Usuario)* | **FASE 1 (Completada)** | `src/core/` (`base.py`, `audio_io.py`, `analyzer.py`, `quantization.py`), `tests/`, `fase1_demo.py` | Contratos abstractos, I/O audio, espectro FFT/NQS, cuantizador PCM Bit/Byte, exportación serializada y suite de pruebas. |
| **Colaborador 1** | *Especialista en Modulación* | **FASE 2** | `src/modulation/` (`analog_digital_stubs.py`) | Moduladores AM/FM (analógicos) y ASK/FSK/BPSK (digitales sobre bitstream), plots espectrales de portadora y síntesis audible de modulación. |
| **Colaborador 2** | *Especialista en Demodulación* | **FASE 3** | `src/demodulation/` (`demod_stubs.py`) | Demoduladores coherentes, detector de envolvente (Hilbert), filtros paso-bajo Butterworth de recuperación, plots y reproductor de audio recuperado. |
| **Colaborador 3** | *Especialista en Reconstrucción y Métricas* | **FASE 4** | `src/reconstruction/` (`metrics_stubs.py`) | Reconstructor Whittaker-Shannon (Sinc) y ZOH con filtro analógico, generador de WAV final, evaluador de fidelidad (MSE, SNR, PSNR, Correlación) y plots comparativos. |
| **Colaborador 4** | *Especialista en Integración CLI y Driver GUI* | **FASE 5** | `pipeline_cli.py`, `src/gui_bridge/` | Orquestador integral por línea de comandos (CLI con flags e interactivo), adaptadores para futura GUI (Tkinter / PyQt / Web), CI y revisión de código. |

*RACI: R = Responsable de ejecución, A = Aprobador (Líder), C = Consultado, I = Informado.*

---

## 3. Desglose Detallado de Fases y Especificaciones Técnicas

```
       [ Micrófono / Archivo WAV ]
                   │
                   ▼
       ┌────────────────────────┐
       │ FASE 1: Adquisición &  │  ◄── IMPLEMENTADA Y VALIDADA
       │ Análisis NQS & PCM     │      (Núcleo base, AudioSignal, DigitalStream)
       └────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐     ┌───────────────┐
│ Rama Analógica│     │ Rama Digital  │
│ m(t)          │     │ Bitstream     │
└───────┬───────┘     └───────┬───────┘
        │                     │
        ▼                     ▼
┌─────────────────────────────────────┐
│ FASE 2: Modulación (Colaborador 1)  │  ◄── AM / FM  ó  ASK / FSK / BPSK
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ FASE 3: Demodulación (Colab. 2)     │  ◄── Coherente / Envolvente + Filtro LPF
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ FASE 4: Reconstrucción & Métricas   │  ◄── Sinc / ZOH + MSE, SNR dB, WAV final
│         (Colaborador 3)             │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ FASE 5: Integración CLI & GUI Driver│  ◄── Pipeline end-to-end + desacople UI
│         (Colaborador 4)             │
└─────────────────────────────────────┘
```

---

### FASE 1: Adquisición, Análisis y Digitalización PCM (Puntos 1, 2 y 3)
* **Estado:** **100% PRODUCCIÓN - FINALIZADA Y PROBADA.**
* **Archivos Desarrollados:**
  - `src/core/base.py`: Dataclasses inmutables (`AudioSignal`, `DigitalStream`, `ModulatedSignal`, `DemodulatedResult`, `PerformanceMetrics`) e interfaces abstractas.
  - `src/core/audio_io.py`: Carga y guardado de WAV PCM, grabación de audio con fallback a sintetizador formántico vocal de prueba, y reproductor Windows `winsound` nativo.
  - `src/core/analyzer.py`: Medición de pico, RMS, factor de cresta, rango dinámico; cálculo de FFT unilateral ventaneada (Hann), cálculo automático de $f_{max}$ al 99% de energía y verificación del criterio de Nyquist-Shannon.
  - `src/core/quantization.py`: Muestreo por diezmado para comparar sobremuestreo vs submuestreo con aliasing; cuantización lineal uniforme para $b \in [1, 16]$ bits (resolución por Byte y Bit); cálculo empírico y teórico de SQNR ($6.02b + 1.76\text{ dB}$); serialización a archivo binario `.bin` y metadatos `.json`.
  - `tests/test_fase1.py`: Suite de 6 tests unitarios automatizados (`unittest`).
  - `fase1_demo.py`: Script interactivo de validación y generación de artefactos visuales.

---

### FASE 2: Modulación Analógica y Digital (Punto 4 del Proyecto)
* **Responsable:** **Colaborador 1**
* **Rama de Trabajo:** `feature/fase2-modulacion-analogica-digital`
* **Entradas:**
  - `AudioSignal` (desde Fase 1) para modulaciones analógicas (AM, FM).
  - `DigitalStream` (desde Fase 1) para modulaciones digitales (ASK, FSK, BPSK, QAM).
* **Tareas Específicas a Desarrollar:**
  1. Completar la clase `AMModulator` en `src/modulation/analog_digital_stubs.py`:
     $$s_{AM}(t) = [A_c + m(t)] \cos(2\pi f_c t)$$
     Verificar que el índice de modulación $\mu = \frac{\max|m(t)|}{A_c} \le 1.0$ para evitar sobremodulación.
  2. Implementar modulación de frecuencia (FM) en banda angosta o ancha:
     $$s_{FM}(t) = A_c \cos\left(2\pi f_c t + 2\pi k_f \int_0^t m(\tau) d\tau\right)$$
  3. Implementar modulador digital (e.g. ASK o FSK binario):
     - Para bit = 1: emitir $A_1 \cos(2\pi f_1 t)$
     - Para bit = 0: emitir $A_0 \cos(2\pi f_0 t)$
  4. Graficar la señal modulada con zoom temporal (mostrando oscilaciones de la portadora) y espectro FFT que evidencia la traslación en frecuencia y los lóbulos laterales.
  5. Permitir la audición de la señal modulada mediante `play_audio` (usando una frecuencia de portadora en el espectro audible, e.g., $f_c = 2000 - 4000\text{ Hz}$).
* **Definición de Terminado (DoD):**
  - Módulo con clases herederas de `BaseModulator`.
  - Tests unitarios en `tests/test_modulation.py`.
  - PR abierto contra `develop`.

---

### FASE 3: Demodulación y Procesamiento de Recepción (Punto 5 del Proyecto)
* **Responsable:** **Colaborador 2**
* **Rama de Trabajo:** `feature/fase3-demodulacion-recuperacion`
* **Entradas:** `ModulatedSignal` generado por el Colaborador 1 en la Fase 2.
* **Tareas Específicas a Desarrollar:**
  1. Completar la clase `AMDemodulator` en `src/demodulation/demod_stubs.py`:
     - **Opción A (Coherente):** Mezclador local $s_{mod}(t) \cdot \cos(2\pi f_c t)$ seguido de filtro paso-bajo Butterworth (orden 4 a 6) con frecuencia de corte en $f_{cutoff} \approx f_{audio\_max}$.
     - **Opción B (Detector de Envolvente):** Transformada de Hilbert de la señal analítica $\hat{s}(t)$, cálculo de la envolvente instantánea $A(t) = |s(t) + j\hat{s}(t)|$, y eliminación del nivel DC de la portadora.
  2. Implementar demodulador digital si se utiliza ASK/FSK:
     - Correlador síncrono o filtro acoplado (Matched Filter) con muestreo en los instantes de decisión $T_b$ y comparador de umbral para recuperar el bitstream $\hat{b}[k]$.
  3. Generar gráfica comparativa temporal entre la señal de audio original y la señal demodulada.
  4. Reproducir la señal demodulada en el altavoz para contrastar la inteligibilidad de la voz recuperada.
* **Definición de Terminado (DoD):**
  - Recuperación de la señal con correlación $r > 0.85$ respecto al audio base.
  - Tests unitarios en `tests/test_demodulation.py`.
  - PR abierto contra `develop`.

---

### FASE 4: Reconstrucción DAC y Métricas de Rendimiento (Punto 6 del Proyecto)
* **Responsable:** **Colaborador 3**
* **Rama de Trabajo:** `feature/fase4-reconstruccion-dac-metricas`
* **Entradas:** `DigitalStream` (Fase 1) o `DemodulatedResult` (Fase 3).
* **Tareas Específicas a Desarrollar:**
  1. Completar la clase `AudioReconstructor` en `src/reconstruction/metrics_stubs.py`:
     - Implementar interpolación sinc ideal (Whittaker-Shannon):
       $$x_r(t) = \sum_{n=-\infty}^{\infty} x[n] \cdot \text{sinc}\left(\frac{t - n T_s}{T_s}\right)$$
     - Implementar retenedor de orden cero (ZOH) con filtro pasobajo analógico antillave de reconstrucción.
  2. Generar el archivo WAV de la señal de voz reconstruida (`audio_reconstruido.wav`) usando `save_wav`.
  3. Ejecutar la función de reproducción con `play_audio` para verificación auditiva.
  4. Calcular las métricas objetivas de fidelidad:
     - Error Cuadrático Medio: $\text{MSE} = \frac{1}{N} \sum_{n=1}^N (x[n] - \hat{x}[n])^2$
     - Relación Señal a Ruido: $\text{SNR} = 10 \log_{10}\left(\frac{\sum x[n]^2}{\sum (x[n] - \hat{x}[n])^2}\right)\text{ dB}$
     - Peak SNR: $\text{PSNR} = 10 \log_{10}\left(\frac{1.0}{\text{MSE}}\right)\text{ dB}$
     - Coeficiente de correlación lineal de Pearson $r \in [-1, 1]$.
  5. Graficar la superposición temporal y espectral (Original vs Reconstruida + Curva de Error).
* **Definición de Terminado (DoD):**
  - Generación del archivo WAV reconstruido.
  - Cuadro cuantitativo de métricas (MSE, SNR, PSNR).
  - Tests unitarios en `tests/test_reconstruction.py`.
  - PR abierto contra `develop`.

---

### FASE 5: Integración CLI, Driver para GUI y Consolidación Final
* **Responsable:** **Colaborador 4** (en coordinación con el equipo)
* **Rama de Trabajo:** `feature/fase5-cli-gui-engine`
* **Tareas Específicas a Desarrollar:**
  1. Crear el script orquestador maestro `pipeline_cli.py`:
     - Menú interactivo o banderas de consola que permitan correr el flujo de extremo a extremo:
       `Grabación -> Análisis NQS -> Cuantización -> Modulación -> Demodulación -> Reconstrucción -> Reporte`.
  2. Diseñar la capa de abstracción `src/gui_bridge/controller.py`:
     - Métodos de alto nivel que emitan señales o callbacks de progreso.
     - Esta capa servirá para alimentar sin fricción la futura Interfaz Gráfica (Tkinter, PyQt6 o Web).
  3. Revisión de calidad de código (Anti-slop check):
     - Validar que no existan rutas absolutas en duro (hardcoded paths).
     - Comprobar compatibilidad multiplataforma (Windows/Linux/macOS).
     - Fusionar la rama `develop` hacia `main` una vez todos los tests estén en verde.
