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

{% if summary %}{{ summary.text }}
{% else %}No project summary yet.
{% endif %}
**Focus.** {{ project.focus or "not set" }}
{% if focus_history %}
{% for f in focus_history %}- {{ f.created_at[:10] }} — {{ f.text }}
{% endfor %}{% endif %}
{% if project.brief %}**Open questions from the analysis**

{{ project.brief }}
{% endif %}
## Themes

{% for t in themes %}### {{ t.name }}

{{ t.gist }}

{{ t.derivation }}
{% if t.account %}
{{ t.account.text }}
{% endif %}
#### Materials where this theme appears

{% for m in t.carrying %}**{{ m.title or m.name }}** — {{ m.kind or "material" }} · {{ m.claims }} {{ 'claim' | plural(m.claims) }}

{% for x in m.moments %}{{ loop.index }}. {{ x.claim }}
   > {{ x.anchor }}  [{{ x.sid }}]
{% endfor %}
{% else %}No material contains claims for this theme yet.
{% endfor %}
#### Materials where this theme does not appear
{% if t.absent %}
No claims in these materials support this theme:

{% for m in t.absent %}- {{ m.title or m.name }} — {{ m.kind or "material" }}
{% endfor %}{% if t.set_aside %}
Before reading that as absence, check what was excluded below — a set of claims too thin to keep
is dropped whole and would look the same as absence here:

{% for n in t.set_aside %}- {{ n.note }}{% if n.material %} — {{ n.material }}{% endif %}
{% endfor %}{% endif %}
{% else %}
Every material contains claims for this theme.
{% endif %}
{% else %}No themes yet.

{% endfor %}
## Materials

{% for m in materials %}### {{ m.title or m.name }}

{{ m.kind or "material" }} · {{ m.state }} · {{ m.derivation }}
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

{% for x in th.moments %}{{ loop.index }}. {{ x.claim }}
   > {{ x.anchor }}  [{{ x.sid }}]
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

{% for n in set_aside %}- {{ n.note }}{% if n.material %} — {{ n.material }}{% endif %}
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
