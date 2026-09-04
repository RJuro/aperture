# {{ project.name }}

{{ app_name }} · started {{ project.created_at[:10] }} · {{ materials | length }} {{ 'material' | plural(materials | length) }} · {{ themes | length }} {{ 'theme' | plural(themes | length) }}

- [Across the corpus](#across-the-corpus)
- [Themes](#themes)
- [Materials](#materials)
- [Questions checked against the materials](#questions-checked-against-the-materials)
- [Excluded from the analysis](#excluded-from-the-analysis)
- [Researcher feedback](#researcher-feedback)
- [Processing history](#processing-history)
- [Theme history](#theme-history)

## Across the corpus

{% if summary %}**What the material shows**

{{ summary.text }}
{% else %}No project summary yet.
{% endif %}{% if interpretation and interpretation.text %}
**What this may mean, so far**

{{ interpretation.text }}
{% endif %}
**Focus.** {{ project.focus or "not set" }}
{% if focus_history %}
{% for f in focus_history %}- {{ f.created_at[:10] }} — {{ f.text }}
{% endfor %}{% endif %}
{% if project.brief %}**Open questions from the analysis**

{{ project.brief }}
{% endif %}
## Themes

{% if materials | length == 1 %}With one material, a theme cannot yet run across materials.

{% endif %}{% for group, rows in [("Across materials", themes | rejectattr("single") | list), ("In one material so far", themes | selectattr("single") | list)] %}{% if rows %}### {{ group }}

{% endif %}{% for t in rows %}#### {{ t.name }}

{{ t.gist }}

{{ t.derivation }} · {{ t.hold }}
{% if t.account %}
{{ t.account.text }}
{% endif %}{% if t.hold == 'frozen' and t.notes %}
##### What has pulled against this definition

{% for n in t.notes %}- {{ n.created_at[:10] }} — {{ n.text }}{% if n.display_title %} — {{ n.display_title }}{% endif %}
{% endfor %}
{% endif %}
##### Materials where this theme appears

{% for m in t.carrying %}**{{ m.display_title }}** — {{ (m.kind or "material") | replace("_", " ") }}
{% if m.summary %}
{{ m.summary.text }}
{% endif %}
[{{ m.claims }} {{ 'claim' | plural(m.claims) }} · printed in full under {{ m.display_title }} below](#{{ m.display_title | slug }})

{% else %}No material contains claims for this theme yet.
{% endfor %}{% if t.absent %}{% for head, mats in
   ([("Looked for and found too thin", t.absent | selectattr("looked_for") | list),
     ("Not looked for here", t.absent | rejectattr("looked_for") | list)]) %}{% if mats %}##### {{ head }}

{% for m in mats %}- {{ m.display_title }} — {{ (m.kind or "material") | replace("_", " ") }}
{% endfor %}
{% endif %}{% endfor %}{% if t.set_aside %}
Before reading that as absence, check what was excluded below — a set of claims too thin to keep
is dropped whole and would look the same as absence here:

{% for n in t.set_aside %}- {{ n.note }}{% if n.material %} — {{ n.material }}{% endif %}
{% endfor %}{% endif %}
{% else %}Every material contains claims for this theme.
{% endif %}
{% endfor %}{% endfor %}{% if not themes %}No themes yet.

{% endif %}
## Materials

{% for m in materials %}### {{ m.display_title }}

{{ (m.kind or "material") | replace("_", " ") }} · {{ m.derivation }}
{% if m.people %}
People: {% for p in m.people %}{{ p.name }}{% if p.aliases %} ({{ p.aliases }}){% endif %}{% if p.role %} — {{ p.role }}{% endif %}{% if not loop.last %}; {% endif %}{% endfor %}
{% endif %}{% if m.speakers %}
Speakers: {% for s in m.speakers %}{{ s.label }}{% if s.name %}, identified as {{ s.name }}{% endif %}{% if s.role %} ({{ s.role }}){% endif %}{% if not loop.last %}; {% endif %}{% endfor %}
{% endif %}{% if m.orientation %}
#### Before reading

{{ m.orientation.text }}
{% endif %}{% if m.reading %}
#### After reading

{{ m.reading.text }}
{% endif %}{% if m.angles %}
#### What to look for

{{ m.angles.text }}
{% endif %}
{% for th in m.threads %}#### {{ th.theme.name }}

{{ th.moments | length }} {{ 'claim' | plural(th.moments | length) }}
{% if th.summary %}
{{ th.summary.text }}
{% endif %}
{% for x in th.moments %}{{ loop.index }}. {{ x.claim }}
{% if x.support == 'partly' %}   The passage carries part of this: {{ x.support_note }}
{% endif %}   > {{ x.anchor }}  [{{ x.sid }}]
{% endfor %}
{% else %}No analysis yet.

{% endfor %}{% else %}No materials yet.

{% endfor %}
## Questions checked against the materials

{% for k in checks %}- {{ k.created_at[:10] }} — {{ k.question }}
  Verdict: {{ k.verdict }}. Searched {{ k.searched_n }} {{ 'passage' | plural(k.searched_n) }}{% if k.material_name %} in {{ k.material_name }}{% endif %}

{% for a in k.anchors %}  > {{ a.anchor }}{% if a.sid %}  [{{ a.sid }}]{% endif %}
{% endfor %}
{% else %}Nothing has been checked against the material yet.
{% endfor %}
## Excluded from the analysis

{% for name, notes in set_aside | groupby("material") %}### {{ name or "The project" }}

{% for n in notes %}- {{ n.note }}
{% endfor %}
{% else %}Nothing was excluded from the analysis.
{% endfor %}
## Researcher feedback

{% for f in feedback %}- {{ f.created_at[:10] }} — {{ f.kind }} on {{ f.about }}{% if f.text %}: {{ f.text }}{% endif %} — {{ f.outcome }}
{% else %}No researcher feedback yet.
{% endfor %}
## Processing history

{% for kind, rs in runs | groupby("kind") %}{% set ti = rs | sum(attribute="tokens_in") %}{% set to = rs | sum(attribute="tokens_out") %}- **{{ rs[0].step }}** — {{ rs | length }} {{ 'run' | plural(rs | length) }} · {{ ti }} input {{ 'token' | plural(ti) }} · {{ to }} output {{ 'token' | plural(to) }} · {{ rs | map(attribute="provider") | unique | join(", ") }} / {{ rs | map(attribute="model") | unique | join(", ") }}
{% endfor %}{% if not runs %}No processing history yet.
{% endif %}
## Theme history

{% for t in theme_history %}### {{ t.name }}
{% if t.status != "live" %}
Merged into another theme.
{% endif %}
Earlier versions (oldest first):

{% for h in t.history %}{{ h.at[:10] }} — **{{ h.name }}** — {{ h.gist }}

{% endfor %}
{% else %}No theme has been rewritten yet.
{% endfor %}
