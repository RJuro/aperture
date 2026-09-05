# Reading the 8-material Ellis Island record

Source: `bench/records/ellis-8mat.md`. Counts are parsed claim-level and reproduce the record's own
totals: 748 claims, 74 lines, 5 sparse marks, 224 theme×material cells. Compared against
`ellis-v3-earlier.md` (2 materials, 8 themes, same architecture) and `calibrated-students-2.md`
(5 materials, 12 themes).

---

## 1. The three language themes

Names and gists verbatim:

| Theme | Gist | Header |
|---|---|---|
| **Language as barrier and gateway** | "Suppression or absence of a shared language determines whether a child can enter schooling and whether a parent can navigate institutions." | in 7 of 8 · 53 claims on 53 passages · 23 shared · candidate |
| **Language practices across migration** | "How multilingualism precedes migration as an ordinary condition and English is acquired through immersion rather than formal instruction." | in 4 of 8 · 33 claims on 32 passages · 21 shared · candidate |
| **Heritage language retained and valued** | "Heritage language continues voluntarily in the destination and is valued as cultural and literary enrichment rather than discarded for assimilation." | in 1 of 8 · 12 claims on 12 passages · 4 shared · candidate |

### Per material, and passages held twice

| Material | barrier | practices | heritage | barrier ∩ practices (same `sid`) |
|---|---:|---:|---:|---:|
| Mary Masare Thome | 14 | — (not assessed) | — (not assessed) | 0 |
| Lillian Kaiz | — (not looked for) | — (not assessed) | — (not assessed) | 0 |
| Charles Rizzuto | 8 | — (not assessed) | — (not assessed) | 0 |
| Yolan Szency Batta | 5 | 5 | — (not looked for) | **2** (S346, S407) |
| Elizabeth Friedman | 11 | 14 | — (not looked for) | **7** |
| Helen Hansen | 1 (sparse) | — (not looked for) | — (not looked for) | 0 |
| Leona Turkin | 12 | 11 | — (not looked for) | **9** |
| Eleanor Larsen | 2 (sparse) | 3 (sparse) | 12 | **1** (S331) |
| **Total** | **53** | **33** | **12** | **19** |

heritage ∩ barrier = 0; heritage ∩ practices = 1 (Larsen S340); heritage ∩ *Ethnic enclave* = 4 —
its strongest tie is to a non-language theme.

**Five examples each.**

| Theme | sid | Claim |
|---|---|---|
| barrier | S034 | Schooling in Austria-Hungary required Hungarian; the children's own language had no place in the school. |
| barrier | S173 | The mother's lack of English prevented her from writing a school excuse for her daughter's absence. |
| barrier | S176 | Kindergarten functioned as a language holding period; she remained there until English was acquired. |
| barrier | S143 | Accent marked the children at school as different; classmates' teasing was the form the language barrier took. |
| barrier | S494 | Knowing English at her citizenship hearing meant the judge held her to a higher standard than other applicants. |
| practices | S176 | English was acquired by placement in kindergarten alongside younger children, not a language class. |
| practices | S404 | Schooling in Russia already included German and French for the older sisters. |
| practices | S409 | English is described as something that arrived on its own, without study or apparent effort. |
| practices | S528 | Russian was never lost, enabling the speaker's later work as a translator. |
| practices | S332 | She rejects the position that people coming to America need to be taught in their own language. |
| heritage | S338 | The church's worship was conducted entirely in the heritage language. |
| heritage | S342 | Danish at home is described as spontaneous rather than enforced. |
| heritage | S345 | Other immigrants are contrasted for wanting to discard the heritage language. |
| heritage | S349 | The heritage language is valued for access to Danish literature in its original form. |
| heritage | S352 | The sibling's translations are described as matching what the father would have written himself in English. |

**Judgement: two patterns, not three.**

barrier and practices are one pattern read twice. 19 of practices' 33 claims (58%) sit on a passage
barrier already holds in the same material, and there the two paraphrase each other — S500: "The
mother acquired English partly through radio soap operas, a source outside the family" / "The mother
learned English by listening to radio soap operas." **For those 19 the merge is mechanical**: same
passage, same sense, drop one of each pair. **For the other 14 it is interpretive** — repertoire
facts with no barrier twin, except barrier carries repertoire facts of its own (Batta S407, Turkin
S175), so no boundary survives. The merged gist needs rewriting: barrier's test, "determines whether
a child can enter schooling and whether a parent can navigate institutions", is one roughly half the
merged claims do not meet.

heritage stays apart: 0 shared passages with barrier, 1 with practices, and its other 11 claims are
about voluntary retention and its worth, not access. It is single-material — a candidate, not
foldable into a 7-of-8 theme on one case.

Fixture: `bench/records/language-themes.json` (all 98 claims, plus `expected.merge` /
`expected.keep_apart` / `why`).

### The other near-duplicate pairs, briefly

**Detention vs child's threshold — keep apart, repair the gist.** Detention is "How **adult
detainees** experience the processing center as a place of constant bureaucratic sorting, sustaining
themselves through cross-ethnic solidarity, social networks, and political leverage." It runs in 3
materials (Batta 13, Friedman 11, Larsen 3) and shares **1** of its 27 passages with threshold
(Larsen S283); in Batta the two hold 13 and 14 claims of one episode with **zero** shared passages —
a partition by facet. Larsen's line reports the definition failing: "What the theme's definition
expects beyond this — adult detainee perspective, cross-ethnic solidarity, social networks,
political leverage — is absent here. The narrator was four years old" (confirmed in `T2 DP-35
LARSEN`). That line is *sparse*; the defect is the "adult detainees" clause, not the theme.

**Economic push-pull vs property vs class descent — keep all three.** Pairwise overlap 1, 0, 0.
Three objects: motive (Hansen, Larsen), resource (Rizzuto, Friedman, Turkin, Larsen), trajectory
(Turkin only). The one shared passage, Larsen S192, is read in *opposite* directions — "The scarcity
is described as total, affecting everybody" vs "The claim that nobody possessed anything is a
destitution narrative the family's documented property positions them against" — a tension to log,
not a merge. The redundancy overlap misses: in Turkin, property's 3 claims and class descent's first
3 (S042, S048, S078) state the same standing on different sentences.

**Ethnic enclave vs ethnic institutions — merge.** Both live only in Hansen (12 and 9 claims) and
share **4** passages, 44% of institutions' total, near-paraphrased (S272: "…she is the only Scotch
person" / "…the institutional base is gone; she is the only Scot"). Mechanical on those 4,
interpretive on the other 5: enclave's gist has no room for the decline arc.

---

## 2. What sequential reading lost: the Thome claims

**Against the 2-material run (`ellis-v3-earlier.md`, same architecture): nothing changed.** Thome
has 70 claims on 65 passages in both. By passage id, 65 of 65 sids in both, 0 only in one; comparing
claim text, quote, `partly` note and theme: **65 identical, 0 changed, 0 disappeared, 0 new.** Same
six themes, same counts (barrier 14, family separation 14, lodging 14, threshold 12, children's
labor 10, known contacts 6). Six more materials and 22 further themes came after, and none touched
her. Sequential reading did not *change* Thome's claims — it **froze** them at a 2-material corpus.
What was lost is application: 20 of her 28 cells read "not assessed yet".

**Against the 5-material run (a different theme set): the reading is genuinely different.** 105
claims on 96 passages there vs 70 on 65 here. By passage id: **34 shared, 62 only there, 31 only
here** — and of the 34 shared, **0** have identical text (S034: "The village school imposed
Hungarian as the required language" → "Schooling in Austria-Hungary required Hungarian; the
children's own language had no place in the school").

- **Moved because the theme set moved (the 34 shared).** All 34 reassigned: S034/S036 from
  *Institutional encounters reshaping identity* to *barrier*; S231–S243 from *Crossing as
  improvisation* / *Detention as confinement* to *child's threshold* and *Family separation*; S310
  from *Household labor as collective survival* to *Children's household labor*. Same evidence, new
  containers, rewritten wording.
- **Moved because the reading changed (93 passages).** The 62 dropped are the ones whose 5-material
  themes have no v3 successor: *Childhood ability displayed and diverted* (skipping a grade, the
  principal, the unrecovered gaps), *Crossing as improvisation* (the wicker trunk, the feather beds,
  the child carrying water through steerage), *Worker resistance*, *Emotion and memory about
  homeland* (the brook still running, the friend who recognised her decades later). The 31 new ones
  cluster in the two themes v3 built out, *Lodging and rental* and *Children's household labor*.

The 5-material reading found Thome's schooling ambition, her wage-labour resistance and the texture
of the crossing; the v3 reading found her household economy. Neither is a superset — and v3, once
written, never revisited her.

---

## 3. Hedge density

Reading order = order of the Materials section; the processing history carries no per-material
dates and the theme history has one dated entry. Passage counts come from the derivation line
"claims rest on N of M passages"; word counts are `wc -w` on the matching transcript.

| # | Material | Claims | `partly` | Share | Passages (M) | Rest on (N) | Words | Words/passage |
|--:|---|--:|--:|--:|--:|--:|--:|--:|
| 1 | Mary Masare Thome | 70 | 16 | 22.9% | 532 | 65 | 6,395 | 12.0 |
| 2 | Lillian Kaiz | 63 | 22 | 34.9% | 334 | 60 | 4,004 | 12.0 |
| 3 | Charles Rizzuto | 90 | **73** | **81.1%** | 1,105 | 77 | 6,171 | **5.6** |
| 4 | Yolan Szency Batta | 90 | 37 | 41.1% | 493 | 78 | 3,412 | 6.9 |
| 5 | Elizabeth Friedman | 142 | 32 | 22.5% | 565 | 120 | 6,137 | 10.9 |
| 6 | Helen Hansen | 68 | 38 | 55.9% | 315 | 58 | 2,499 | 7.9 |
| 7 | Leona Turkin | 113 | 40 | 35.4% | 309 | 77 | 3,882 | 12.6 |
| 8 | Eleanor Larsen | 112 | 33 | 29.5% | 449 | 93 | 4,783 | 10.7 |
| | **Total** | **748** | **291** | **38.9%** | | | | |

The `partly` share tracks **neither** length nor order: by position it runs 23, 35, 81, 41, 23, 56,
35, 30, and the longest transcript (Thome) has the second-lowest share while the third-longest
(Rizzuto) has the highest. It tracks **passage granularity** — the three materials averaging under
8 words per passage carry the three highest shares (Rizzuto 5.6 w/p → 81%, Hansen 7.9 → 56%, Batta
6.9 → 41%), while all five at 10.7 w/p or above sit in a 22–35% band. Rizzuto's 1,105 passages for
6,171 words is a nursing-home transcript chopped into fragments, and his notes say so ("'only two
words' and 'for a single occasion' are not stated"; "'once in Brooklyn' is not stated in this
passage") — the claim outruns the sentence because the sentence is too short to hold it, not
because the reader hedged.

---

## 4. Coverage table

28 × 8 = 224 cells. `n` = line with n claims, `n*` = sparse (< 4), `·` = not looked for,
`?` = not assessed yet.

| Theme | Thome | Kaiz | Rizzuto | Batta | Friedman | Hansen | Turkin | Larsen |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Ellis Island as a child's threshold | 12 | 14 | 11 | 14 | 14 | 9 | 9 | 12 |
| Family separation and reunion | 14 | 14 | 13 | 14 | 14 | 8 | 14 | 14 |
| Migration through known contacts | 6 | 9 | 12 | 10 | 9 | 7 | 10 | 6 |
| Childhood memory as partial and mediated | · | 12 | · | · | · | 9 | 11 | 14 |
| Economic push and pull of emigration | ? | ? | ? | · | · | 6 | · | 10 |
| Emotional weight of homeland | ? | ? | 11 | · | 11 | · | · | · |
| Ethnic enclave as bounded social world | ? | ? | ? | · | · | 12 | · | 10 |
| Household authority in sending family | ? | ? | 9 | 10 | · | · | 7 | · |
| Language as barrier and gateway | 14 | · | 8 | 5 | 11 | 1* | 12 | 2* |
| Language practices across migration | ? | ? | ? | 5 | 14 | · | 11 | 3* |
| Navigating immigration detention | ? | ? | ? | 13 | 11 | · | · | 3* |
| Property as migration's economic foundation | ? | ? | 12 | · | 8 | · | 3* | 11 |
| Violence as habitual backdrop | · | 14 | · | 6 | 13 | · | 8 | · |
| Absence of arrival support → volunteerism | ? | ? | ? | · | 12 | · | · | · |
| Childhood disrupted by delays and losses | ? | ? | ? | · | 13 | · | · | · |
| Children's household labor | 10 | · | · | · | · | · | · | · |
| Children's journey as freedom and ordeal | ? | ? | ? | · | · | · | · | 7 |
| Class descent and adaptation | ? | ? | ? | · | · | · | 11 | · |
| Craft displaced and redirected | ? | ? | ? | · | · | · | · | 8 |
| Economic loss defeating educational promise | ? | ? | ? | · | 12 | · | · | · |
| Ethnic institutions formed and fading | ? | ? | ? | · | · | 9 | · | · |
| Heritage language retained and valued | ? | ? | ? | · | · | · | · | 12 |
| Immigrant women's occupational trajectory | ? | ? | ? | 13 | · | · | · | · |
| Lodging and rental as household economy | 14 | · | · | · | · | · | · | · |
| Religious observance shaping work/residence | ? | ? | ? | · | · | · | 11 | · |
| Theft and loss during border crossing | ? | ? | ? | · | · | · | 6 | · |
| Women's wage work shaped by family stage | ? | ? | ? | · | · | 7 | · | · |
| Workplace mobility as assertion of freedom | ? | ? | 14 | · | · | · | · | · |

**Totals:** line **74** (748 claims), of which **5 sparse** (Hansen/barrier, Larsen/barrier,
Larsen/practices, Larsen/detention, Turkin/property) · not looked for **94** · not assessed **56** ·
**looked-for-too-thin 0** · **residual 0**. Two of §13's four silences never occur.

**Not-assessed cells in themes with ≥ 2 carrying materials — what a back-fill would read: 18**, in 7
themes (push-pull 3, ethnic enclave 3, language practices 3, detention 3, emotional weight 2,
household authority 2, property 2). All 56 not-assessed cells fall on the first three materials
read: Thome 20, Kaiz 20, Rizzuto 16; materials 4–8 have none.

---

## 5. What the six points did not name

- **No frozen themes, 3 open, 25 candidates.** §12 calls a candidate "a pattern found in one
  material so far", yet *barrier* is a candidate at 7 of 8 materials and 53 claims, and 10
  candidates run in 2 or more. The ceiling counts open + frozen, so with 3 open it never bit —
  nothing forced the merge-down that would have caught the language pair.
- **A 14-claim cap truncates lines silently.** 15 of 74 lines land on exactly 14, the modal value.
  One truncation is disclosed ("kept the first 14 of 21 claims", Kaiz); the other 14 say nothing.
  Line counts are not a prevalence measure where the cap binds.
- **Law 2's verb never ran.** "Nothing has been checked against the material yet." No CHECK, no
  researcher feedback; the theme history holds one entry for one theme, and no `stable_passes` or
  Freeze appears.
- **The "before reading that as absence" footnote points at the wrong thing.** It promises "a set of
  claims too thin to keep is dropped whole", but every item it lists is a summary-overreach note.
  Exclusions: 28 summary-overreach, 8 claims set aside, 2 moments dropped for an unfindable quote,
  1 line truncated.
- **16% of claims re-read an already-claimed passage.** 748 claims rest on 628 distinct (material,
  passage) pairs; 102 passages carry 2 or 3 claims, 120 in excess, concentrated in *Family
  separation* (46 shared) and the language pair (19 mutual). Nothing aggregates it, so a reader can
  count one sentence three times as spread.
- **8 line summaries carry a stale disclaimer** — "(1 claim was set aside after checking; this
  summary predates that.)" — prose and claim list written against different evidence.
