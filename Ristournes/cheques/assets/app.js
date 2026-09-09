/* Application chèques & listings — comportements :
   - rendu des codes QR (chaîne signée Ed25519 -> QRCode, même QR pour chèque et listing) ;
   - sélecteur de clients : modes « Tous / Un / Liste », filtre, compteur. */
document.addEventListener('DOMContentLoaded', function () {

  /* ---- Codes QR ---- */
  function rendreQrs() {
    if (typeof QRCode === 'undefined') { return; }
    document.querySelectorAll('.qr[data-qr]').forEach(function (el) {
      el.innerHTML = '';
      /* ×4 : bitmap haute résolution — à l'impression le QR (18 mm) est
         rendu net, au lieu d'être étiré depuis ~68 px */
      var taille = Math.max(el.clientWidth, 64) * 4;
      new QRCode(el, {
        text: el.getAttribute('data-qr'),
        width: taille,
        height: taille,
        /* Niveau H (≈ 30 % de redondance) : couvre la surface masquée par le
           filigrane « BELGOCAM SA » — le code reste décodable (jsQR testé) */
        correctLevel: QRCode.CorrectLevel.H
      });
    });
  }
  rendreQrs();

  /* =============================================================
   * Suivi des impressions (aperçu / impression)
   * Le navigateur ne peut PAS détecter la réussite physique d'une
   * impression (beforeprint/afterprint se déclenchent même sur
   * « Annuler ») : après chaque impression, une boîte de dialogue
   * demande le résultat. Lots : boucle guidée client par client ;
   * Ctrl+P est intercepté ; le menu Fichier > Imprimer est couvert
   * par un filet afterprint (confirmation du lot entier).
   * Garde file:// : la page du PDF headless inline le même app.js
   * — sans la garde, elle lancerait fetch/modales et double-compterait.
   * ============================================================= */
  if (location.protocol !== 'file:') {

    var etat = 'idle';        // idle | impression | confirmation | suivant
    var feuilleActive = -1;
    var bilan = null;

    var feuilles = function () {
      return Array.prototype.slice.call(document.querySelectorAll('.feuille'));
    };

    /* uuid d'une feuille : déduits de ses documents (chèque + listing
       partagent le même uuid ; en mode « chèques seuls », une feuille
       porte 2 clients distincts — d'où le dédoublonnage). */
    function feuilleInfos(f) {
      var uuids = [], labels = [];
      Array.prototype.forEach.call(f.querySelectorAll('.doc[data-uuid]'), function (d) {
        var u = d.getAttribute('data-uuid');
        if (uuids.indexOf(u) === -1) { uuids.push(u); }
        labels.push(d.getAttribute('data-tiers') || '');
      });
      return { uuids: uuids, labels: labels };
    }

    function tousUuids() {
      var uuids = [];
      feuilles().forEach(function (f) {
        feuilleInfos(f).uuids.forEach(function (u) {
          if (uuids.indexOf(u) === -1) { uuids.push(u); }
        });
      });
      return uuids;
    }

    /* ---- API suivi (POST JSON) — silencieuse en cas d'échec réseau ---- */
    function api(payload, ok) {
      fetch('index.php?p=suivi_api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(function (r) { return r.json(); })
      .then(function (r) { if (ok) { ok(r); } })
      .catch(function () { /* ne pas bloquer l'utilisateur */ });
    }

    function logUuids(uuids, type, statut, ok) {
      api({ action: 'log_lot', type: type, statut: statut, uuids: uuids }, ok);
    }

    /* ---- Modale de confirmation (non fermable hors choix) ---- */
    function ouvrirModale(titre, lignes, boutons) {
      var ov = document.createElement('div');
      ov.className = 'modal-impression';
      var pan = document.createElement('div');
      pan.className = 'modal-panneau';
      var t = document.createElement('div');
      t.className = 'modal-titre';
      t.textContent = titre;
      pan.appendChild(t);
      (lignes || []).forEach(function (l) {
        var d = document.createElement('div');
        d.className = 'modal-texte';
        d.textContent = l;
        pan.appendChild(d);
      });
      var bar = document.createElement('div');
      bar.className = 'modal-boutons';
      boutons.forEach(function (b) {
        var btn = document.createElement('button');
        btn.className = 'btn-modal ' + (b.classe || '');
        btn.textContent = b.label;
        btn.addEventListener('click', function () {
          ov.parentNode.removeChild(ov);
          b.action();
        });
        bar.appendChild(btn);
      });
      pan.appendChild(bar);
      ov.appendChild(pan);
      document.body.appendChild(ov);
    }

    /* ---- Boucle guidée client par client ---- */
    function marquerActive(i, fs) {
      fs.forEach(function (f, k) {
        f.classList.toggle('impression-active', k === i);
      });
    }

    function imprimerFeuille(i, fs) {
      feuilleActive = i;
      marquerActive(i, fs);
      etat = 'impression';
      /* window.print() est bloquant (Chrome/Edge) : la modale étape 1
         ne s'ouvre qu'à la fermeture de la boîte d'impression.
         setTimeout(0) : jamais d'appel ré-entrant depuis un clic. */
      setTimeout(function () {
        window.print();
        etapeResultat(i, fs);
      }, 0);
    }

    function etapeResultat(i, fs) {
      etat = 'confirmation';
      var infos = feuilleInfos(fs[i]);
      var suite = function () { apresReponse(i, fs); };
      ouvrirModale('Feuille ' + (i + 1) + ' / ' + fs.length, [
        'L\'impression de « ' + infos.labels.join(' · ') + ' »',
        's\'est-elle bien déroulée ?'
      ], [
        { label: '✅ Réussie', classe: 'ok', action: function () {
            logUuids(infos.uuids, 'directe', 'reussi'); bilan.reussi++; suite();
          } },
        { label: '❌ Échouée', classe: 'ko', action: function () {
            logUuids(infos.uuids, 'directe', 'echoue'); bilan.echoue++; suite();
          } },
        { label: '🚫 Annulée', classe: 'neutre', action: function () {
            logUuids(infos.uuids, 'directe', 'annulee'); bilan.annulee++; suite();
          } }
      ]);
    }

    function apresReponse(i, fs) {
      if (i + 1 < fs.length) {
        etat = 'suivant';
        ouvrirModale('Client suivant', [
          'Passer au client suivant ? (feuille ' + (i + 2) + ' / ' + fs.length + ')'
        ], [
          { label: '➡ Suivant', classe: 'ok', action: function () { imprimerFeuille(i + 1, fs); } },
          { label: '⏹ Arrêter', classe: 'neutre', action: finImpression }
        ]);
      } else {
        finImpression();
      }
    }

    function finImpression() {
      document.body.classList.remove('mode-lot');
      feuilles().forEach(function (f) { f.classList.remove('impression-active'); });
      feuilleActive = -1;
      etat = 'idle';
      var b = bilan;
      bilan = null;
      var lignes = [b.reussi + ' réussie(s) · ' + b.echoue + ' échouée(s) · ' + b.annulee + ' annulée(s).'];
      if (b.echoue > 0 || b.annulee > 0) {
        lignes.push('Les compteurs peuvent être corrigés dans « Suivi des impressions ».');
      }
      ouvrirModale('Impression terminée', lignes, [
        { label: 'OK', classe: 'ok', action: function () {} }
      ]);
    }

    function lancerImpression() {
      if (etat !== 'idle') { return; }
      var fs = feuilles();
      if (!fs.length) { return; }
      document.body.classList.add('mode-lot');
      bilan = { reussi: 0, echoue: 0, annulee: 0 };
      imprimerFeuille(0, fs);
    }
    window.lancerImpression = lancerImpression; // bouton de la barre d'outils

    /* ---- Filet « impression hors boucle » (menu Fichier > Imprimer…) ----
       Impressions possibles mais non guidées : après fermeture de la boîte,
       on demande une confirmation pour le lot entier. Aucun double comptage :
       la boucle guidée pose etat ≠ idle pendant window.print(). */
    window.addEventListener('beforeprint', function () {
      if (etat !== 'idle' && feuilleActive >= 0) {
        /* préview synchrone : une seule feuille visible, même si
           l'impression est déclenchée par un autre chemin */
        document.body.classList.add('mode-lot');
        marquerActive(feuilleActive, feuilles());
      }
    });

    window.addEventListener('afterprint', function () {
      if (etat !== 'idle' || !feuilles().length) { return; }
      var fs = feuilles();
      ouvrirModale('Impression du lot (' + fs.length + ' feuille(s))', [
        'L\'impression s\'est-elle bien déroulée ?'
      ], [
        { label: '✅ Réussie', classe: 'ok', action: function () {
            logUuids(tousUuids(), 'directe', 'reussi');
          } },
        { label: '❌ Échouée', classe: 'ko', action: function () {
            logUuids(tousUuids(), 'directe', 'echoue');
          } },
        { label: '🚫 Annulée', classe: 'neutre', action: function () {
            logUuids(tousUuids(), 'directe', 'annulee');
          } }
      ]);
    });

    /* ---- Ctrl+P : boucle guidée (état idle uniquement) ---- */
    document.addEventListener('keydown', function (ev) {
      if ((ev.ctrlKey || ev.metaKey) && String(ev.key).toLowerCase() === 'p'
          && etat === 'idle' && feuilles().length) {
        ev.preventDefault();
        lancerImpression();
      }
    });

    /* ---- Téléchargement PDF : fetch → blob → confirmation d'impression ---- */
    document.addEventListener('click', function (ev) {
      var a = ev.target && ev.target.closest ? ev.target.closest('a[data-action-pdf]') : null;
      if (!a) { return; }
      ev.preventDefault();
      var annee = a.getAttribute('data-nom') || 'annee';
      fetch(a.href)
        .then(function (r) {
          if (!r.ok) { throw new Error('HTTP ' + r.status); }
          return r.blob();
        })
        .then(function (blob) {
          var url = URL.createObjectURL(blob);
          var tmp = document.createElement('a');
          tmp.href = url;
          tmp.download = 'Ristournes_' + annee + '_BLP.pdf';
          document.body.appendChild(tmp);
          tmp.click();
          tmp.remove();
          setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
          var uuids = tousUuids();
          ouvrirModale('PDF téléchargé', ['Le PDF a-t-il été imprimé ?'], [
            { label: '✅ Oui', classe: 'ok', action: function () {
                logUuids(uuids, 'pdf', 'reussi');
              } },
            { label: '❌ Non', classe: 'neutre', action: function () {
                logUuids(uuids, 'pdf', 'annulee');
              } }
          ]);
        })
        .catch(function () {
          alert('La génération du PDF a échoué.');
        });
    });

    /* ---- p=imprimer : démarrage guidé dès que la page est prête ---- */
    if (window.__autoPrint) {
      setTimeout(lancerImpression, 250);
    }

    /* ---- Badges du formulaire : suivre l'année sélectionnée ---- */
    var selAnnee = document.querySelector('select[name="annee"]');
    var badges = Array.prototype.slice.call(document.querySelectorAll('.imp[data-imp]'));
    function badgeTexte(s) {
      /* toujours visible — identique au rendu PHP badge_imp() */
      var d = s ? (s.directe || 0) : 0;
      var x = s ? (s.echecs || 0) : 0;
      var p = s ? (s.pdf || 0) : 0;
      var t = '🖨' + d + ' 📄' + p;
      if (x > 0) { t += ' ✗' + x; }
      return t;
    }
    function majBadges() {
      var annee = selAnnee ? selAnnee.value : '';
      badges.forEach(function (b) {
        var data = {};
        try { data = JSON.parse(b.getAttribute('data-imp') || '{}'); } catch (e) { /* ignore */ }
        var s = data[annee] || null;
        b.textContent = badgeTexte(s);
        b.classList.toggle('imp-alerte', !!(s && s.echecs > 0));
        /* Bouton « ✓ imprimé » : visible seulement quand les compteurs sont à 0 */
        var btn = b.parentElement ? b.parentElement.querySelector('.btn-imprime') : null;
        if (btn) {
          btn.setAttribute('data-annee', annee);
          btn.hidden = !!(s && ((s.directe || 0) > 0 || (s.pdf || 0) > 0));
        }
      });
    }
    if (selAnnee && badges.length) {
      selAnnee.addEventListener('change', majBadges);
    }
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
  var btnZero = document.getElementById('btn-zero');
  /* Nombre de clients correspondant au filtre courant (0 = pas de filtre actif) */
  var nbCorrespond = 0;

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
    if (nbCorrespond > 0) {
      compteur.textContent = nbCorrespond
        + (nbCorrespond === 1 ? ' client correspond au filtre' : ' clients correspondent au filtre')
        + (n === 0 ? ' — aucun sélectionné' : (n === 1 ? ' — 1 sélectionné' : ' — ' + n + ' sélectionnés'));
      return;
    }
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
      if (btnZero) {
        btnZero.disabled = un;
        btnZero.style.opacity = un ? '.45' : '';
      }
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

  /* Filtre par code, nom ou agence : masque les lignes hors filtre et
     sélectionne automatiquement les clients qui correspondent —
     tous en mode « Liste », le premier en mode « Un client ».
     La sélection suit le filtre : les clients qui ne correspondent
     plus sont décochés. */
  filtre.addEventListener('input', function () {
    var q = filtre.value.trim().toLowerCase();
    var un = (mode() === 'un');
    nbCorrespond = 0;
    var premier = true;
    Array.prototype.forEach.call(listes.querySelectorAll('label[data-q]'), function (lab) {
      var ok = !q || lab.getAttribute('data-q').indexOf(q) !== -1;
      lab.style.display = ok ? '' : 'none';
      if (!q) { return; }
      var c = lab.querySelector('input[name="choix[]"]');
      if (!c) { return; }
      if (ok) {
        nbCorrespond++;
        c.checked = !un || premier;
        premier = false;
      } else {
        c.checked = false;
      }
    });
    majCompteur();
  });

  btnTous.addEventListener('click', function () {
    Array.prototype.forEach.call(choixs(), function (c) { c.checked = true; });
    majCompteur();
  });
  btnAucun.addEventListener('click', function () {
    Array.prototype.forEach.call(choixs(), function (c) { c.checked = false; });
    majCompteur();
  });

  /* « Non imprimés » : ne cocher que les clients dont les compteurs
     d'impression sont à 0 (directe et PDF) pour l'année choisie.
     Quand le filtre de recherche est actif, la sélection se limite
     aux clients qui correspondent au filtre (ex. un dépôt) : les
     clients hors filtre sont décochés.
     Les échecs/annulations laissent le compteur à 0 : le client
     reste sélectionnable, car il reste à imprimer. */
  btnZero.addEventListener('click', function () {
    var annee = selAnnee ? selAnnee.value : '';
    var q = filtre.value.trim().toLowerCase();
    var n = 0;
    Array.prototype.forEach.call(choixs(), function (c) {
      var lab = c.closest('label');
      var ok = !q || (lab && lab.getAttribute('data-q').indexOf(q) !== -1);
      if (!ok) { c.checked = false; return; }
      var b = lab ? lab.querySelector('.imp[data-imp]') : null;
      var data = {};
      if (b) { try { data = JSON.parse(b.getAttribute('data-imp') || '{}'); } catch (e) { /* ignore */ } }
      var s = data[annee] || null;
      var zero = !s || ((s.directe || 0) === 0 && (s.pdf || 0) === 0);
      c.checked = zero;
      if (zero) { n++; }
    });
    majCompteur();
    if (!n) {
      alert(q
        ? 'Aucun client non imprimé parmi les résultats du filtre pour l\'année ' + annee + '.'
        : 'Aucun client non imprimé pour l\'année ' + annee + '.');
    }
  });

  /* « ✓ imprimé » : marquer le client comme déjà imprimé (+1 🖨 directe)
     — pour corriger un client imprimé qui ressort à 0 dans « Non imprimés ».
     Écriture d'audit dans le journal (note « marqué manuellement »). */
  listes.addEventListener('click', function (ev) {
    var btn = ev.target && ev.target.closest ? ev.target.closest('.btn-imprime') : null;
    if (!btn) { return; }
    ev.preventDefault();
    ev.stopPropagation();
    btn.disabled = true;
    fetch('index.php?p=suivi_api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'marquer',
        tiers: btn.getAttribute('data-tiers'),
        agence: btn.getAttribute('data-agence'),
        annee: parseInt(btn.getAttribute('data-annee'), 10)
      })
    }).then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.ok) {
          alert('Marquage impossible : ' + (res.message || 'erreur inconnue'));
          btn.disabled = false;
          return;
        }
        /* Mettre à jour le badge de la ligne avec les compteurs renvoyés */
        var lab = btn.closest('label');
        var b = lab ? lab.querySelector('.imp[data-imp]') : null;
        if (b) {
          var data = {};
          try { data = JSON.parse(b.getAttribute('data-imp') || '{}'); } catch (e) { /* ignore */ }
          var annee = btn.getAttribute('data-annee');
          if (!data[annee]) { data[annee] = { directe: 0, pdf: 0, echecs: 0 }; }
          data[annee].directe = res.compteurs.directe;
          data[annee].pdf = res.compteurs.pdf;
          b.setAttribute('data-imp', JSON.stringify(data));
          b.textContent = badgeTexte(data[annee] || null);
          b.classList.toggle('imp-alerte', !!((data[annee] || {}).echecs > 0));
        }
        btn.hidden = true; /* compteur > 0 : le bouton disparaît */
        var c = lab ? lab.querySelector('input[name="choix[]"]') : null;
        if (c) { c.checked = false; }
        majCompteur();
      })
      .catch(function () {
        alert('Erreur réseau — marquage non appliqué.');
        btn.disabled = false;
      });
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
