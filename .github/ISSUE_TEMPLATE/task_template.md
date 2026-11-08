---
name: Tarea de Fase Técnica
about: Registro de tarea para los colaboradores del equipo DSP
title: '[FASE-X]: <Nombre de la Tarea Técnica>'
labels: ['fase-tecnica', 'dsp']
assignees: ''
---

### Objetivo Técnico
<!-- ¿Qué función, demodulador, modulador o cálculo se va a desarrollar? -->

### Entradas Requeridas (Contratos)
<!-- ¿Qué tipo de dato de src/core/base.py recibe? (AudioSignal, DigitalStream, ModulatedSignal) -->

### Salidas Esperadas
<!-- ¿Qué entrega? (ModulatedSignal, DemodulatedResult, PerformanceMetrics, Gráficas PNG, Audio WAV) -->

### Fórmulas Matemáticas y Referencias
<!-- Ecuaciones teóricas aplicadas (AM, FM, ASK, FSK, sinc Whittaker-Shannon, etc.) -->

### Checklist de Definición de Terminado (DoD)
- [ ] Código modular en carpeta correspondiente (`src/modulation`, `src/demodulation`, `src/reconstruction`).
- [ ] Función de graficado temporal y frecuencial exportable a PNG.
- [ ] Función de reproducción de audio audible.
- [ ] Test unitario añadido en `tests/`.
- [ ] PR abierto hacia la rama `develop` siguiendo el template.
