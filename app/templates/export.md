# {{ project.name }}

{{ project.created_at }}
{% if summary %}
## What the reading found

{{ summary.text }}
{% endif -%}
{% if project.brief %}
## Brief

{{ project.brief }}
{% endif %}
## Focus

{{ project.focus or "not set" }}
{% for f in feedback if f.target_kind == "focus" -%}
- {{ f.created_at }} — {{ f.text }}
{% endfor %}
## Themes
{% for t in themes -%}
- **{{ t.name }}** — {{ t.gist }}
{% endfor -%}
{% for m in materials %}
---

## {{ m.title or m.name }}

{{ m.kind or "material" }} · {{ m.state }} · {{ m.derivation }}
{% if m.people -%}
People: {% for p in m.people %}{{ p.name }}{% if p.aliases %} ({{ p.aliases }}){% endif %}{% if p.role %} — {{ p.role }}{% endif %}{% if not loop.last %}; {% endif %}{% endfor %}
{% endif -%}
{% if m.speakers -%}
Speaking: {% for s in m.speakers %}{{ s.label }}{% if s.name %} = {{ s.name }}{% endif %}{% if s.role %} ({{ s.role }}){% endif %}{% if not loop.last %}; {% endif %}{% endfor %}
{% endif -%}
{% if m.orientation %}
### What this is

{{ m.orientation.text }}
{% endif -%}
{% if m.reading %}
### What the reading found

{{ m.reading.text }}
{% endif -%}
{% for th in m.threads %}
### {{ th.theme.name }}{% if th.theme.gist %} — {{ th.theme.gist }}{% endif %}

{% for x in th.moments -%}
{{ loop.index }}. {{ x.claim }}
   > {{ x.anchor }}  [{{ x.sid }}]
{% endfor -%}
{% endfor -%}
{% endfor %}
---

## Checks
{% for k in checks %}
- {{ k.created_at }} — {{ k.question }}
  verdict: {{ k.verdict }}, searched {{ k.searched_n }} passages
{% for a in k.anchors -%}
  > {{ a.anchor }}{% if a.sid %}  [{{ a.sid }}]{% endif %}
{% endfor -%}
{% else %}
None.
{% endfor %}
## What the researcher said
{% for f in feedback %}
- {{ f.created_at }} — {{ f.kind }} on {{ f.target_kind }} {{ f.target_id }}{% if f.text %}: {{ f.text }}{% endif %}
{% else %}
Nothing yet.
{% endfor %}
## Runs
{% for r in runs %}
- {{ r.kind }}{% if r.material_id %} ({{ r.material_id }}){% endif %} — {{ r.provider }} / {{ r.model }} — {{ r.tokens_in }} in, {{ r.tokens_out }} out — {{ r.started }}{% if r.finished %} to {{ r.finished }}{% endif %}{% if r.error %} — failed: {{ r.error }}{% endif %}{% if r.line %} — {{ r.line }}{% endif %}
{% else %}
None.
{% endfor %}
