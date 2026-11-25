# Catálogo de especies · San Blas Reserva Ambiental

Web con las plantas y aves de San Blas Reserva Ambiental (San Miguel de Abona, Tenerife):
foto, descripción y usos tradicionales en **español de Canarias, inglés y alemán**.

Pensada para publicarse en https://sanblasreservaambiental.org/catalogo/ (GitHub Pages).

## Archivos

| Archivo | Qué contiene |
|---|---|
| `index.html`, `estilo.css`, `catalogo.js` | La web (mismo estilo que *Materiales*). Sin dependencias. |
| `datos.js` | Las fichas de cada especie, en los tres idiomas. Aquí se corrigen textos o se añaden especies. |
| `datos-inat.js` | Especies observadas en iNaturalist alrededor de la reserva (se genera con el script). |
| `taxonomia.js` | Reino, clase, orden y familia de cada especie, para el selector de nivel (se genera con el script). |
| `img/` | Imágenes de las guías de plantas y aves de San Blas. |
| `img/inat/` | Fotos de iNaturalist con licencia Creative Commons (las descarga el script). |
| `herramientas/actualizar_inat.py` | Actualiza `datos-inat.js` desde el proyecto de iNaturalist. |

## Actualizar las especies de iNaturalist

```
python herramientas/actualizar_inat.py            # consulta iNaturalist
python herramientas/actualizar_inat.py --sin-red  # regenera desde la copia guardada
```

El script recoge **todas las observaciones de iNaturalist en un radio de 750 m alrededor de la reserva**
(no solo las del proyecto [San Blas Reserva Ambiental](https://www.inaturalist.org/projects/san-blas-reserva-ambiental),
que todavía tiene pocas), las agrupa por especie y guarda el resultado en `herramientas/inat-cache.tsv`.
Después genera `datos-inat.js` y descarga la foto representativa de cada especie nueva **solo si tiene licencia
Creative Commons**, guardando autor y licencia (la web los muestra en la ficha). Si las fotos pesan mucho,
conviene reducirlas a unos 700 px antes de subirlas.

Las correcciones a mano van en `herramientas/ajustes-inat.json`:

- `nombres_es`: nombre canario cuando el de iNaturalist no sirve (p. ej. *Cenchrus setaceus* → «Rabo de gato»).
- `estatus`: endémica, nativa, introducida, **invasora**… (claves de `ESTATUS` en `datos.js`).
- `excluir`: especies que aparecen por observaciones con ubicación oculta pero no viven aquí.
- `alias`: cuando iNaturalist usa otro nombre científico que nuestras fichas.

Las especies que ya tienen ficha en `datos.js` reciben el número de observaciones y el enlace a iNaturalist;
las nuevas aparecen como «ficha en preparación» hasta que se redacte su texto en `datos.js`. Las observaciones
con ubicación oculta (especies protegidas o autores que la esconden) llevan la etiqueta «Ubicación aproximada».

## Usar sin conexión (móvil)

El botón «Descargar para usar sin conexión» guarda en el móvil la web entera,
con todas las fotos y en los tres idiomas (unos 6 MB). Solo se descarga cuando se
pulsa, para no gastar datos a quien no lo quiere. En Android aparece además
«Añadir a la pantalla de inicio». En iPhone se explica cómo hacerlo desde Compartir.

- `sw.js`: service worker. Sirve desde el móvil lo descargado y, cuando la web
  cambia, renueva la copia sola. La página comprueba si hay versión nueva al
  abrirse, al volver a la app y cada 30 minutos; cuando la copia nueva está
  guardada entera aparece el aviso «Hay una versión nueva del catálogo ·
  Actualizar».
- `offline.js`: lista de archivos y versión. **Se genera**: al final de
  `actualizar_inat.py`, o a mano con `python3 herramientas/generar_offline.py`
  después de tocar `index.html`, `estilo.css`, un `.js` o `img/`.
- `manifest.webmanifest` e `iconos/`: nombre e icono al instalarlo.

Necesita HTTPS (o `localhost`). En la vista previa de Claude puede no funcionar.

## Marcas de «visto»

En cada ficha, el botón «¿Lo han visto? Márquenlo» señala las especies vistas
durante la visita. El botón «Vistos» de la barra filtra solo esas, y desde ahí
se pueden borrar todas para la siguiente visita. Se guardan en el propio
dispositivo (`localStorage`, clave `catalogo-vistos`), sin cuentas ni servidor,
así que funcionan sin conexión.

## Nivel del alumnado

Encima de los filtros hay un deslizador con cuatro niveles, los mismos de los cuadernos:

1. **Primaria 3.º–4.º · Reinos**: plantas, animales u hongos; solo nombres comunes.
2. **Primaria 5.º–6.º · Grupos**: aves, reptiles, peces, insectos, arácnidos, moluscos…
3. **ESO · Clases y órdenes**: filtros por clase y tarjetas agrupadas por orden.
4. **Bachillerato y FP · Familias**: tarjetas agrupadas por familia y clasificación completa en la ficha.

Los nombres en español de clases, órdenes y familias están en `herramientas/ajustes-inat.json` → `nombres_rangos`.
El nivel se puede fijar en el enlace con `?nivel=1` … `?nivel=4`.

## Enlaces directos

Cada ficha tiene su propia dirección, p. ej. `…/catalogo/#cardon`, y el idioma se puede fijar con `?lang=en` o `?lang=de`.
