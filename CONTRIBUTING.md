# Guía de Contribución y Flujo de Trabajo en GitHub

¡Bienvenidos al repositorio del **Proyecto Integral de Comunicaciones I (DSP)**!

Este documento establece las reglas de ingeniería, control de versiones y estándares de código para que los 4 colaboradores trabajen de forma armónica y coordinada mientras el líder técnico se ausenta.

---

## 1. Estrategia de Ramas (Git Workflow)

Trabajamos con una variante estricta y limpia de **GitHub Flow / Feature Branching**:

* `main`: **Rama de Producción**. Solo contiene código probado, verificado y aprobado. Nadie comitea directamente a `main`.
* `develop`: **Rama de Integración Continua**. Aquí convergen los Pull Requests aprobados de cada fase.
* `feature/<fase>-<descripcion>`: Ramas de trabajo individuales para cada colaborador.

### Nomenclatura de Ramas por Colaborador:
- **Colaborador 1 (Modulación)**: `feature/fase2-modulacion-analogica-digital`
- **Colaborador 2 (Demodulación)**: `feature/fase3-demodulacion-recuperacion`
- **Colaborador 3 (Reconstrucción y Métricas)**: `feature/fase4-reconstruccion-dac-metricas`
- **Colaborador 4 (Integración CLI y Driver GUI)**: `feature/fase5-cli-gui-engine`

---

## 2. Convención de Commits (Conventional Commits)

Cada commit debe ser atómico y describir con precisión el aporte:
- `feat:`: Añade una nueva funcionalidad (ej. `feat(modulation): implement FSK modulator with binary stream`).
- `fix:`: Corrige un error o bug (ej. `fix(quantization): correct mid-tread offset level rounding`).
- `test:`: Agrega o actualiza tests unitarios (ej. `test(demod): add coherent AM demodulation test case`).
- `docs:`: Cambios exclusivamente en documentación o diagramas (ej. `docs: update math equations in README`).
- `refactor:`: Modificación de código sin cambiar su comportamiento externo.

---

## 3. Protocolo para Abrir y Aprobar un Pull Request (PR)

1. **Crear la rama** a partir de la última versión de `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/faseX-mi-tarea
   ```
2. **Desarrollar y probar localmente**:
   - Todo código nuevo debe heredar de las clases base definidas en `src/core/base.py` (`BaseModulator`, `BaseDemodulator`, `BaseReconstructor`).
   - Ejecutar la suite de pruebas:
     ```bash
     python -m unittest discover tests
     ```
3. **Push y Pull Request**:
   - Subir la rama a GitHub: `git push -u origin feature/faseX-mi-tarea`.
   - Abrir el PR hacia la rama `develop`.
   - Completar el formulario del PR template.
   - Solicitar la revisión de al menos **un compañero de equipo**. Se requieren pruebas en verde (`OK`) para poder hacer merge.

---

## 4. Estándares de Código Python

- **PEP 8**: Nombres de variables y funciones en `snake_case`, clases en `PascalCase`.
- **Tipado estricto**: Usar anotaciones de tipo (`numpy.ndarray`, `AudioSignal`, `int`, `float`, etc.).
- **Docstrings**: Formato Google o Sphinx en cada función indicando `Args:` y `Returns:`.
- **Manejo de audios**: Todas las señales de audio internas deben permanecer normalizadas en `[-1.0, 1.0]` en `float32` para evitar *clipping* o saturación en conversiones DAC.
- **Gráficas**: Fondo oscuro legible, ejes rotulados con magnitudes físicas y unidades en corchetes (`[s]`, `[Hz]`, `[dB]`), leyendas claras y DPI de al menos 300 al exportar a `.png`.
