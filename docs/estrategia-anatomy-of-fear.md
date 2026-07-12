# The Anatomy of Fear — Estrategia y diseño completo
### Pieza scrollytelling estilo The Pudding para Pulp Analytics

---

## 1. Concepto

**Título:** *The Anatomy of Fear: 100 Years of Horror Movie Posters*
**Subtítulo:** *We analyzed 32,000 horror posters to see how the way we sell fear has changed — one pixel at a time.*

**Tesis narrativa:** el póster de terror es un fósil cultural. Cada década vende el miedo de su época: los monstruos pintados de los 30, el ocultismo fotográfico de los 70, el negro-y-rojo del slasher ochentero, el minimalismo del "elevated horror" actual. Analizando color, brillo, saturación y composición de los pósters se puede *medir* esa evolución — y contarla visualmente.

**Por qué este ángulo gana:**
- Es 100% alcanzable con datos públicos (TMDB tiene póster para casi todo el catálogo).
- Es inherentemente visual: el dato *es* la imagen. Ideal para scrollytelling.
- Hay hueco real: existen análisis de color de pósters en general ([Vijay Pandurangan, 35k pósters](https://flowingdata.com/2012/06/13/evolution-of-movie-poster-colors/)) y estudios académicos de color en tráilers ([The Colour of Horror, ACM 2022](https://dl.acm.org/doi/10.1145/3565516.3565523)), pero **nadie ha hecho la pieza narrativa tipo Pudding dedicada solo al terror**.
- Conecta con la identidad "pulp" de tu blog (tus piezas de Metallica y Cube ya mezclan pop culture + analítica).

---

## 2. Plan de datos

### Fuentes
| Fuente | Qué aporta | Costo |
|---|---|---|
| [TMDB API](https://developer.themoviedb.org/) | Metadata + `poster_path` de todo el género horror | Gratis (con atribución) |
| [Dataset horror-movies de Tanya Shapiro](https://github.com/tashapiro/horror-movies) (TidyTuesday 2022) | 32,540 películas de terror ya filtradas, con `poster_path`, fecha, rating, revenue, subgéneros | Gratis, arranque inmediato |
| [Stephen Follows / Horror Movie Report](https://stephenfollows.com/p/the-horror-movie-report) | Contexto de industria para el texto (el terror = >20% de estrenos, género más rentable) | Citar |

### Pipeline (Python)
1. **Descarga:** posters vía `https://image.tmdb.org/t/p/w342/{poster_path}` (w342 basta para análisis de color). ~30k imágenes ≈ 1 GB.
2. **Extracción por póster:** con Pillow + scikit-learn:
   - Paleta dominante: k-means (k=5) en espacio LAB, ponderando saturación (método del paper ACM).
   - Brillo medio (L*), saturación media, % de píxeles "oscuros" (L<20).
   - % de píxeles rojos (hue 345°–15°, S>40).
   - Entropía de color (¿póster caótico pulp vs. minimalista?).
3. **Composición (opcional, capítulo extra):** detección de caras con OpenCV → ¿cuántas caras?, ¿ojos visibles?, % de espacio negativo.
4. **Agregación:** métricas por año y por subgénero → JSON estáticos que alimentan la página (sin backend).

### Métricas-historia (cada una es una sección)
- **The Color River:** distribución de hue por década (stream graph).
- **The Darkness Curve:** brillo medio por año, 1920→2025. Hipótesis verificable: cae en los 70 y toca fondo en los 2000 (torture porn), con leve repunte A24.
- **The Rise of Red:** % de rojo por año, con anotaciones (Psycho, Halloween, Scream).
- **The Vanishing Face:** nº medio de caras por póster — del collage pulp al objeto único minimalista.
- **Bonus:** paleta media por subgénero (slasher vs. ghost vs. zombie vs. folk horror).

---

## 3. Estructura narrativa de la página (sección por sección)

Arquitectura Pudding clásica: *hook visual → pregunta → capítulos cronológicos con scrollytelling → interactivo exploratorio → metodología*.

1. **Hero.** Fondo: mosaico de cientos de pósters reales en desorden que, al hacer scroll, se ordenan por color formando un gradiente temporal. Título con tipografía condensada estilo slasher. Un dato-gancho: *"32,540 posters. 100 years. One question: what does fear look like?"*
2. **Intro (texto corto).** 3 párrafos: el póster como fósil cultural + qué medimos + invitación a bajar.
3. **The Color River.** Stream graph de hues por década a ancho completo; scroll-triggered: cada década se ilumina con 3 pósters ejemplares.
4. **Capítulos por era** (patrón: panel sticky con pósters a la izquierda, tarjetas de texto+dato deslizando a la derecha):
   - *1920s–30s — Painted Monsters:* litografía, paletas cálidas, el monstruo en el centro.
   - *1940s–50s — Atomic Pulp:* amarillos y rojos chillones, exclamaciones tipográficas ("SEE!").
   - *1960s–70s — The Occult Turn:* llega la fotografía; el negro se apodera del fondo (Rosemary's Baby, The Exorcist).
   - *1980s — Black & Red:* el slasher impone la fórmula: fondo negro, arma, sangre, título metálico.
   - *1990s–2000s — The Desaturation:* Scream/torture porn; verde-azul frío, caras flotantes de estrellas.
   - *2010s–hoy — Elevated Minimalism:* A24, espacio negativo, un solo objeto simbólico, tipografía serif.
5. **The Darkness Curve.** Línea anotada de brillo 1920→2025. Momento "payoff" de la tesis.
6. **The Rise of Red.** Área roja creciendo sobre fondo negro. Anotaciones de hitos.
7. **Explorador interactivo.** Grid de los 32k pósters filtrable por década/subgénero/color dominante; click → paleta extraída de ese póster. (Es la parte compartible/viral.)
8. **Methodology + créditos.** Transparencia total estilo Pudding: fuentes, código en GitHub, limitaciones. Atribución TMDB obligatoria.

**Extensión objetivo:** 1,800–2,200 palabras de texto. Lectura: 8–10 min.

---

## 4. Sistema visual

- **Tema:** fondo casi-negro `#0a0a0c`, texto hueso `#e8e4da`, acento rojo sangre `#c1121f`, acento secundario ámbar `#e5a00d` (guiño pulp).
- **Tipografía:** display condensada tipo grindhouse (p. ej. *Anton* o *Oswald*) para títulos; serif legible (*Source Serif*/Georgia) para el cuerpo — el contraste "póster vs. ensayo" refuerza el concepto.
- **Regla de oro Pudding:** el efecto de scroll solo cuando revela información; el resto, texto estático limpio.
- **Los pósters reales son la estrella:** los gráficos usan paletas extraídas de los propios pósters, no colores arbitrarios.
- Mobile-first: los paneles sticky degradan a imagen-luego-texto apilados.

---

## 5. Stack técnico

- **Análisis:** Python (Pillow, scikit-learn, OpenCV, pandas) → JSONs estáticos.
- **Página:** Svelte + D3 + Scrollama (el stack real de The Pudding) o, más simple, HTML/CSS/JS vanilla con IntersectionObserver (suficiente y sin build).
- **Librerías recomendadas por The Pudding** (de su [FAQ de recursos](https://pudding.cool/resources/)): [Scrollama](https://github.com/russellgoldenberg/scrollama) para los capítulos, [enter-view](https://github.com/russellgoldenberg/enter-view) para reveals ligeros, [d3-annotation](http://d3-annotation.susielu.com/) para las anotaciones de la Darkness Curve y Rise of Red, [noUiSlider](https://refreshless.com/nouislider/) para el slider de años del explorador.
- **Responsive:** seguir sus [Responsive Scrollytelling Best Practices](https://pudding.cool/process/responsive-scrollytelling/) — en móvil el gráfico va fijo arriba y el texto pasa por encima (nunca sticky lateral). Su estudio [How Many Users Resize Their Browser?](https://pudding.cool/process/resize/) concluye que casi nadie redimensiona: basta calcular el layout al cargar.
- **Hosting:** GitHub Pages o Netlify (gratis, estático).
- **Derechos:** los pósters son material promocional; su uso analítico/editorial con thumbnails es práctica estándar (así operan Pudding, FlowingData, Stephen Follows). Incluir atribución TMDB y disclaimer de fair use en metodología.

---

## 6. Estrategia de lanzamiento

- **Timing:** publicar la primera semana de octubre (pico de interés por Halloween; el explorador da 4 semanas de vida compartible).
- **Piezas satélite en Medium (Pulp Analytics):** (1) "How I analyzed 32,000 horror posters with Python" (tutorial técnico — tu audiencia actual), (2) "5 things the data taught me about fear" (listicle-teaser que enlaza a la página).
- **Distribución:** r/dataisbeautiful (el explorador), r/horror (los hallazgos), Hacker News (el pipeline), newsletter Data Is Plural, y taggear a Stephen Follows/The Pudding en X-Bluesky — ambos amplifican trabajo del gremio.
- **[Pudding Cup](https://pudding.cool/pudding-cup):** inscribir la pieza — The Pudding premia anualmente los mejores proyectos visuales hechos fuera de su equipo. Ganar o quedar destacado es la mejor amplificación posible para esta pieza.
- **Ruta alternativa — [Pitch Us](https://pudding.cool/pitch):** The Pudding acepta pitches de freelancers (remunerados). Opción: pitcharles la historia y publicarla directamente en pudding.cool. Trade-off: máxima audiencia y pago vs. la pieza no vive en tu dominio ni construye tu marca. Recomendación: publicar en tu sitio e inscribir al Pudding Cup; si buscas el salto profesional, pitchear primero y publicar tú si no la aceptan (su [guía de pitching](https://pudding.cool/process/pitching-gendered-descriptions/) documenta el proceso).
- **Métrica de éxito:** tiempo en página >4 min y % de scroll >60% (no pageviews).

---

## 7. Roadmap (6 semanas, ritmo part-time)

| Semana | Entregable |
|---|---|
| 1 | Descarga de dataset + posters; pipeline de color funcionando en 1,000 pósters |
| 2 | Pipeline completo en 32k; checkpoint [Continue / Pivot / Put It Down](https://pudding.cool/process/pivot-continue-down/): ¿los datos confirman la Darkness Curve o la historia es otra? |
| 3 | **Storyboard** (proceso Pudding: bocetar cada sección con su gráfico antes de codear) + redacción del ensayo en inglés + selección de 30-40 pósters ejemplares |
| 4 | Maquetación: hero, color river, capítulos |
| 5 | Darkness Curve, Rise of Red, explorador |
| 6 | Mobile, QA, metodología, lanzamiento |

**Riesgos y mitigación:** si los datos no confirman una hipótesis, esa *es* la historia (estilo Pudding: "we expected X, found Y"). Si 32k pósters pesan mucho, muestrear 8–10k estratificados por año da las mismas curvas.

---

## 8. Prototipo

Adjunto `anatomy-of-fear-prototype.html`: mockup navegable con la estructura completa, sistema visual y scrollytelling funcionando. **Los datos del prototipo son ilustrativos** (marcados como sample); el pipeline de la sección 2 los reemplaza.
