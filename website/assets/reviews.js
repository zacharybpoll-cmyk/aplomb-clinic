// APLOMB. — PDP reviews module
//
// Loaded on the four PDPs (serum, roots, calm, breath). Finds the
// [data-reviews="<key>"] section, asks /api/reviews for *published* reviews
// only, and renders them. Honest by construction:
//   * Never fabricates a rating or a count.
//   * If there are no published reviews and the visitor has no review token,
//     the whole section stays hidden — we show an empty widget to nobody.
//   * The submission form only appears when the T+10-day email's signed ?rt=
//     token is present, and the server re-verifies it; the browser is never
//     trusted to assert "I bought this".
//
// Framework-free, no external deps, no animation (reduced-motion safe). All
// user-supplied text is written via textContent — never innerHTML.

(function () {
  'use strict';

  const section = document.querySelector('[data-reviews]');
  if (!section) return;

  const productKey = section.getAttribute('data-reviews');
  if (!productKey) return;

  const rt = new URLSearchParams(window.location.search).get('rt');

  const headEl = section.querySelector('[data-reviews-head]');
  const listEl = section.querySelector('[data-reviews-list]');
  const emptyEl = section.querySelector('[data-reviews-empty]');
  const formEl = section.querySelector('[data-reviews-form]');

  function starString(n) {
    const full = Math.round(n);
    let s = '';
    for (let i = 1; i <= 5; i++) s += i <= full ? '★' : '☆';
    return s;
  }

  function fmtDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d)) return '';
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
  }

  function renderHead(count, avg) {
    headEl.textContent = '';
    if (!count) return;
    const stars = document.createElement('span');
    stars.className = 'reviews-stars';
    stars.setAttribute('aria-hidden', 'true');
    stars.textContent = starString(avg);
    const label = document.createElement('span');
    label.className = 'reviews-avg';
    label.textContent =
      avg.toFixed(1) + ' · ' + count + (count === 1 ? ' verified review' : ' verified reviews');
    headEl.setAttribute(
      'aria-label',
      'Rated ' + avg.toFixed(1) + ' out of 5 from ' + count + ' verified ' +
        (count === 1 ? 'review' : 'reviews')
    );
    headEl.appendChild(stars);
    headEl.appendChild(label);
  }

  function renderList(items) {
    listEl.textContent = '';
    items.forEach(function (r) {
      const card = document.createElement('article');
      card.className = 'review';

      const top = document.createElement('div');
      top.className = 'review-top';
      const st = document.createElement('span');
      st.className = 'reviews-stars';
      st.setAttribute('aria-hidden', 'true');
      st.textContent = starString(r.rating);
      const sr = document.createElement('span');
      sr.className = 'sr-only';
      sr.textContent = r.rating + ' out of 5';
      top.appendChild(st);
      top.appendChild(sr);
      card.appendChild(top);

      if (r.title) {
        const h = document.createElement('div');
        h.className = 'review-title';
        h.textContent = r.title;
        card.appendChild(h);
      }

      const b = document.createElement('p');
      b.className = 'review-body';
      b.textContent = r.body;
      card.appendChild(b);

      const meta = document.createElement('div');
      meta.className = 'review-meta';
      const who = [r.name, fmtDate(r.date)].filter(Boolean).join(' · ');
      meta.textContent = (who ? who + ' · ' : '') + 'Verified buyer';
      card.appendChild(meta);

      listEl.appendChild(card);
    });
  }

  function buildForm() {
    formEl.textContent = '';

    const fs = document.createElement('fieldset');
    fs.className = 'rf-rating';
    const lg = document.createElement('legend');
    lg.textContent = 'Your rating';
    fs.appendChild(lg);
    for (let i = 5; i >= 1; i--) {
      const lab = document.createElement('label');
      const inp = document.createElement('input');
      inp.type = 'radio';
      inp.name = 'rf-rating';
      inp.value = String(i);
      if (i === 5) inp.checked = true;
      const sp = document.createElement('span');
      sp.textContent = i + ' ★';
      lab.appendChild(inp);
      lab.appendChild(sp);
      fs.appendChild(lab);
    }
    formEl.appendChild(fs);

    const title = document.createElement('input');
    title.type = 'text';
    title.placeholder = 'Headline (optional)';
    title.maxLength = 160;
    title.className = 'rf-title';
    formEl.appendChild(title);

    const body = document.createElement('textarea');
    body.placeholder = 'What did it do, or not do? Plain and honest helps most.';
    body.required = true;
    body.rows = 4;
    body.className = 'rf-body';
    formEl.appendChild(body);

    const name = document.createElement('input');
    name.type = 'text';
    name.placeholder = 'First name to show (optional)';
    name.maxLength = 80;
    name.className = 'rf-name';
    formEl.appendChild(name);

    const btn = document.createElement('button');
    btn.type = 'submit';
    btn.className = 'btn btn-dark';
    btn.textContent = 'Submit review';
    formEl.appendChild(btn);

    const note = document.createElement('p');
    note.className = 'rf-note';
    note.setAttribute('data-rf-note', '');
    note.textContent = 'We read every review before it goes up. Nothing is auto-posted.';
    formEl.appendChild(note);

    formEl.addEventListener('submit', function (e) {
      e.preventDefault();
      const note2 = formEl.querySelector('[data-rf-note]');
      btn.disabled = true;
      const ratingEl = formEl.querySelector('input[name="rf-rating"]:checked');
      const payload = {
        rt: rt,
        product: productKey,
        rating: ratingEl ? parseInt(ratingEl.value, 10) : 0,
        title: title.value.trim(),
        body: body.value.trim(),
        name: name.value.trim(),
      };
      fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
        .then(function (res) {
          return res.json().then(function (j) {
            return { ok: res.ok, j: j };
          });
        })
        .then(function (r) {
          if (r.ok && r.j && r.j.ok) {
            formEl.textContent = '';
            const done = document.createElement('p');
            done.className = 'rf-done';
            done.textContent =
              r.j.status === 'duplicate'
                ? 'You have already reviewed this — thank you.'
                : 'Thank you. Your review is in; we read every one before it goes up.';
            formEl.appendChild(done);
            // Strip the one-time token so a refresh does not look re-submittable.
            try {
              const u = new URL(window.location.href);
              u.searchParams.delete('rt');
              window.history.replaceState({}, '', u.toString());
            } catch (_) {}
          } else {
            btn.disabled = false;
            note2.textContent =
              (r.j && r.j.error) || 'Could not submit just now. Please try again.';
            note2.classList.add('is-error');
          }
        })
        .catch(function () {
          btn.disabled = false;
          note2.textContent = 'Could not submit just now. Please try again.';
          note2.classList.add('is-error');
        });
    });
  }

  fetch('/api/reviews?product=' + encodeURIComponent(productKey))
    .then(function (res) {
      return res.ok ? res.json() : { count: 0, avg: null, items: [] };
    })
    .catch(function () {
      return { count: 0, avg: null, items: [] };
    })
    .then(function (data) {
      const count = (data && data.count) || 0;
      const items = (data && data.items) || [];

      // Show nothing when there is nothing to show and no one is here to write
      // one. No empty widget, no fabricated content.
      if (!count && !rt) return;

      section.hidden = false;

      if (count) {
        renderHead(count, data.avg || 0);
        renderList(items);
        if (emptyEl) emptyEl.hidden = true;
      } else if (emptyEl) {
        emptyEl.hidden = false;
      }

      if (rt && formEl) {
        formEl.hidden = false;
        buildForm();
      }
    });
})();
