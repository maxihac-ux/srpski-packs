# Полный ASR-гейт sr-ru-a1-audio-m **1.0.2** (инструкция №25)

Дата: 2026-11-09 · Гейт: asr_gate.py (whisper-base ONNX, sr-RS, локально) · 1447/1447 файлов пака.
Вердикты: REJECT sim<0.45; REVIEW 0.45–0.60; OK ≥0.60. Два заменённых файла взяты из audio_fix_a1m_2.zip владельца (байт-в-байт), не пересинтезированы.

| Вердикт | Файлов | Доля |
| --- | --- | --- |
| OK | 1400 | 96.8% |
| REVIEW | 30 | 2.1% |
| REJECT | 17 | 1.2% |
| Всего | 1447 | 100% |

Заменённые в 1.0.2: w060 sim 0.67 OK («Ljewo.» — владелец: 0.67), w1092_ex sim 0.91 OK («Munje o svetlila nebo.» — владелец: 0.91).

## Не-OK (47)

| id | вердикт | sim | ASR слышит | текст |
| --- | --- | --- | --- | --- |
| qa020cd843ba | REJECT | 0.24 | 20 euro. | Двадесет евра. |
| qa78a42f4c38 | REJECT | 0.15 | u 9. | У девет сати. |
| qa9794eba1d2 | REJECT | 0.0 | 10% | Десет сати. |
| qac2b3ea4a4a | REJECT | 0.38 | 80 uveć. | У осам сати увече. |
| qae8ecd91042 | REJECT | 0.36 | Ujovo. | У јулу. |
| w007_ex | REJECT | 0.32 | Wobec, le, wovo. | Све је добро. |
| w065 | REJECT | 0.0 | 3 | три |
| w071 | REJECT | 0.4 | David. | девет |
| w073 | REJECT | 0.0 | 20. | двадесет |
| w085_ex | REJECT | 0.22 | Dot a via Rzorgog. | Мој брат је студент. |
| w1078 | REJECT | 0.29 | Jeb. | џеп |
| w1101_ex | REJECT | 0.26 | Rambičas te majd. | Вода из чесме је чиста. |
| w1111 | REJECT | 0.0 | 4. | четвртина |
| w1111_ex | REJECT | 0.31 | 4-15 minuta. | Четвртина сата је петнаест минута. |
| w114_ex | REJECT | 0.32 | kad je met burej. Daž kov gip. | Српска храна је укусна. |
| w115_ex | REJECT | 0.29 | John Dresbenub. | Вода је хладна. |
| w314_ex | REJECT | 0.12 | Laloht be a duro. | Грожђе је слатко. |
| qa36667b8655 | REVIEW | 0.57 | 100 dina. | Сто динара. |
| qa5a1a940f36 | REVIEW | 0.55 | U 700 u jutro. | У седам сати ујутру. |
| qa8ec32e49de | REVIEW | 0.59 | i mošli dajt se. | Имаш ли деце? |
| w030 | REVIEW | 0.5 | Twoi. | твој |
| w073_ex | REVIEW | 0.5 | Platius on 20 euro. | Платио сам двадесет евра. |
| w087 | REVIEW | 0.57 | Sime. | син |
| w090 | REVIEW | 0.5 | Dada. | деда |
| w1035 | REVIEW | 0.55 | Zbela. | ципела |
| w1052 | REVIEW | 0.55 | uvetsi. | увече |
| w1060 | REVIEW | 0.5 | Smak. | смех |
| w1061 | REVIEW | 0.55 | lonuts. | лонац |
| w1080 | REVIEW | 0.46 | Bek mis. | пекмез |
| w1096_ex | REVIEW | 0.56 | Je tren vajem organ. | Јетра је важан орган. |
| w1110 | REVIEW | 0.5 | Bova. | пола |
| w112_ex | REVIEW | 0.51 | Meset i ma 30 dana. | Месец има тридесет дана. |
| w141 | REVIEW | 0.53 | Kohohini. | кухиња |
| w142 | REVIEW | 0.56 | Ko pa te o. | купатило |
| w154 | REVIEW | 0.57 | Drag. | трг |
| w201 | REVIEW | 0.57 | Rekš. | реч |
| w217 | REVIEW | 0.57 | Bres. | брз |
| w234 | REVIEW | 0.57 | Poon. | пун |
| w235 | REVIEW | 0.57 | Otvaraj. | отворен |
| w243 | REVIEW | 0.5 | Seran. | црн |
| w299 | REVIEW | 0.46 | Jo bude. | јогурт |
| w335 | REVIEW | 0.5 | Bice. | пица |
| w695 | REVIEW | 0.5 | Vela. | врло |
| w708 | REVIEW | 0.5 | Bila. | пиле |
| w715 | REVIEW | 0.57 | Kokorus. | кукуруз |
| w724 | REVIEW | 0.5 | Pitch. | пећ |
| w735 | REVIEW | 0.59 | Wozneret. | возни ред |

Не-OK совпадает с известным списком: числовые ложные срабатывания (qa78a42f4c38, qa9794eba1d2, qac2b3ea4a4a, w065, w071, w073, w1111…), пары из human_listen (w007_ex, w085_ex, w1101_ex, w114_ex, w115_ex, w314_ex, qae8ecd91042, w1078) и короткие слова 0.45–0.60 (REVIEW).
