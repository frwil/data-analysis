/* Application chèques & listings — comportements :
   - rendu des codes QR (chaîne signée Ed25519 -> QRCode, même QR pour chèque et listing) ;
   - sélecteur de clients : modes « Tous / Un / Liste », filtre, compteur. */
document.addEventListener('DOMContentLoaded', function () {

  /* ---- Codes QR ---- */
  if (typeof QRCode !== 'undefined') {
    document.querySelectorAll('.qr[data-qr]').forEach(function (el) {
      var taille = Math.max(el.clientWidth, 64);
      new QRCode(el, {
        text: el.getAttribute('data-qr'),
        width: taille,
        height: taille,
        correctLevel: QRCode.CorrectLevel.M
      });
    });
  }

  /* ---- Formulaire ---- */
  var form = document.getElementById('filtres');
  if (!form) { return; }

  var picker = document.getElementById('picker');
  var filtre = document.getElementById('filtre');
  var compteur = document.getElementById('compteur');
  var listes = document.getElementById('liste-clients');
  var radios = form.querySelectorAll('input[name="sel"]');
  var idHidden = form.querySelector('input[name="id"]');
  var idsHidden = form.querySelector('input[name="ids"]');
  var btnTous = document.getElementById('btn-tous');
  var btnAucun = document.getElementById('btn-aucun');

  function mode() {
    for (var i = 0; i < radios.length; i++) {
      if (radios[i].checked) { return radios[i].value; }
    }
    return 'tous';
  }

  function choixs() {
    return listes.querySelectorAll('input[name="choix[]"]');
  }

  function coches() {
    return Array.prototype.filter.call(choixs(), function (c) { return c.checked; });
  }

  function majCompteur() {
    var n = coches().length;
    compteur.textContent = n === 0 ? 'Aucun client sélectionné'
      : (n === 1 ? '1 client sélectionné' : n + ' clients sélectionnés');
  }

  function majPicker() {
    var m = mode();
    picker.hidden = (m === 'tous');
    if (btnTous && btnAucun) {
      var un = (m === 'un');
      btnTous.disabled = un;
      btnAucun.disabled = un;
      btnTous.style.opacity = un ? '.45' : '';
      btnAucun.style.opacity = un ? '.45' : '';
    }
  }

  Array.prototype.forEach.call(radios, function (r) {
    r.addEventListener('change', majPicker);
  });

  /* En mode « Un client » : un seul choix possible */
  listes.addEventListener('change', function (ev) {
    var t = ev.target;
    if (t.type === 'checkbox' && t.checked && mode() === 'un') {
      Array.prototype.forEach.call(choixs(), function (c) {
        if (c !== t) { c.checked = false; }
      });
    }
    majCompteur();
  });

  /* Filtre par code, nom ou agence */
  filtre.addEventListener('input', function () {
    var q = filtre.value.trim().toLowerCase();
    Array.prototype.forEach.call(listes.querySelectorAll('label[data-q]'), function (lab) {
      lab.style.display = (!q || lab.getAttribute('data-q').indexOf(q) !== -1) ? '' : 'none';
    });
  });

  btnTous.addEventListener('click', function () {
    Array.prototype.forEach.call(choixs(), function (c) { c.checked = true; });
    majCompteur();
  });
  btnAucun.addEventListener('click', function () {
    Array.prototype.forEach.call(choixs(), function (c) { c.checked = false; });
    majCompteur();
  });

  /* À l'envoi : renseigner id / ids selon le mode, et retirer choix[] de l'URL */
  form.addEventListener('submit', function () {
    var m = mode();
    var c = coches();
    idHidden.value = (m === 'un' && c.length) ? c[0].value : '';
    idsHidden.value = (m === 'liste') ? c.map(function (x) { return x.value; }).join(',') : '';
    if (m === 'tous') { idHidden.value = ''; idsHidden.value = ''; }
    Array.prototype.forEach.call(choixs(), function (ch) { ch.disabled = true; });
  });

  majPicker();
  majCompteur();
});
