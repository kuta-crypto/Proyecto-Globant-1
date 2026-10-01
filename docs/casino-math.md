# Matemática de los giros 6x6

Se cambió únicamente el generador de símbolos y las reglas de cálculo de los giros, conservando las interfaces, la matriz 6x6, el movimiento descendente, las cascadas, los guardados y los sistemas de personajes, mascotas, tienda y mejoras.

## Reglas

- Cinco símbolos existentes, con pesos base **27 / 24 / 21 / 17 / 11**. Cada casilla y cada reposición se sortean independientemente.
- Premios por **12 o más símbolos iguales en cualquier posición**, en tramos 12–14, 15–17 y 18+.
- Con cinco símbolos en 36 casillas, el umbral anterior de ocho obligaba a que siempre hubiera un ganador. El nuevo umbral permite tableros sin premio.
- Si hay premio, se retiran todos los símbolos premiados, caen los supervivientes y entran símbolos nuevos. Si no hay premio, no se vuelve a sortear el tablero.
- Se conserva el límite de diez cascadas. Es parte de las reglas de pago y de la simulación; no se impone un resultado perdedor cuando se alcanza.
- En el juego en vivo se usa `random.SystemRandom`, que obtiene su aleatoriedad del sistema operativo. `random.Random(seed)` queda reservado a pruebas y simulaciones explícitas.
- No se consulta el saldo, el historial de premios, las rachas ni un contador de retorno para decidir un resultado. La escala se fija antes de jugar y jamás se recalibra durante una partida.
- Las habilidades de suerte existentes siguen siendo modificadores explícitos. No son compensaciones ocultas y sus probabilidades no se incluyen en el RTP base indicado abajo.

## Tabla fija

Multiplicadores brutos de la apuesta por cada símbolo premiado, después de aplicar la escala fija **1,6364**. Se suman los premios de las cascadas.

| Símbolo | Probabilidad base por casilla | 12–14 | 15–17 | 18+ |
| --- | ---: | ---: | ---: | ---: |
| Moneda | 27% | 0,24546× | 0,65456× | 1,6364× |
| Siete | 24% | 0,4091× | 0,98184× | 2,4546× |
| Joker | 21% | 0,8182× | 2,4546× | 6,5456× |
| 69 | 17% | 1,6364× | 4,9092× | 13,0912× |
| Jackpot | 11% | 8,182× | 24,546× | 81,82× |

Los umbrales base de bonus se ajustan a los nuevos pesos: 12 Joker, 25 símbolos de alto valor combinados o 12 símbolos 69. Se conservan los efectos de las mejoras de bonus, las habilidades que lo activan y las rondas gratuitas. **Estas rondas adicionales no forman parte del RTP de premios base de la tabla.**

## Calibración y validación

1. Muestra de calibración: 1.000.000 de giros, semilla `20260929`, con escala provisional 1,63. Sugirió 1,636356 para un objetivo base de 0,96. Se fijó 1,6364.
2. Muestra independiente: 1.000.000 de giros, semilla `20260930`, con esa escala ya fijada.

Resultado de la segunda muestra:

| Medida | Resultado |
| --- | ---: |
| RTP base medido, sin redondeo | **96,2693%** |
| Intervalo aproximado de confianza del 95% | 95,8059%–96,7328% |
| Giros con algún premio de símbolos | 43,5512% |
| Giros sin premio de símbolos | 56,4488% |
| Giros cuyo premio supera la apuesta | 23,7069% |
| Cascadas medias por giro | 1,080802 |
| Giros que alcanzaron el límite con otro grupo visible | 0,2886% |
| RTP tras truncar premios a oro entero, apuesta 10 | **94,2674%** |

El objetivo del 96% está dentro del intervalo de la validación. El RTP es una media sobre muchas partidas, no una devolución garantizada por sesión. El redondeo existente a oro entero se conserva y reduce el retorno de premios pequeños; su efecto se muestra por separado.

**El retorno total del juego RPG es diferente**: personajes, suerte, mascotas, equipamiento, giros gratis, descuentos, habilidades y oro de viaje se aplican aparte. No se desactivaron esos sistemas para forzar un RTP total del 96%. Esta implementación no es una certificación para operar apuestas con dinero real.

El auditor usa conteos en lugar de coordenadas porque el premio depende únicamente de cuántos símbolos hay y todas las reposiciones son independientes. Una prueba compara 1.000 secuencias idénticas con el motor real de gravedad, incluyendo premios, número de cascadas y límites.

Reproducir la validación sin cargar ni modificar guardados:

```powershell
python tools/casino_math.py --spins 1000000 --seed 20260930 --output docs/casino-validation.json
python -m pytest -q
```

Los informes completos se guardaron en `casino-calibration.json` y `casino-validation.json`. La simulación es una comprobación estadística del modelo; no sustituye pruebas externas de certificación.

## Referencias utilizadas

- [Gambling Commission, RTS 7: Generation of random outcomes](https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-7-generation-of-random-outcomes): distribución, impredecibilidad, correspondencia entre reglas y pagos, y ausencia de compensación adaptativa.
- [Gambling Commission, Return to player](https://www.gamblingcommission.gov.uk/public-and-players/guide/return-to-player-how-much-gaming-machines-payout): RTP como promedio de largo plazo, no como promesa para cada partida.

Estas fuentes establecen criterios generales; no certifican este juego ni prescriben sus pesos, tabla o umbral de doce símbolos.
