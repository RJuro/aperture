# {{ project.name }}

{{ app_name }} · started {{ project.created_at[:10] }} · {{ materials | length }} materials · {{ themes | length }} themes

- [Across the corpus](#across-the-corpus)
- [Themes](#themes)
- [Materials](#materials)
- [Checks](#checks)
- [What the readings set aside](#what-the-readings-set-aside)
- [What the researcher said](#what-the-researcher-said)
- [Runs](#runs)
- [Theme history](#theme-history)

## Across the corpus

{% if summary %}{{ summary.text }}
{% else %}Nothing has been written across the corpus yet.
{% endif %}
**Focus.** {{ project.focus or "not set" }}
{% if focus_history %}
{% for f in focus_history %}- {{ f.created_at[:10] }} — {{ f.text }}
{% endfor %}{% endif %}
{% if project.brief %}**What the readings carried forward**

{{ project.brief }}
{% endif %}
## Themes

{% for t in themes %}### {{ t.name }}

{{ t.gist }}

{{ t.derivation }}
{% if t.account %}
{{ t.account.text }}
{% endif %}
#### Where it runs

{% for m in t.carrying %}**{{ m.title or m.name }}** — {{ m.kind or "material" }} · {{ m.claims }} claims

{% for x in m.moments %}{{ loop.index }}. {{ x.claim }}
   > {{ x.anchor }}  [{{ x.sid }}]
{% endfor %}
{% else %}Nothing rests on this theme yet.
{% endfor %}
#### Where it does not
{% if t.absent %}
No claim in these rests on this theme:

{% for m in t.absent %}- {{ m.title or m.name }} — {{ m.kind or "material" }}
{% endfor %}{% if t.set_aside %}
Read that as silence only beside what the readings set aside naming this theme — a line too thin
to keep is dropped whole, and a dropped line and an empty one look the same here:

{% for n in t.set_aside %}- {{ n.note }}{% if n.material %} — {{ n.material }}{% endif %}
{% endfor %}{% endif %}
{% else %}
Every material carries claims under this theme.
{% endif %}
{% else %}No themes yet.

{% endfor %}
## Materials

{% for m in materials %}### {{ m.title or m.name }}

{{ m.kind or "material" }} · {{ m.state }} · {{ m.derivation }}
{% if m.people %}
People: {% for p in m.people %}{{ p.name }}{% if p.aliases %} ({{ p.aliases }}){% endif %}{% if p.role %} — {{ p.role }}{% endif %}{% if not loop.last %}; {% endif %}{% endfor %}
{% endif %}{% if m.speakers %}
Speaking: {% for s in m.speakers %}{{ s.label }}{% if s.name %} = {{ s.name }}{% endif %}{% if s.role %} ({{ s.role }}){% endif %}{% if not loop.last %}; {% endif %}{% endfor %}
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
{% else %}Nothing has been read here yet.

{% endfor %}{% else %}No materials yet.

{% endfor %}
## Checks

{% for k in checks %}- {{ k.created_at[:10] }} — {{ k.question }}
  {{ k.verdict }}, searched {{ k.searched_n }} passages{% if k.material_name %} in {{ k.material_name }}{% endif %}

{% for a in k.anchors %}  > {{ a.anchor }}{% if a.sid %}  [{{ a.sid }}]{% endif %}
{% endfor %}
{% else %}Nothing has been checked against the material yet.
{% endfor %}
## What the readings set aside

{% for n in set_aside %}- {{ n.note }}{% if n.material %} — {{ n.material }}{% endif %}
{% else %}The readings set nothing aside.
{% endfor %}
## What the researcher said

{% for f in feedback %}- {{ f.created_at[:10] }} — {{ f.kind }} on {{ f.about }}{% if f.text %}: {{ f.text }}{% endif %} — {{ f.outcome }}
{% else %}Nothing said yet.
{% endfor %}
## Runs

{% for kind, rs in runs | groupby("kind") %}- **{{ rs[0].step }}** ({{ kind }}) — {{ rs | length }} runs · {{ rs | sum(attribute="tokens_in") }} input tokens · {{ rs | sum(attribute="tokens_out") }} output tokens · {{ rs | map(attribute="provider") | unique | join(", ") }} / {{ rs | map(attribute="model") | unique | join(", ") }}
{% endfor %}{% if not runs %}Nothing has run yet.
{% endif %}
## Theme history

{% for t in theme_history %}### {{ t.name }}
{% if t.status != "live" %}
Merged into another theme.
{% endif %}
Earlier, oldest first:

{% for h in t.history %}{{ h.at[:10] }} — **{{ h.name }}** — {{ h.gist }}

{% endfor %}
{% else %}No theme has been rewritten yet.
{% endfor %}
