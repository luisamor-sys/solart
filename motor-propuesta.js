/* ============================================================================
   MOTOR DE PROPUESTAS SOLART — port a JavaScript del paquete Python
   solart-propuestas (src/solart_propuestas). Cálculo puro, sin dependencias.

   Reglas confirmadas con Daniel / Ingeniería:
   - Módulo JA Solar 645 W · inversores Solis (Huawei opcional) · tope 499 kW AC
   - Ratio DC/AC máximo 1.35 · PR calibrado 0.755
   - Margen: el mayor posible que cierre el crédito en <= 72 meses (ideal 60),
     con piso de margen de mercado por tamaño (20/18/17 %)
   - Precio al cliente con el FIX; costo convertido con FIX menos $0.10 (colchón)
   ========================================================================== */
(function (global) {
  'use strict';

  // ── Constantes del catálogo (catalogos/equipos.py) ──────────────────────
  var POT_MODULO_W = 645;
  var RATIO_DC_AC_MAX = 1.35;
  var TOPE_AC_KW = 499;
  var OM_USD_POR_MODULO = 13.0;
  var DEMANDA_UMBRAL_VOLTAJE_KW = 200;
  var FP_UMBRAL_BC = 0.90;

  var INVERSORES = [
    { modelo: 'Solis-124K-HV-5G', marca: 'Solis', kwAc: 124, voltaje: 480 },
    { modelo: 'Solis-60K-LV-5G', marca: 'Solis', kwAc: 60, voltaje: 220 },
    { modelo: 'HWI-SUN2000-150K', marca: 'Huawei', kwAc: 150, voltaje: 480 },
    { modelo: 'Solis-30K-LV-5G', marca: 'Solis', kwAc: 30, voltaje: 220 }
  ];

  var MEDIDORES = [
    { modelo: 'KL2R', tarifa: 'GDMTO', demandaMin: 0, usd: 2080 },
    { modelo: 'VL2R', tarifa: 'GDMTH', demandaMin: 0, usd: 2080 },
    { modelo: 'VM2Y', tarifa: 'GDMTH', demandaMin: 750, usd: 15900 },
    { modelo: 'ION 8650-A', tarifa: 'DIST', demandaMin: 0, usd: 22740 }
  ];

  // ── Constantes de generación (motor/generacion.py) ──────────────────────
  var DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  var PR_CALIBRADO = 0.755;

  // ── Constantes de precio (motor/precio.py) ──────────────────────────────
  var TASA_ANUAL = 0.14;
  var PLAZO_IDEAL = 60, PLAZO_MAX = 72;
  var MARGEN_MIN = 0.10, MARGEN_MAX = 0.25;
  var TASA_ISR = 0.30, TASA_IVA = 0.16;
  var PLAZO_CORPUS = 48, HOLGURA_PAGO = 0.90;
  var FACTOR_COSTO_HUAWEI = 0.83;
  var USD_POR_KVAR_BANCO = 49.4;
  var COLCHON_TC = 0.10;
  var CURVA_COSTO_220 = [[34.56, 0.930], [354.75, 0.637]];
  var CURVA_COSTO_480 = [[165.0, 0.624], [376.70, 0.570], [636.0, 0.540]];

  var DATOS = null; // se inyecta con cargarDatos()

  // ── Utilidades ──────────────────────────────────────────────────────────
  function norm(s) {
    return String(s == null ? '' : s).normalize('NFD').replace(/[̀-ͯ]/g, '').trim().toLowerCase();
  }
  function diasDelMes(anio, mes) { return new Date(anio, mes, 0).getDate(); }
  function domingosDelMes(anio, mes) {
    var n = diasDelMes(anio, mes), c = 0;
    for (var d = 1; d <= n; d++) if (new Date(anio, mes - 1, d).getDay() === 0) c++;
    return c;
  }
  function r2(x) { return Math.round(x * 100) / 100; }

  // ── Datos (tarifas CNE, HSP, divisiones) ────────────────────────────────
  function cargarDatos(d) { DATOS = d; }

  function divisionDe(estado, municipio) {
    if (!DATOS) throw new Error('Datos no cargados');
    var mun = DATOS.municipios[estado];
    if (mun) {
      if (mun[municipio] != null) return DATOS.divisiones[mun[municipio]];
      var nm = norm(municipio);
      for (var k in mun) if (norm(k) === nm) return DATOS.divisiones[mun[k]];
    }
    // Fallback: buscar el municipio en cualquier estado si la división es única
    var encontradas = {};
    for (var e in DATOS.municipios) {
      for (var m in DATOS.municipios[e]) {
        if (norm(m) === norm(municipio)) encontradas[DATOS.municipios[e][m]] = 1;
      }
    }
    var idxs = Object.keys(encontradas);
    if (idxs.length === 1) return DATOS.divisiones[idxs[0]];
    return null;
  }

  // Cargos de un mes; retrocede hasta 13 meses si ese periodo no está publicado
  function cargosDe(division, tarifa, anio, mes) {
    var a = anio, m = mes;
    for (var i = 0; i < 14; i++) {
      var c = DATOS.cargos[division + '|' + tarifa + '|' + a + '-' + (m < 10 ? '0' : '') + m];
      if (c) {
        return {
          suministro: c.s || 0, transmision: c.t || 0, cenace: c.c || 0, scnmem: c.m || 0,
          distribucion: c.d || 0, capacidad: c.k || 0, generacion: c.g || {}, anio: anio, mes: mes
        };
      }
      m--; if (m === 0) { m = 12; a--; }
    }
    return null;
  }

  // ── 1. GENERACIÓN (motor/generacion.py) ─────────────────────────────────
  function hspDe(lugar) {
    var lug = norm(lugar), k;
    for (k in DATOS.hsp) if (norm(k) === lug) return DATOS.hsp[k];
    for (k in DATOS.hsp) { var nk = norm(k); if (nk.indexOf(lug) >= 0 || lug.indexOf(nk) >= 0) return DATOS.hsp[k]; }
    return null;
  }
  function perfilMensualDe(lugar) {
    var lug = norm(lugar), k;
    for (k in DATOS.perfil) if (norm(k) === lug) return DATOS.perfil[k];
    for (k in DATOS.perfil) { var nk = norm(k); if (nk.indexOf(lug) >= 0 || lug.indexOf(nk) >= 0) return DATOS.perfil[k]; }
    return null;
  }
  function generacionMensual(kwp, lugar, pr) {
    pr = pr || PR_CALIBRADO;
    var hsp = hspDe(lugar);
    if (!hsp) throw new Error('Sin datos de radiación para: ' + lugar);
    var suma = 0, i;
    for (i = 0; i < 12; i++) suma += hsp[i] * DIAS_MES[i];
    var anual = kwp * pr * suma;
    var forma = perfilMensualDe(lugar), out = [];
    for (i = 0; i < 12; i++) {
      out.push(forma ? anual * forma[i] : anual * (hsp[i] * DIAS_MES[i]) / suma);
    }
    return out;
  }
  function kwhPorKwpAnual(lugar, pr) {
    return generacionMensual(1.0, lugar, pr).reduce(function (a, b) { return a + b; }, 0);
  }

  // ── 2. DIMENSIONADO (motor/dimensionado.py) ─────────────────────────────
  function seleccionarInversores(kwDcObjetivo, voltaje, marca) {
    var elegibles = INVERSORES.filter(function (inv) {
      return Math.abs(inv.voltaje - voltaje) <= 60 && (!marca || inv.marca.toLowerCase() === String(marca).toLowerCase());
    });
    if (!elegibles.length) throw new Error('Sin inversores para ' + voltaje + 'V');
    var cand = [];
    elegibles.forEach(function (inv) {
      var n = Math.max(1, Math.ceil(kwDcObjetivo / (inv.kwAc * RATIO_DC_AC_MAX)));
      if (n * inv.kwAc > TOPE_AC_KW) return;
      cand.push({ n: n, kwAc: n * inv.kwAc, inv: inv });
    });
    if (cand.length) {
      cand.sort(function (a, b) { return a.n - b.n || a.kwAc - b.kwAc || (a.inv.modelo < b.inv.modelo ? -1 : 1); });
      return cand[0];
    }
    // Ninguno alcanza: el que más capacidad AC permite bajo el tope
    var mejor = null;
    elegibles.forEach(function (inv) {
      var n = Math.floor(TOPE_AC_KW / inv.kwAc), tot = n * inv.kwAc * RATIO_DC_AC_MAX;
      if (!mejor || tot > mejor.tot) mejor = { tot: tot, n: n, inv: inv };
    });
    return { n: mejor.n, kwAc: mejor.n * mejor.inv.kwAc, inv: mejor.inv };
  }

  function dimensionar(o) {
    var avisos = [];
    var pr = o.pr || PR_CALIBRADO;
    var rendimiento = kwhPorKwpAnual(o.lugar, pr);
    var cobertura = o.coberturaObjetivo == null ? 1.0 : o.coberturaObjetivo;
    var kwpObjetivo = o.consumoAnualKwh * cobertura / rendimiento;

    if (o.kwpMaxTecho && kwpObjetivo > o.kwpMaxTecho) {
      kwpObjetivo = o.kwpMaxTecho;
      avisos.push('Limitado por área de techo a ' + Math.round(o.kwpMaxTecho) + ' kWp');
    } else if (!o.kwpMaxTecho) {
      avisos.push('Área de techo no validada: confirmar que el espacio alcanza');
    }

    var voltaje = o.voltaje || 480;
    var marca = o.marca || null;
    var elegibles = INVERSORES.filter(function (inv) {
      return Math.abs(inv.voltaje - voltaje) <= 60 && (!marca || inv.marca.toLowerCase() === String(marca).toLowerCase());
    });
    var kwpTope = 0;
    elegibles.forEach(function (inv) {
      var t = Math.floor(TOPE_AC_KW / inv.kwAc) * inv.kwAc * RATIO_DC_AC_MAX;
      if (t > kwpTope) kwpTope = t;
    });
    if (kwpTope && kwpObjetivo > kwpTope) {
      kwpObjetivo = kwpTope;
      avisos.push('Limitado por tope de 499 kW AC (máx ' + Math.round(kwpTope) + ' kWp DC)');
    }

    var nMods = Math.round(kwpObjetivo * 1000 / POT_MODULO_W);
    var kwpDc = nMods * POT_MODULO_W / 1000;
    var sel = seleccionarInversores(kwpDc, voltaje, marca);
    var ratio = kwpDc / sel.kwAc;

    if (ratio > RATIO_DC_AC_MAX + 1e-9) {
      avisos.push('Ratio DC/AC ' + ratio.toFixed(2) + ' excede el máximo del modelo (1.35)');
    } else if (ratio < 1.10) {
      avisos.push('Ratio DC/AC ' + ratio.toFixed(2) + ': hay capacidad AC de sobra');
    }
    if (o.demandaContratadaKw && sel.kwAc > o.demandaContratadaKw) {
      avisos.push('La capacidad AC (' + sel.kwAc + ' kW) supera la demanda contratada (' +
        o.demandaContratadaKw + ' kW): revisar incremento de demanda con CFE');
    }

    var genAnual = kwpDc * rendimiento;
    return {
      nModulos: nMods, modeloModulo: 'JA-M72D42-645/LB', kwpDc: r2(kwpDc),
      modeloInversor: sel.inv.modelo, marcaInversor: sel.inv.marca, nInversores: sel.n, kwAc: sel.kwAc,
      ratioDcAc: Math.round(ratio * 1000) / 1000, rendimientoKwhKwp: rendimiento,
      generacionAnualKwh: genAnual,
      cobertura: o.consumoAnualKwh > 0 ? Math.min(1.0, genAnual / o.consumoAnualKwh) : 0,
      avisos: avisos
    };
  }

  // ── 3. FACTURA CFE (motor/factura.py) ───────────────────────────────────
  function factorPotencia(c) {
    var tot = (c.kwhBase || 0) + (c.kwhIntermedia || 0) + (c.kwhPunta || 0);
    if (tot <= 0) return 1.0;
    var kv = c.kvarh || 0;
    return tot / Math.sqrt(tot * tot + kv * kv);
  }
  function fpPct(fp) {
    var p = fp * 100;
    if (p < 90) return (3 / 5) * (90 / p - 1);
    return -Math.min((1 / 4) * (1 - 90 / p), 0.025);
  }

  function simularFactura(cargos, c, factorCarga) {
    var kwhBase = c.kwhBase || 0, kwhInt = c.kwhIntermedia || 0, kwhPunta = c.kwhPunta || 0;
    var total = kwhBase + kwhInt + kwhPunta;
    var dias = c.dias || 30;
    var W = total > 0 ? Math.ceil(total / (24 * dias * factorCarga)) : 0;
    var demDist = c.demandaMaxKw ? Math.min(c.demandaMaxKw, W) : W;
    var demCap = c.demandaPuntaKw ? Math.min(c.demandaPuntaKw, W) : W;
    var g = cargos.generacion || {};
    // GDMTO publica la energía bajo "NA" (sin horarios): se cobra sobre el total
    var energia = (g.B != null || g.I != null || g.P != null)
      ? (g.B || 0) * kwhBase + (g.I || 0) * kwhInt + (g.P || 0) * kwhPunta
      : (g.NA || 0) * total;

    var conceptos = {
      'Suministro': cargos.suministro,
      'Transmisión': cargos.transmision * total,
      'CENACE': cargos.cenace * total,
      'SCnMEM': cargos.scnmem * total,
      'Energía': energia,
      'Distribución': cargos.distribucion * demDist,
      'Capacidad': cargos.capacidad * demCap
    };
    var base = 0;
    for (var k in conceptos) base += conceptos[k];
    var fp = factorPotencia(c);
    var fpAplicado = base * fpPct(fp);
    var subtotal = base + fpAplicado;
    var iva = subtotal * TASA_IVA;
    var dap = c.dap || 0;
    return {
      conceptos: conceptos, base: base, fpAplicado: fpAplicado, subtotal: subtotal,
      iva: iva, dap: dap, total: subtotal + iva + dap, demandaFacturable: W, factorPotencia: fp
    };
  }

  function simularFacturaPdbt(subperiodos, dapPct) {
    // subperiodos: [{cargos, kwh}] — todos los cargos son $/kWh en baja tensión
    var c = { 'Suministro': 0, 'Transmisión': 0, 'CENACE': 0, 'SCnMEM': 0, 'Energía': 0, 'Distribución': 0, 'Capacidad': 0 };
    if (subperiodos.length) c['Suministro'] = subperiodos[0].cargos.suministro * 2.0;
    subperiodos.forEach(function (sp) {
      var g = sp.cargos.generacion || {};
      c['Transmisión'] += sp.cargos.transmision * sp.kwh;
      c['CENACE'] += sp.cargos.cenace * sp.kwh;
      c['SCnMEM'] += sp.cargos.scnmem * sp.kwh;
      c['Energía'] += (g.NA != null ? g.NA : (g.B || 0)) * sp.kwh;
      c['Distribución'] += sp.cargos.distribucion * sp.kwh;
      c['Capacidad'] += sp.cargos.capacidad * sp.kwh;
    });
    var subtotal = 0;
    for (var k in c) subtotal += c[k];
    var iva = subtotal * TASA_IVA, dap = subtotal * (dapPct || 0);
    return { conceptos: c, base: subtotal, fpAplicado: 0, subtotal: subtotal, iva: iva, dap: dap, total: subtotal + iva + dap };
  }

  // ── 4. AHORRO: factura con solar (motor/ahorro.py) ──────────────────────
  function consumoConSolar(c, gen, creditoPrevio, anio, mes, conBc) {
    var dias = diasDelMes(anio, mes);
    var fracDom = domingosDelMes(anio, mes) / dias;
    var genBase = gen * fracDom;                       // el domingo entero es horario base
    var genInt = gen - genBase + (creditoPrevio || 0); // el crédito arrastrado va a intermedia

    var baseNet = (c.kwhBase || 0) - genBase;
    var intNet = (c.kwhIntermedia || 0) - genInt;
    var puntaNet = (c.kwhPunta || 0);
    if (intNet < 0) { baseNet += intNet; intNet = 0; }
    if (baseNet < 0) { puntaNet += baseNet; baseNet = 0; }
    var excedente = 0;
    if (puntaNet < 0) { excedente = -puntaNet; puntaNet = 0; }

    var kvarh = c.kvarh || 0;
    var nuevo = {
      kwhBase: baseNet, kwhIntermedia: intNet, kwhPunta: puntaNet,
      demandaMaxKw: c.demandaMaxKw, demandaPuntaKw: c.demandaPuntaKw,
      kvarh: kvarh, dias: c.dias, dap: c.dap
    };
    if (conBc !== false && kvarh > 0) {
      var fpNuevo = factorPotencia(nuevo);
      if (fpNuevo < 0.95) {
        var totalNet = baseNet + intNet + puntaNet;
        var objetivo = totalNet * Math.sqrt(1 / (0.95 * 0.95) - 1);
        nuevo.kvarh = Math.min(kvarh, objetivo);
      }
    }
    return { consumo: nuevo, excedente: excedente };
  }

  function simular12Meses(perfil, division, tarifa, generacion, conBc) {
    var fc = DATOS.factor_carga[tarifa] || 0.57;
    var credito = 0, meses = [], ahorroAnual = 0;
    perfil.forEach(function (p) {
      var cargos = cargosDe(division, tarifa, p.anio, p.mes);
      if (!cargos) throw new Error('Sin tarifas publicadas para ' + division + ' ' + tarifa);
      var gen = generacion[p.mes - 1];
      var sin = simularFactura(cargos, p, fc);
      var res = consumoConSolar(p, gen, credito, p.anio, p.mes, conBc);
      var con = simularFactura(cargos, res.consumo, fc);
      credito = res.excedente;
      var ahorro = sin.total - con.total;
      ahorroAnual += ahorro;
      meses.push({
        anio: p.anio, mes: p.mes, sin: sin.total, con: con.total,
        genKwh: gen, kwhTotal: (p.kwhBase || 0) + (p.kwhIntermedia || 0) + (p.kwhPunta || 0),
        ahorro: ahorro, excedenteKwh: res.excedente
      });
    });
    return { meses: meses, ahorroAnual: ahorroAnual };
  }

  // Perfil de 12 meses a partir de UN recibo (motor/ahorro.py:113)
  function perfilDesdeMesUnico(c, anioFin, mesFin) {
    var diasRef = diasDelMes(anioFin, mesFin), out = [];
    var anio = anioFin, mes = mesFin;
    // 12 meses hacia atrás, terminando en el mes del recibo
    var lista = [];
    for (var i = 0; i < 12; i++) {
      lista.unshift({ anio: anio, mes: mes });
      mes--; if (mes === 0) { mes = 12; anio--; }
    }
    lista.forEach(function (p) {
      var esc = diasDelMes(p.anio, p.mes) / diasRef;
      out.push({
        anio: p.anio, mes: p.mes,
        kwhBase: (c.kwhBase || 0) * esc, kwhIntermedia: (c.kwhIntermedia || 0) * esc,
        kwhPunta: (c.kwhPunta || 0) * esc, kvarh: (c.kvarh || 0) * esc,
        demandaMaxKw: c.demandaMaxKw, demandaPuntaKw: c.demandaPuntaKw,
        dias: diasDelMes(p.anio, p.mes), dap: c.dap || 0
      });
    });
    return out;
  }

  // Perfil a partir de la tabla de histórico del recibo (motor/ahorro.py:141)
  function perfilDesdeHistorico(c, historico) {
    var total = (c.kwhBase || 0) + (c.kwhIntermedia || 0) + (c.kwhPunta || 0);
    if (total <= 0) return null;
    var fb = (c.kwhBase || 0) / total, fi = (c.kwhIntermedia || 0) / total, fpu = (c.kwhPunta || 0) / total;
    var ratioPunta = c.demandaMaxKw ? (c.demandaPuntaKw || c.demandaMaxKw * 0.9) / c.demandaMaxKw : 0.9;
    var kvarhRatio = total > 0 ? (c.kvarh || 0) / total : 0;
    return historico.slice(-12).map(function (h) {
      var kwh = h.kwh || 0;
      return {
        anio: h.anio, mes: h.mes,
        kwhBase: kwh * fb, kwhIntermedia: kwh * fi, kwhPunta: kwh * fpu,
        demandaMaxKw: h.demanda || c.demandaMaxKw,
        demandaPuntaKw: (h.demanda || c.demandaMaxKw || 0) * ratioPunta,
        kvarh: kwh * kvarhRatio, dias: diasDelMes(h.anio, h.mes), dap: c.dap || 0
      };
    });
  }

  // ── 5. PRECIO Y FINANCIAMIENTO (motor/precio.py) ────────────────────────
  function interpolar(curva, x) {
    if (x <= curva[0][0]) return curva[0][1];
    for (var i = 1; i < curva.length; i++) {
      if (x <= curva[i][0]) {
        var x0 = curva[i - 1][0], y0 = curva[i - 1][1], x1 = curva[i][0], y1 = curva[i][1];
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
      }
    }
    return curva[curva.length - 1][1];
  }
  function costoBaseUsdW(kwp, equipo, voltaje) {
    var base = interpolar(voltaje < 440 ? CURVA_COSTO_220 : CURVA_COSTO_480, kwp);
    return String(equipo).toLowerCase() === 'huawei' ? base * FACTOR_COSTO_HUAWEI : base;
  }
  function pagoMensual(monto, tasa, n) {
    var r = tasa / 12;
    return monto * r / (1 - Math.pow(1 + r, -n));
  }
  function plazoParaPago(monto, tasa, pago) {
    var r = tasa / 12;
    if (pago <= monto * r) return Infinity;
    return -Math.log(1 - monto * r / pago) / Math.log(1 + r);
  }
  function margenTabla(kwp) { return kwp <= 300 ? 0.20 : kwp <= 500 ? 0.18 : 0.17; }

  function engancheParaPagoNeutro(precioMxnIva, ahorroMensual, plazo, tasa, holgura) {
    plazo = plazo || PLAZO_CORPUS; tasa = tasa || TASA_ANUAL; holgura = holgura || HOLGURA_PAGO;
    var r = tasa / 12;
    var pagoObj = ahorroMensual * holgura;
    var montoMax = pagoObj * (1 - Math.pow(1 + r, -plazo)) / r;
    var eng = Math.max(0, 1 - montoMax / precioMxnIva);
    return Math.ceil(eng * 20) / 20; // al 5% superior
  }

  function seleccionarMedidor(tarifa, demandaKw) {
    var cands = MEDIDORES.filter(function (m) { return m.tarifa === tarifa && (demandaKw || 0) >= m.demandaMin; });
    if (!cands.length) return null;
    cands.sort(function (a, b) { return b.demandaMin - a.demandaMin; });
    return cands[0];
  }

  function kvarBanco(demandaKw, fpActual, fpObjetivo) {
    fpObjetivo = fpObjetivo || 0.95;
    if (!(demandaKw > 0) || !(fpActual > 0 && fpActual < 1)) return 0;
    var kvar = demandaKw * (Math.tan(Math.acos(fpActual)) - Math.tan(Math.acos(fpObjetivo)));
    return Math.max(25, Math.ceil(kvar / 25) * 25);
  }

  function adicionalesProyecto(nModulos, medidorUsd, kvar, incrementoDemandaUsd) {
    var a = {};
    a['O&M primer año'] = nModulos * OM_USD_POR_MODULO;
    if (medidorUsd) a['Medidor bidireccional'] = medidorUsd;
    if (kvar) a['Banco de capacitores'] = kvar * USD_POR_KVAR_BANCO;
    if (incrementoDemandaUsd) a['Incremento de demanda'] = incrementoDemandaUsd;
    return a;
  }

  function cotizarPrecio(o) {
    var avisos = [];
    var tc = o.tc, tcCosteo = o.tcCosteo || (tc - COLCHON_TC);
    var adicionales = o.adicionalesUsd || 0;
    var costoUsd = costoBaseUsdW(o.kwp, o.equipo, o.voltaje) * o.kwp * 1000 * (tc / tcCosteo) + adicionales;
    var ahorroMensual = o.ahorroAnualMxn / 12;
    var tasa = o.tasa || TASA_ANUAL;

    function plazoAMargen(m) {
      return plazoParaPago(costoUsd / (1 - m) * tc * (1 + TASA_IVA), tasa, ahorroMensual);
    }

    var margen = null;
    var objetivos = [PLAZO_IDEAL, PLAZO_MAX];
    for (var oi = 0; oi < objetivos.length; oi++) {
      var objetivo = objetivos[oi];
      if (plazoAMargen(MARGEN_MIN) > objetivo) continue;
      var lo = MARGEN_MIN, hi = MARGEN_MAX;
      for (var i = 0; i < 40; i++) {
        var mid = (lo + hi) / 2;
        if (plazoAMargen(mid) <= objetivo) lo = mid; else hi = mid;
      }
      margen = Math.max(lo, margenTabla(o.kwp));
      if (objetivo === PLAZO_MAX) {
        avisos.push('No alcanza pago neutro a 60 meses con 0% de enganche; se usó el tope de 72');
      }
      break;
    }
    if (margen == null) {
      margen = margenTabla(o.kwp);
      avisos.push('Pago neutro con 0% de enganche no alcanzable en 72 meses: se aplica margen de mercado ' +
        Math.round(margen * 100) + '% y financiamiento con enganche');
    }
    margen = r2(margen);

    var precioUsd = costoUsd / (1 - margen);
    var precioMxn = precioUsd * tc;
    var precioMxnIva = precioMxn * (1 + TASA_IVA);
    var plazoNeutro = plazoParaPago(precioMxnIva, tasa, ahorroMensual);
    var enganche4a = engancheParaPagoNeutro(precioMxnIva, ahorroMensual, PLAZO_CORPUS, tasa);

    return {
      costoUsd: costoUsd, margen: margen, precioUsd: precioUsd,
      usdW: precioUsd / (o.kwp * 1000), precioMxn: precioMxn, precioMxnIva: precioMxnIva,
      tc: tc, tcCosteo: tcCosteo, equipo: o.equipo, voltaje: o.voltaje,
      markupUsd: precioUsd - costoUsd, markupMxn: (precioUsd - costoUsd) * tc,
      adicionales: o.desgloseAdicionales || {},
      plazoPagoNeutroMeses: isFinite(plazoNeutro) ? plazoNeutro : null,
      enganche4a: enganche4a,
      mensualidad4a: pagoMensual(precioMxnIva * (1 - enganche4a), tasa, PLAZO_CORPUS),
      escenarios: [36, 48, 60].map(function (p) {
        return { anios: p / 12, meses: p, mensualidad: pagoMensual(precioMxnIva, tasa, p) };
      }),
      roiSimple: precioMxn / o.ahorroAnualMxn,
      roiConBf: precioMxn * (1 - TASA_ISR) / o.ahorroAnualMxn,
      avisos: avisos
    };
  }

  // ── 6. SERIES: ROI 25 años y beneficio fiscal (infografia/series.py) ────
  function retornoInversion(precioMxn, precioMxnIva, ahorroAnual, anios) {
    anios = anios || 25;
    var bf = precioMxn * (TASA_ISR + TASA_IVA); // 46%
    var acum = [-precioMxnIva], roi = null;
    for (var i = 1; i <= anios; i++) {
      acum.push(acum[i - 1] + ahorroAnual + (i === 1 ? bf : 0));
      if (roi == null && acum[i] >= 0) {
        roi = (i - 1) + (-acum[i - 1] / (acum[i] - acum[i - 1]));
      }
    }
    return {
      acumulado: acum, roiAnios: roi,
      roiPrimerAnio: (ahorroAnual + bf) / precioMxnIva,
      roiSiguientes: ahorroAnual / precioMxnIva
    };
  }

  function tablaBeneficioFiscal(precioMxn, ahorroAnual) {
    var iva = precioMxn * TASA_IVA;
    var deducible = precioMxn + iva;
    var bfIsr = precioMxn * TASA_ISR;
    var totalBf = bfIsr + iva;
    var costoReal = deducible - totalBf;
    return {
      precio: precioMxn, iva: iva, deducible: deducible, bfIsr: bfIsr,
      totalBf: totalBf, costoReal: costoReal, retornoAnios: costoReal / ahorroAnual
    };
  }

  function pagosProyectados(facturaSinProm, facturaConProm, mensualidad, plazoMeses, anios) {
    anios = anios || 15;
    var out = [], ahorroPeriodo = 0;
    for (var i = 0; i < anios; i++) {
      var f = Math.pow(1.05, i);
      var cfe = facturaSinProm * f;
      var solart = facturaConProm * f + (i * 12 < plazoMeses ? mensualidad : 0);
      ahorroPeriodo += (cfe - solart) * 12;
      out.push({ anio: i + 1, cfe: cfe, solart: solart, cfeAlto: facturaSinProm * Math.pow(1.10, i) });
    }
    return { serie: out, ahorroPeriodo: ahorroPeriodo };
  }

  // ── 7. PIPELINE COMPLETO (pipeline.py::cotizar_proyecto) ────────────────
  function cotizarProyecto(o) {
    var avisos = [];
    var tarifa = String(o.tarifa || 'GDMTH').toUpperCase();
    if (['GDMTH', 'GDMTO', 'PDBT', 'GDBT'].indexOf(tarifa) < 0) {
      return { ok: false, error: 'Tarifa ' + tarifa + ' fuera del caso estándar: canalizar a manual' };
    }
    var division = o.division || divisionDe(o.estado, o.municipio);
    if (!division) return { ok: false, error: 'No se encontró la división tarifaria de ' + o.municipio + ', ' + o.estado };
    var lugar = o.lugarHsp || o.estado;
    if (!hspDe(lugar)) return { ok: false, error: 'Sin datos de radiación para ' + lugar + ': elige la ciudad más cercana' };

    var c = o.consumo || {};
    var esBaja = (tarifa === 'PDBT' || tarifa === 'GDBT');
    var perfil = null, modo = '', consumoAnual = 0;

    if (esBaja) {
      // Baja tensión: bimestres capturados (o uno proyectado)
      var bims = (o.bimestres && o.bimestres.length) ? o.bimestres : [{ kwh: c.kwhTotal || 0 }];
      consumoAnual = bims.length >= 6
        ? bims.slice(-6).reduce(function (s, b) { return s + (b.kwh || 0); }, 0)
        : (bims.reduce(function (s, b) { return s + (b.kwh || 0); }, 0) / bims.length) * 6;
      modo = bims.length >= 6 ? 'COMPLETA (' + bims.length + ' bimestres reales)' : 'PRELIMINAR (' + bims.length + ' bimestre)';
    } else {
      var anioFin = (o.periodoFin && o.periodoFin.anio) || new Date().getFullYear();
      var mesFin = (o.periodoFin && o.periodoFin.mes) || new Date().getMonth() + 1;
      if (o.historico && o.historico.length >= 12) {
        perfil = perfilDesdeHistorico(c, o.historico);
        modo = 'ÁGIL (histórico del recibo; base/intermedia/punta estimados)';
      } else {
        perfil = perfilDesdeMesUnico(c, anioFin, mesFin);
        modo = 'PRELIMINAR (1 recibo proyectado a 12 meses)';
      }
      consumoAnual = perfil.reduce(function (s, p) {
        return s + (p.kwhBase || 0) + (p.kwhIntermedia || 0) + (p.kwhPunta || 0);
      }, 0);
    }
    if (!(consumoAnual > 0)) return { ok: false, error: 'El consumo capturado es cero: revisa los kWh del recibo' };

    // Voltaje por demanda
    var demandaRef = c.demandaMaxKw || o.demandaContratadaKw || 0;
    var voltaje = o.voltaje;
    if (!voltaje) {
      voltaje = demandaRef < DEMANDA_UMBRAL_VOLTAJE_KW ? 220 : 480;
      avisos.push('Voltaje asumido ' + voltaje + 'V por demanda de ' + Math.round(demandaRef) + ' kW');
    }

    var marca = (!o.equipo || o.equipo === 'auto') ? null
      : o.equipo.charAt(0).toUpperCase() + o.equipo.slice(1).toLowerCase();
    var sistema = dimensionar({
      consumoAnualKwh: consumoAnual, lugar: lugar,
      coberturaObjetivo: o.coberturaObjetivo == null ? 1.0 : o.coberturaObjetivo,
      kwpMaxTecho: o.techoModulos ? o.techoModulos * 0.645 : null,
      voltaje: voltaje, demandaContratadaKw: o.demandaContratadaKw, marca: marca
    });
    avisos = avisos.concat(sistema.avisos);
    var equipo = sistema.marcaInversor.toLowerCase();

    var gen = generacionMensual(sistema.kwpDc, lugar);

    // Ahorro
    var ahorroAnual, facturaSinProm, facturaConProm, facturaSinMax, detalleMeses = [];
    if (esBaja) {
      var fcB = DATOS.factor_carga[tarifa] || 0.58;
      var cargosB = cargosDe(division, tarifa, new Date().getFullYear(), new Date().getMonth() + 1);
      if (!cargosB) return { ok: false, error: 'Sin tarifas publicadas para ' + division + ' ' + tarifa };
      var bims2 = (o.bimestres && o.bimestres.length) ? o.bimestres.slice(-6) : [{ kwh: c.kwhTotal || 0 }];
      var totSin = 0, totCon = 0, credB = 0, maxSin = 0;
      bims2.forEach(function (b, ix) {
        var kwh = b.kwh || 0;
        var sin = simularFacturaPdbt([{ cargos: cargosB, kwh: kwh / 2 }, { cargos: cargosB, kwh: kwh / 2 }], o.dapPct == null ? 0.10 : o.dapPct);
        var mesA = ((ix * 2) % 12), mesB = ((ix * 2 + 1) % 12);
        var genBim = gen[mesA] + gen[mesB];
        var neto = Math.max(0, kwh - genBim - credB);
        credB = Math.max(0, genBim + credB - kwh);
        var con = simularFacturaPdbt([{ cargos: cargosB, kwh: neto / 2 }, { cargos: cargosB, kwh: neto / 2 }], o.dapPct == null ? 0.10 : o.dapPct);
        totSin += sin.total; totCon += con.total;
        if (sin.total > maxSin) maxSin = sin.total;
        detalleMeses.push({ periodo: 'Bimestre ' + (ix + 1), sin: sin.total, con: con.total, genKwh: genBim, kwhTotal: kwh, ahorro: sin.total - con.total });
      });
      // A escala anual: 6 bimestres = 12 meses
      ahorroAnual = (totSin - totCon) * (6 / bims2.length);
      facturaSinProm = totSin / bims2.length / 2;  // promedio mensual
      facturaConProm = totCon / bims2.length / 2;
      facturaSinMax = maxSin / 2;
    } else {
      var sim;
      try {
        sim = simular12Meses(perfil, division, tarifa, gen, true);
      } catch (e) {
        return { ok: false, error: e.message };
      }
      ahorroAnual = sim.ahorroAnual;
      detalleMeses = sim.meses;
      var sumSin = 0, sumCon = 0; facturaSinMax = 0;
      sim.meses.forEach(function (m) {
        sumSin += m.sin; sumCon += m.con;
        if (m.sin > facturaSinMax) facturaSinMax = m.sin;
      });
      facturaSinProm = sumSin / sim.meses.length;
      facturaConProm = sumCon / sim.meses.length;
    }
    if (!(ahorroAnual > 0)) return { ok: false, error: 'El ahorro calculado no es positivo: revisa los datos del recibo' };

    // Banco de capacitores, medidor e incremento de demanda
    var fpActual = c.fpPct ? c.fpPct / 100 : factorPotencia(c);
    var incluyeBc = fpActual > 0 && fpActual < FP_UMBRAL_BC;
    var kvar = incluyeBc ? kvarBanco(demandaRef, fpActual) : 0;
    var medidor = seleccionarMedidor(tarifa, o.demandaContratadaKw || 0);
    var requiereIncremento = (o.demandaContratadaKw || 0) > 0 && sistema.kwAc > o.demandaContratadaKw;
    if (requiereIncremento) avisos.push('Requiere trámite de incremento de demanda ante CFE (no cotizado)');

    var adics = adicionalesProyecto(sistema.nModulos, medidor ? medidor.usd : 0, kvar, 0);
    var sumaAdics = 0;
    for (var k in adics) sumaAdics += adics[k];

    var precio = cotizarPrecio({
      kwp: sistema.kwpDc, ahorroAnualMxn: ahorroAnual, tc: o.tc || 17.5,
      equipo: equipo, voltaje: voltaje, adicionalesUsd: sumaAdics, desgloseAdicionales: adics
    });
    avisos = avisos.concat(precio.avisos);

    var roi = retornoInversion(precio.precioMxn, precio.precioMxnIva, ahorroAnual);
    var bf = tablaBeneficioFiscal(precio.precioMxn, ahorroAnual);
    var pagos = pagosProyectados(facturaSinProm, facturaConProm, precio.mensualidad4a, PLAZO_CORPUS);

    return {
      ok: true, modo: modo, cliente: o.cliente || '', noServicio: o.noServicio || '',
      tarifa: tarifa, division: division, ubicacion: (o.municipio || '') + ', ' + (o.estado || ''),
      lugarHsp: lugar, consumoAnualKwh: consumoAnual, rendimientoKwhKwp: sistema.rendimientoKwhKwp,
      sistema: sistema, generacionMensual: gen,
      ahorroAnualMxn: ahorroAnual, facturaSinProm: facturaSinProm, facturaConProm: facturaConProm,
      facturaSinMax: facturaSinMax, precio: precio, roi: roi, beneficioFiscal: bf, pagos: pagos,
      bancoCapacitores: incluyeBc, kvarBanco: kvar, medidor: medidor,
      requiereIncrementoDemanda: requiereIncremento, demandaMaxKw: demandaRef,
      factorPotenciaPct: fpActual * 100, detalleMeses: detalleMeses, avisos: avisos
    };
  }

  global.MotorSolar = {
    cargarDatos: cargarDatos, cotizarProyecto: cotizarProyecto,
    divisionDe: divisionDe, generacionMensual: generacionMensual, kwhPorKwpAnual: kwhPorKwpAnual,
    dimensionar: dimensionar, simularFactura: simularFactura, simular12Meses: simular12Meses,
    cotizarPrecio: cotizarPrecio, retornoInversion: retornoInversion,
    tablaBeneficioFiscal: tablaBeneficioFiscal, pagoMensual: pagoMensual,
    kvarBanco: kvarBanco, seleccionarMedidor: seleccionarMedidor, hspDe: hspDe,
    perfilDesdeMesUnico: perfilDesdeMesUnico,
    CONST: {
      POT_MODULO_W: POT_MODULO_W, RATIO_DC_AC_MAX: RATIO_DC_AC_MAX, TOPE_AC_KW: TOPE_AC_KW,
      PR_CALIBRADO: PR_CALIBRADO, TASA_ANUAL: TASA_ANUAL, COLCHON_TC: COLCHON_TC,
      INVERSORES: INVERSORES, MEDIDORES: MEDIDORES
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
