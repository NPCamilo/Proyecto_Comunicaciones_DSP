"""
Generador del Documento PDF: Plan de Trabajo Técnico para Colaboradores
Proyecto DSP Comunicaciones I - UTP
Equipo: Camilo, Ángel, Mariano, Luis
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para calcular dinámicamente el número total de páginas."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (en páginas > 1)
        if self._pageNumber > 1:
            self.drawString(40, letter[1] - 30, "UTP - Comunicaciones I | Plan de Trabajo DSP - Camilo, Ángel, Mariano, Luis")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(40, letter[1] - 34, letter[0] - 40, letter[1] - 34)

        # Footer (en todas las páginas)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 42, letter[0] - 40, 42)
        
        footer_text = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(letter[0] - 40, 30, footer_text)
        self.drawString(40, 30, "Proyecto Integral DSP: Adquisición, Modulación, Demodulación y Reconstrucción")
        self.restoreState()


def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=38,
        rightMargin=38,
        topMargin=42,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Definición de Estilos Tipográficos
    primary_color = colors.HexColor("#0F172A")    # Slate 900
    brand_blue = colors.HexColor("#1D4ED8")       # Blue 700
    dark_text = colors.HexColor("#1E293B")        # Slate 800
    muted_text = colors.HexColor("#475569")       # Slate 600

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=brand_blue,
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=muted_text
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=6
    )

    card_title = ParagraphStyle(
        'CardTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=0,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=dark_text
    )

    bold_body = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=dark_text
    )

    code_style = ParagraphStyle(
        'CodeText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=dark_text
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=primary_color
    )

    story = []

    # =========================================================================
    # PÁGINA 1: ENCABEZADO, ESTADO ACTUAL Y MATRIZ GENERAL
    # =========================================================================
    
    # Encabezado Institucional
    story.append(Paragraph("UNIVERSIDAD TECNOLÓGICA DE PEREIRA (UTP)", ParagraphStyle(
        'UnivHeader', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor("#64748B"), spaceAfter=2
    )))
    story.append(Paragraph("FACULTAD DE INGENIERÍAS | COMUNICACIONES I - SEMESTRE 6", meta_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("PLAN DE TRABAJO TÉCNICO Y ASIGNACIÓN DE FASES", title_style))
    story.append(Paragraph("Cadena Transceptora de Voz DSP: Adquisición, Modulación, Demodulación y Reconstrucción", subtitle_style))
    
    # Banner de Estado Fase 1
    banner_data = [[
        Paragraph(
            "<b>ESTADO DE ENTREGA:</b> <b>FASE 1 COMPLETADA Y VALIDADA</b> (Por Camilo).<br/>"
            "El núcleo de procesamiento en Python (I/O WAV, análisis de Fourier con criterio Nyquist-Shannon y digitalización "
            "PCM Byte/Bit) cuenta con suite de tests al 100% (6/6 aprobados). Las interfaces y contratos de integración "
            "están listos en el repositorio para que Ángel, Mariano y Luis continúen sin dependencias bloqueantes.",
            ParagraphStyle('BannerText', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor("#065F46"))
        )
    ]]
    banner_table = Table(banner_data, colWidths=[letter[0] - 76])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#10B981")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # Matriz General de Asignación
    story.append(Paragraph("1. Matriz General de Responsabilidades del Equipo", section_heading))

    team_table_data = [
        [
            Paragraph("Integrante", table_header_style),
            Paragraph("Rol en el Proyecto", table_header_style),
            Paragraph("Fase y Rama Git", table_header_style),
            Paragraph("Puntos Clave", table_header_style),
            Paragraph("Estado", table_header_style)
        ],
        [
            Paragraph("<b>Camilo</b><br/>(Líder Técnico)", table_cell_bold),
            Paragraph("Arquitectura DSP, Contratos Base e I/O de Audio", table_cell_style),
            Paragraph("<b>Fase 1</b><br/><code>develop / main</code>", table_cell_style),
            Paragraph("Puntos 1, 2 y 3 (Grabación, Análisis NQS y PCM)", table_cell_style),
            Paragraph("<font color='#059669'><b>COMPLETADA</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Ángel</b>", table_cell_bold),
            Paragraph("Especialista en Modulación Analógica y Digital", table_cell_style),
            Paragraph("<b>Fase 2</b><br/><code>feature/fase2-modulacion</code>", table_cell_style),
            Paragraph("Punto 4 (AM / FM y ASK / FSK, audio de portadora)", table_cell_style),
            Paragraph("<font color='#2563EB'><b>Asignada</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Mariano</b>", table_cell_bold),
            Paragraph("Especialista en Demodulación y Procesamiento Receptor", table_cell_style),
            Paragraph("<b>Fase 3</b><br/><code>feature/fase3-demodulacion</code>", table_cell_style),
            Paragraph("Punto 5 (Coherente / Envolvente + Filtro LPF)", table_cell_style),
            Paragraph("<font color='#2563EB'><b>Asignada</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Luis</b>", table_cell_bold),
            Paragraph("Especialista en Reconstrucción DAC, Métricas y Pipeline", table_cell_style),
            Paragraph("<b>Fases 4 y 5</b><br/><code>feature/fase4-reconstruccion</code>", table_cell_style),
            Paragraph("Punto 6 (Sinc/ZOH, MSE, SNR, Pearson, CLI/GUI)", table_cell_style),
            Paragraph("<font color='#2563EB'><b>Asignada</b></font>", table_cell_style)
        ]
    ]

    team_table = Table(team_table_data, colWidths=[90, 135, 140, 115, 60])
    team_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(team_table)
    story.append(Spacer(1, 12))

    # Resumen Arquitectura y Flujo de Datos
    story.append(Paragraph("2. Flujo de Datos y Contratos de Integración", section_heading))
    story.append(Paragraph(
        "El proyecto opera bajo el principio de <b>servicios desacoplados</b>. Cada etapa consume objetos tipados "
        "definidos en <code>src/core/base.py</code> y genera el siguiente eslabón de la cadena:",
        body_style
    ))
    story.append(Spacer(1, 4))

    flow_box = [
        [Paragraph(
            "<b>Cadena de Transmisión:</b> "
            "Audio WAV original <b>[AudioSignal]</b> "
            "&rarr; Análisis FFT & Nyquist "
            "&rarr; Cuantizador PCM <b>[DigitalStream]</b> "
            "&rarr; Modulador Pasabanda <b>[ModulatedSignal]</b> "
            "&rarr; Demodulador & Filtro <b>[DemodulatedResult]</b> "
            "&rarr; Reconstructor DAC & Métricas <b>[PerformanceMetrics]</b> "
            "&rarr; <code>audio_reconstruido.wav</code>",
            ParagraphStyle('FlowText', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor("#1E3A8A"))
        )]
    ]
    flow_table = Table(flow_box, colWidths=[letter[0] - 76])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#3B82F6")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # FICHA INDIVIDUAL 1: CAMILO
    # =========================================================================
    camilo_box = [
        [Paragraph("<b>CAMILO</b> | Líder Técnico & Arquitecto DSP (Fase 1 - Realizada)", card_title)],
        [Paragraph(
            "<b>Módulos entregados:</b> <code>src/core/base.py</code>, <code>audio_io.py</code>, <code>analyzer.py</code>, "
            "<code>quantization.py</code>, <code>fase1_demo.py</code>, <code>tests/test_fase1.py</code>.<br/>"
            "<b>Logros técnicos consolidados:</b><br/>"
            "&bull; <i>Punto 1 (Grabación):</i> Soporte de micrófono en vivo y generador sintético de formantes vocales de respaldo.<br/>"
            "&bull; <i>Punto 2 (Análisis):</i> FFT con ventana Hann, determinación analítica de f_max (99% energía) y validación NQS.<br/>"
            "&bull; <i>Punto 3 (PCM Byte/Bit):</i> Cuantizador lineal uniforme (1 a 16 bits), cálculo empírico de SQNR vs teórico (6.02b + 1.76 dB), "
            "serialización de trama a <code>.bin</code> y metadatos en <code>.json</code>.<br/>"
            "<b>Rol mientras se ausenta:</b> Supervisión de PRs en GitHub y soporte sobre contratos de interfaz.",
            body_style
        )]
    ]
    t_camilo = Table(camilo_box, colWidths=[letter[0] - 76])
    t_camilo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#059669")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_camilo)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: FICHAS TÉCNICAS DE ÁNGEL Y MARIANO
    # =========================================================================
    story.append(Paragraph("3. Fichas Técnicas Individuales de Trabajo", section_heading))
    story.append(Spacer(1, 4))

    # FICHA 2: ÁNGEL
    angel_box = [
        [Paragraph("<b>ÁNGEL</b> | Especialista en Modulación Analógica y Digital (Fase 2)", card_title)],
        [Paragraph(
            "<b>Rama Git:</b> <code>feature/fase2-modulacion-analogica-digital</code> &nbsp;|&nbsp; "
            "<b>Archivos:</b> <code>src/modulation/analog_digital_stubs.py</code><br/>"
            "<b>Entradas del sistema:</b> <code>AudioSignal</code> (para modulación analógica) y <code>DigitalStream</code> (para digital).<br/>"
            "<b>Tareas Técnicas a Desarrollar (Punto 4 del Proyecto):</b><br/>"
            "1. <b>Modulación Analógica (AM / FM):</b><br/>"
            "   &bull; Implementar <code>AMModulator(BaseModulator)</code> con portadora fc audible (ej. 2500 a 3500 Hz):<br/>"
            "     &nbsp;&nbsp;&nbsp;&nbsp;s_AM(t) = [Ac + m(t)] &middot; cos(2&pi; fc t), con índice &mu; = max|m(t)| / Ac &le; 1.0.<br/>"
            "   &bull; (Opcional recomendado) Implementar modulación FM en banda base: s_FM(t) = Ac &middot; cos(2&pi; fc t + &beta; sin(2&pi; fm t)).<br/>"
            "2. <b>Modulación Digital (ASK / FSK / BPSK):</b><br/>"
            "   &bull; Implementar <code>DigitalShiftKeyingModulator</code> operando sobre el array de bits de <code>DigitalStream</code>.<br/>"
            "   &bull; Mapear símbolos a formas de onda pasabanda a fc con N muestras por símbolo.<br/>"
            "3. <b>Visualización y Audio:</b><br/>"
            "   &bull; Crear gráfica de 2 paneles: zoom temporal (10 ms mostrando ciclos de fc) y densidad espectral FFT.<br/>"
            "   &bull; Implementar función de escucha que normalice la señal modulada y la reproduzca mediante <code>play_audio()</code>.<br/>"
            "<b>Criterios de Aceptación (DoD):</b><br/>"
            "&bull; Retornar instancia válida de <code>ModulatedSignal</code>.<br/>"
            "&bull; Incluir test unitario en <code>tests/test_modulation.py</code> con ejecución limpia.<br/>"
            "&bull; Pull Request abierto hacia la rama <code>develop</code>.",
            body_style
        )]
    ]
    t_angel = Table(angel_box, colWidths=[letter[0] - 76])
    t_angel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#2563EB")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_angel)
    story.append(Spacer(1, 10))

    # FICHA 3: MARIANO
    mariano_box = [
        [Paragraph("<b>MARIANO</b> | Especialista en Demodulación y Procesamiento Receptor (Fase 3)", card_title)],
        [Paragraph(
            "<b>Rama Git:</b> <code>feature/fase3-demodulacion-recuperacion</code> &nbsp;|&nbsp; "
            "<b>Archivos:</b> <code>src/demodulation/demod_stubs.py</code><br/>"
            "<b>Entradas del sistema:</b> <code>ModulatedSignal</code> generado por Ángel en la Fase 2.<br/>"
            "<b>Tareas Técnicas a Desarrollar (Punto 5 del Proyecto):</b><br/>"
            "1. <b>Demodulación Analógica (AM):</b><br/>"
            "   &bull; Implementar <code>AMDemodulator(BaseDemodulator)</code> con dos modos seleccionables:<br/>"
            "     &nbsp;&nbsp;&bull; <i>Modo Coherente / Síncrono:</i> Multiplicación por oscilador local cos(2&pi; fc t) seguida de un "
            "filtro Butterworth paso-bajo orden 4 a 6 (fc_corte &asymp; f_max_audio &asymp; 3.5 kHz) implementado con <code>scipy.signal.butter</code>.<br/>"
            "     &nbsp;&nbsp;&bull; <i>Detector de Envolvente:</i> Magnitud de la señal analítica mediante Transformada de Hilbert "
            "(<code>scipy.signal.hilbert</code>), eliminando la componente DC de portadora.<br/>"
            "2. <b>Demodulación Digital (para ASK / FSK):</b><br/>"
            "   &bull; Implementar integración/correlación por período de símbolo y decisión con comparador de umbral para "
            "recuperar la secuencia de bits estimada <code>detected_bits</code>.<br/>"
            "3. <b>Visualización y Verificación Auditiva:</b><br/>"
            "   &bull; Graficar comparación temporal superpuesta entre el audio original y el audio demodulado recuperado.<br/>"
            "   &bull; Permitir reproducir el audio demodulado con <code>play_audio()</code> para contrastar inteligibilidad perceptual.<br/>"
            "<b>Criterios de Aceptación (DoD):</b><br/>"
            "&bull; Retornar <code>DemodulatedResult</code> conteniendo <code>recovered_audio: AudioSignal</code>.<br/>"
            "&bull; Correlación de Pearson entre original y demodulado mayor a 0.85 en canal limpio.<br/>"
            "&bull; Test unitario en <code>tests/test_demodulation.py</code> y Pull Request a <code>develop</code>.",
            body_style
        )]
    ]
    t_mariano = Table(mariano_box, colWidths=[letter[0] - 76])
    t_mariano.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#7C3AED")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_mariano)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: FICHA DE LUIS, PROTOCOLO GIT Y GUÍA RÁPIDA
    # =========================================================================

    # FICHA 4: LUIS
    luis_box = [
        [Paragraph("<b>LUIS</b> | Especialista en Reconstrucción DAC, Métricas e Integración (Fases 4 y 5)", card_title)],
        [Paragraph(
            "<b>Ramas Git:</b> <code>feature/fase4-reconstruccion-dac-metricas</code> y <code>feature/fase5-cli-gui-engine</code><br/>"
            "<b>Archivos:</b> <code>src/reconstruction/metrics_stubs.py</code> y <code>pipeline_cli.py</code><br/>"
            "<b>Entradas del sistema:</b> <code>DigitalStream</code> (Fase 1) o <code>DemodulatedResult</code> (Fase 3).<br/>"
            "<b>Tareas Técnicas a Desarrollar (Punto 6 del Proyecto e Integración):</b><br/>"
            "1. <b>Algoritmos de Reconstrucción DAC:</b><br/>"
            "   &bull; Implementar <code>AudioReconstructor(BaseReconstructor)</code> con:<br/>"
            "     &nbsp;&nbsp;&bull; <i>Interpolación Sinc (Whittaker-Shannon):</i> xr(t) = &sum; x[n] &middot; sinc((t - n&middot;Ts) / Ts).<br/>"
            "     &nbsp;&nbsp;&bull; <i>Retenedor de Orden Cero (ZOH):</i> seguido de filtro analógico Butterworth suavizador antillave.<br/>"
            "   &bull; Exportar a archivo WAV estandarizado (<code>audio_data/audio_reconstruido.wav</code>) mediante <code>save_wav()</code>.<br/>"
            "   &bull; Reproducir el audio reconstruido con <code>play_audio()</code>.<br/>"
            "2. <b>Auditoría Cuantitativa de Fidelidad (Métricas):</b><br/>"
            "   &bull; Implementar cálculo de: <b>MSE</b> (Error Cuadrático Medio), <b>SNR en dB</b>, <b>PSNR</b> y <b>Correlación de Pearson (r)</b>.<br/>"
            "   &bull; Generar gráfica comparativa doble: superposición temporal con curva de error e histograma de residuos, "
            "y superposición de espectros FFT (Original vs Reconstruido).<br/>"
            "3. <b>Integración CLI y Preparación de Driver para GUI (Fase 5):</b><br/>"
            "   &bull; Crear script maestro <code>pipeline_cli.py</code> que encadene: Grabar/Cargar &rarr; NQS/PCM &rarr; Modular &rarr; Demodular &rarr; Reconstruir.<br/>"
            "   &bull; Dejar funciones controladoras limpias sin prints directos, listas para conectar los eventos de la futura interfaz gráfica.<br/>"
            "<b>Criterios de Aceptación (DoD):</b><br/>"
            "&bull; Retornar <code>PerformanceMetrics</code> completo.<br/>"
            "&bull; Test unitario en <code>tests/test_reconstruction.py</code> y PR hacia <code>develop</code>.",
            body_style
        )]
    ]
    t_luis = Table(luis_box, colWidths=[letter[0] - 76])
    t_luis.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#D97706")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_luis)
    story.append(Spacer(1, 10))

    # PROTOCOLO GIT PARA COLABORADORES
    story.append(Paragraph("4. Protocolo de Trabajo en GitHub para el Equipo", section_heading))
    story.append(Paragraph(
        "Para garantizar un desarrollo sin conflictos, cada colaborador debe seguir este flujo riguroso:",
        body_style
    ))
    story.append(Spacer(1, 4))

    git_steps = [
        [Paragraph(
            "<b>1. Clonar y cambiar a la rama asignada:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>git checkout develop</code><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>git pull origin develop</code><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>git checkout feature/faseX-mi-tarea</code><br/>"
            "<b>2. Desarrollar e importar clases base:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>from src.core.base import AudioSignal, DigitalStream, ModulatedSignal, ...</code><br/>"
            "<b>3. Validar con la suite de pruebas unitarias:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>python -m unittest discover tests</code>  <i>(debe finalizar en OK)</i><br/>"
            "<b>4. Comitear siguiendo Conventional Commits:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>git commit -m 'feat(mod): implement AM modulator with modulation index check'</code><br/>"
            "<b>5. Subir rama y abrir Pull Request hacia <code>develop</code>:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>git push -u origin feature/faseX-mi-tarea</code><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Llenar el template del PR y solicitar revisión a un compañero del equipo.",
            ParagraphStyle('GitBoxText', fontName='Helvetica', fontSize=7.8, leading=11, textColor=dark_text)
        )]
    ]
    t_git = Table(git_steps, colWidths=[letter[0] - 76])
    t_git.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#94A3B8")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_git)
    story.append(Spacer(1, 8))

    # Pie de firma
    story.append(Paragraph(
        "<i>Documento generado automáticamente para el equipo de Comunicaciones I (UTP) &bull; Coordinador: Camilo</i>",
        ParagraphStyle('DocSign', fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=colors.HexColor("#94A3B8"), alignment=1)
    ))

    # Construir el documento
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF Generado Exitosamente] -> {filename}")


if __name__ == "__main__":
    out_pdf = os.path.join(os.path.dirname(__file__), "Plan_de_Trabajo_Colaboradores_DSP.pdf")
    build_pdf(out_pdf)
