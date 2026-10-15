# Cruza las propuestas y hojas de calculo de OneDrive (propuestas-historico.json,
# excels-historico.json) con la base comercial (consolidado.json) y produce
# consolidado-unico.json: una ficha por cliente, que front-consolidado.html engancha por idCRM.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File consolidar_unico.ps1
#
# Correr DESPUES de extraer_propuestas.ps1 y extraer_excels.ps1.
$base   = $PSScriptRoot
$jp     = Get-Content "$base\propuestas-historico.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$jc     = Get-Content "$base\consolidado.json"          -Raw -Encoding UTF8 | ConvertFrom-Json
$jx     = Get-Content "$base\excels-historico.json"     -Raw -Encoding UTF8 | ConvertFrom-Json
$salida = "$base\consolidado-unico.json"
$raizOD = "$env:USERPROFILE\OneDrive\Comerciales e Industriales"
$SEP    = [char]0x7C

# Misma normalizacion de nombre de empresa que consolidar_monday.py
function Clave($n) {
  if (-not $n) { return '' }
  $s = [Text.Encoding]::ASCII.GetString([Text.Encoding]::GetEncoding('ISO-8859-8').GetBytes($n.ToLower()))
  $s = $s -replace '\b(s\.?a\.?p\.?i\.?|s\.?a\.?|de\s+c\.?v\.?|s\.?\s*de\s*r\.?l\.?|s\.?c\.?|sapi|cv|srl)\b', ' '
  $s = $s -replace '\(.*?\)', ' ' -replace '[^a-z0-9 ]', ' ' -replace '\s+', ' '
  return $s.Trim()
}
# Un kWp valido va de 1 a ~3000; Bitrix tiene capturas erroneas (ej. 42,701,410)
function KwpValido($v) { if (-not $v) { return $null }; $n = [double]$v; if ($n -ge 1 -and $n -le 3000) { return $n } else { return $null } }
function LimpiarSituacion($t) {
  if (-not $t) { return $null }
  $t = $t -replace '(?i)Situaci.n Actual\s*\|?\s*\d*\s*\|?\s*', '' -replace '\s{2,}', ' '
  $t = $t.Trim(' ', '|'); if ($t.Length -gt 400) { $t = $t.Substring(0, 400) }
  return $(if ($t) { $t } else { $null })
}
function Mediana($v) { $s = @($v | Sort-Object); if (-not $s.Count) { return $null }; return [math]::Round($s[[int][math]::Floor($s.Count / 2)], 2) }

# ---- 1. Propuestas (pptx) agrupadas por cliente -------------------------------------------
$porCliente = @{}
foreach ($p in $jp.propuestas) {
  $k = Clave $p.cliente; if ($k.Length -lt 3) { continue }
  $d = $p.datos
  $kwp = KwpValido $d.kwp
  if (-not $kwp -and $p.texto) {
    $cands = @([regex]::Matches($p.texto, '([\d][\d,]*(?:\.\d+)?)\s*kWp', 'IgnoreCase') | ForEach-Object { [double](($_.Groups[1].Value) -replace ',','') } | Where-Object { $_ -ge 1 -and $_ -le 3000 })
    if ($cands.Count) { $kwp = @($cands | Sort-Object -Descending)[0] }
  }
  # El par USD/MXN solo vale si la paridad implicita es creible (14-24 pesos por dolar)
  $pu = $d.precioUSD; $pm = $d.precioMXN; $tc = $null
  if ($pu -and $pm) { $t = $pm / $pu; if ($t -ge 14 -and $t -le 24) { $tc = [math]::Round($t, 2) } else { $pm = $null } }
  $ficha = [pscustomobject]@{
    carpeta = $p.carpeta; archivo = $p.archivo; fecha = $p.fecha; fechaTexto = $d.fechaPropuesta
    kwp = $kwp; pctEnergia = $d.pctConsumo; tarifa = $d.tarifa
    precioUSD = $pu; precioMXN = $pm; tipoCambio = $tc
    ahorroAnual = $d.ahorroAnual; pagoPromedio = $d.pagoPromedio
    retornoAnios = $(if ($d.retornoAniosConBF) { $d.retornoAniosConBF } else { $d.retornoAnios })
    ubicacion = $d.ubicacion; rpu = $d.rpu; situacion = LimpiarSituacion $d.situacion
  }
  if (-not $porCliente.ContainsKey($k)) { $porCliente[$k] = @{ nombre = $p.cliente; fichas = @() } }
  $porCliente[$k].fichas += $ficha
}

# ---- 2. Hojas de calculo por cliente (las "Infografia *.xlsx" son la hoja fuente de la propuesta) ----
function ValorTrasEtiqueta($filas, $etiqueta) {
  foreach ($f in $filas) {
    $c = $f.Split($SEP)
    if ($c.Count -ge 2 -and $c[0].Trim().ToUpper() -eq $etiqueta) {
      for ($i = 1; $i -lt [Math]::Min($c.Count, 5); $i++) { $t = $c[$i].Trim(); if ($t -and $t -match '^\-?[\d\.]+([eE]\-?\d+)?$') { return [double]$t } }
    }
  }
  return $null
}
$excelPorCliente = @{}
foreach ($a in $jx.archivos) {
  $k = Clave $a.cliente; if ($k.Length -lt 3 -or -not $a.hojas) { continue }
  if (-not $excelPorCliente.ContainsKey($k)) { $excelPorCliente[$k] = @{ archivos = 0; tipos = @{}; datos = @() } }
  $e = $excelPorCliente[$k]; $e.archivos++
  $n = $a.archivo.ToLower()
  $tipo = $(if ($n -match 'infograf') { 'infografia' } elseif ($n -match 'costo') { 'costos' } elseif ($n -match 'consumo') { 'consumo' }
            elseif ($n -match 'memoria') { 'memoria' } elseif ($n -match 'calculadora') { 'calculadora' }
            elseif ($n -match 'gdmth|gdmto|pdbt|gdbt') { 'tarifa' } else { 'otros' })
  $e.tipos[$tipo] = 1 + $(if ($e.tipos.ContainsKey($tipo)) { $e.tipos[$tipo] } else { 0 })
  $todas = @(); foreach ($h in $a.hojas) { $todas += $h.filas }
  $d = [pscustomobject]@{ fecha = $a.fecha; archivo = $a.archivo
    montoProyectoMXN = ValorTrasEtiqueta $todas 'MONTO PROYECTO MXN'; tasaAnual = ValorTrasEtiqueta $todas 'TASA ANUAL'
    enganche = ValorTrasEtiqueta $todas 'ENGANCHE'; costoPorW = ValorTrasEtiqueta $todas 'COSTO PROMEDIO POR W' }
  if ($d.montoProyectoMXN -or $d.tasaAnual -or $d.costoPorW) { $e.datos += $d }
}
function BloqueExcel($k) {
  if (-not $excelPorCliente.ContainsKey($k)) { return $null }
  $e = $excelPorCliente[$k]
  $conMonto = @($e.datos | Where-Object { $_.montoProyectoMXN } | Sort-Object fecha -Descending); $m = $(if ($conMonto.Count) { $conMonto[0] } else { $null })
  # Costo por W creible: 0.3 a 6 USD/W. Fuera de eso la hoja usa otra unidad o formula rota.
  $costo = @($e.datos | Where-Object { $_.costoPorW -and $_.costoPorW -ge 0.3 -and $_.costoPorW -le 6 } | Sort-Object fecha -Descending)
  return [ordered]@{ archivos = $e.archivos; tipos = $e.tipos; montoProyectoMXN = $m.montoProyectoMXN; tasaAnual = $m.tasaAnual; enganche = $m.enganche
                     costoPorW = $(if ($costo.Count) { [math]::Round($costo[0].costoPorW, 3) } else { $null }); fuente = $m.archivo; fecha = $m.fecha }
}

# ---- 3. Carpetas "solo en linea": sin archivos, pero el nombre de las subcarpetas ya trae datos ----
$MESES = @{ enero=1; febrero=2; marzo=3; abril=4; mayo=5; junio=6; julio=7; agosto=8; septiembre=9; setiembre=9; octubre=10; noviembre=11; diciembre=12 }
$carpetaPorCliente = @{}
foreach ($c in Get-ChildItem $raizOD -Directory -Force -EA SilentlyContinue) {
  $k = Clave $c.Name
  if ($k.Length -lt 3 -or $porCliente.ContainsKey($k) -or $excelPorCliente.ContainsKey($k)) { continue }
  $subs = @(Get-ChildItem $c.FullName -Recurse -Directory -Force -EA SilentlyContinue | Select-Object -ExpandProperty Name)
  $txt = (@($c.Name) + $subs) -join ' | '
  $kwps = @([regex]::Matches($txt, '([\d][\d,\.]*)\s*kWp', 'IgnoreCase') | ForEach-Object { [double](($_.Groups[1].Value) -replace ',','') } | Where-Object { $_ -ge 1 -and $_ -le 3000 })
  $pcts = @([regex]::Matches($txt, '(\d{1,3})\s*%') | ForEach-Object { [int]$_.Groups[1].Value } | Where-Object { $_ -ge 1 -and $_ -le 100 })
  $fechas = @(); foreach ($m in [regex]::Matches($txt, '(?i)\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\s+(20\d\d)\b')) { $fechas += ('{0}-{1:00}-01' -f $m.Groups[2].Value, $MESES[$m.Groups[1].Value.ToLower()]) }
  $nProp = @($subs | Where-Object { $_ -match '(?i)propuesta\s*\d+' } | ForEach-Object { ([regex]::Match($_, '(?i)propuesta\s*(\d+)')).Groups[1].Value } | Sort-Object -Unique).Count
  $carpetaPorCliente[$k] = [ordered]@{
    nombre = $c.Name; subcarpetas = $subs.Count; nPropuestas = $nProp
    kwp = $(if ($kwps.Count) { @($kwps | Sort-Object -Descending)[0] } else { $null })
    pctEnergia = $(if ($pcts.Count) { @($pcts | Sort-Object -Descending)[0] } else { $null })
    ultimaFecha = $(if ($fechas.Count) { @($fechas | Sort-Object -Descending)[0] } else { $null })
    visitaTecnica = [bool]($subs | Where-Object { $_ -match '(?i)^VT\b|visita t' }); estructura = @($subs | Select-Object -First 12)
  }
}

# ---- 4. Indice del CRM y cruce -------------------------------------------------------------
$indice = @{}
foreach ($r in $jc.registros) { foreach ($campo in @($r.empresa, $r.proyecto)) { $k = Clave $campo; if ($k.Length -ge 3 -and -not $indice.ContainsKey($k)) { $indice[$k] = $r } } }
$clientes = New-Object System.Collections.ArrayList
$cruzados = 0; $soloPropuesta = 0; $usados = @{}; $excelUsado = @{}; $carpetaUsada = @{}
$peso = { param($f) ([int][bool]$f.precioUSD)*4 + ([int][bool]$f.kwp)*2 + ([int][bool]$f.pctEnergia) + ([int][bool]$f.ahorroAnual) + ([int][bool]$f.retornoAnios) }

foreach ($k in $porCliente.Keys) {
  $g = $porCliente[$k]; $crm = $indice[$k]
  if (-not $crm) { foreach ($k2 in $indice.Keys) { if (($k2.Contains($k) -or $k.Contains($k2)) -and [Math]::Min($k.Length, $k2.Length) -ge 6) { $crm = $indice[$k2]; break } } }
  if ($crm) { $cruzados++; $usados[$crm.id] = 1 } else { $soloPropuesta++ }
  # Manda la propuesta mas completa; entre iguales, la mas reciente. Los huecos se rellenan con otra del mismo cliente.
  $mejor = $g.fichas | Sort-Object @{e={ & $peso $_ }; d=$true}, @{e={$_.fecha}; d=$true} | Select-Object -First 1
  foreach ($campo in @('kwp','pctEnergia','tarifa','precioUSD','precioMXN','tipoCambio','ahorroAnual','pagoPromedio','retornoAnios','ubicacion','rpu','situacion')) {
    if (-not $mejor.$campo) { $alt = $g.fichas | Where-Object { $_.$campo } | Sort-Object fecha -Descending | Select-Object -First 1; if ($alt) { $mejor.$campo = $alt.$campo } }
  }
  $fechas = @(@($g.fichas.fecha) + @($crm.ultContacto) | Where-Object { $_ } | Sort-Object -Descending)
  [void]$clientes.Add([ordered]@{
    cliente = $g.nombre; enCRM = [bool]$crm; origen = $(if ($crm) { $crm.origen } else { 'propuesta' }); idCRM = $crm.id
    pipeline = $crm.pipeline; etapa = $crm.etapa; estado = $(if ($crm) { $crm.estado } else { 'sin registro' }); dueno = $crm.dueno
    contactoNombre = $crm.contacto; tel = $crm.tel; email = $crm.email
    ultimaFecha = $(if ($fechas.Count) { $fechas[0] } else { $null }); ultContactoCRM = $crm.ultContacto
    kwp = $(if ($mejor.kwp) { $mejor.kwp } else { KwpValido $crm.kwp }); pctEnergia = $(if ($mejor.pctEnergia) { $mejor.pctEnergia } else { $crm.energia })
    tarifa = $mejor.tarifa; precioUSD = $(if ($mejor.precioUSD) { $mejor.precioUSD } else { $crm.precioUSD }); precioMXN = $mejor.precioMXN; tipoCambio = $mejor.tipoCambio
    ahorroAnual = $mejor.ahorroAnual; retornoAnios = $(if ($mejor.retornoAnios) { $mejor.retornoAnios } else { $crm.retorno })
    ubicacion = $mejor.ubicacion; rpu = $mejor.rpu; situacion = $mejor.situacion
    nPropuestas = $g.fichas.Count; propuestas = @($g.fichas | Sort-Object fecha -Descending); excel = $(BloqueExcel $k); carpeta = $null
  })
  $excelUsado[$k] = 1
}
# Registros del CRM sin propuesta en pptx
$sinPropuesta = 0
foreach ($r in $jc.registros) {
  if ($usados.ContainsKey($r.id)) { continue }
  $sinPropuesta++
  $kr = Clave $(if ($r.empresa) { $r.empresa } else { $r.proyecto })
  $fila = [ordered]@{
    cliente = $(if ($r.empresa) { $r.empresa } else { $r.proyecto }); enCRM = $true; origen = $r.origen; idCRM = $r.id
    pipeline = $r.pipeline; etapa = $r.etapa; estado = $r.estado; dueno = $r.dueno; contactoNombre = $r.contacto; tel = $r.tel; email = $r.email
    ultimaFecha = $r.ultContacto; ultContactoCRM = $r.ultContacto
    kwp = (KwpValido $r.kwp); pctEnergia = $r.energia; tarifa = $null
    precioUSD = $r.precioUSD; precioMXN = $(if ($r.moneda -eq 'MXN') { $r.precio } else { $null }); tipoCambio = $null
    ahorroAnual = $null; retornoAnios = $r.retorno; ubicacion = $null; rpu = $null; situacion = $r.descripcion
    nPropuestas = 0; propuestas = @(); excel = $(BloqueExcel $kr); carpeta = $null
  }
  if ($kr) {
    $excelUsado[$kr] = 1
    if ($carpetaPorCliente.ContainsKey($kr)) {
      $cp = $carpetaPorCliente[$kr]; $fila.carpeta = $cp; $fila['pendienteDescarga'] = $true; $carpetaUsada[$kr] = 1
      if (-not $fila.kwp -and $cp.kwp) { $fila.kwp = $cp.kwp }
      if (-not $fila.pctEnergia -and $cp.pctEnergia) { $fila.pctEnergia = $cp.pctEnergia }
      if ($cp.ultimaFecha -and (-not $fila.ultimaFecha -or $cp.ultimaFecha -gt $fila.ultimaFecha)) { $fila.ultimaFecha = $cp.ultimaFecha }
    }
  }
  [void]$clientes.Add($fila)
}
# Clientes que solo aparecen en hojas de calculo
$soloExcel = 0
foreach ($k in $excelPorCliente.Keys) {
  if ($excelUsado.ContainsKey($k)) { continue }
  $bl = BloqueExcel $k; if (-not $bl) { continue }; $soloExcel++
  [void]$clientes.Add([ordered]@{ cliente = $k; enCRM = $false; origen = 'excel'; idCRM = $null; pipeline = $null; etapa = $null; estado = 'sin registro'; dueno = $null
    contactoNombre = $null; tel = $null; email = $null; ultimaFecha = $bl.fecha; ultContactoCRM = $null; kwp = $null; pctEnergia = $null; tarifa = $null
    precioUSD = $null; precioMXN = $bl.montoProyectoMXN; tipoCambio = $null; ahorroAnual = $null; retornoAnios = $null; ubicacion = $null; rpu = $null; situacion = $null
    nPropuestas = 0; propuestas = @(); excel = $bl; carpeta = $null })
}
# Clientes cuya unica huella es la carpeta solo en linea
$soloCarpeta = 0
foreach ($k in $carpetaPorCliente.Keys) {
  if ($carpetaUsada.ContainsKey($k)) { continue }
  $cp = $carpetaPorCliente[$k]; $soloCarpeta++
  [void]$clientes.Add([ordered]@{ cliente = $cp.nombre; enCRM = $false; origen = 'carpeta'; idCRM = $null; pipeline = $null; etapa = $null; estado = 'sin registro'; dueno = $null
    contactoNombre = $null; tel = $null; email = $null; ultimaFecha = $cp.ultimaFecha; ultContactoCRM = $null; kwp = $cp.kwp; pctEnergia = $cp.pctEnergia; tarifa = $null
    precioUSD = $null; precioMXN = $null; tipoCambio = $null; ahorroAnual = $null; retornoAnios = $null; ubicacion = $null; rpu = $null; situacion = $null
    nPropuestas = 0; propuestas = @(); excel = $null; carpeta = $cp; pendienteDescarga = $true })
}

# ---- 5. Precio en las dos monedas ----------------------------------------------------------
# Tipo de cambio de referencia por anio: mediana de las paridades reales que usaron las propuestas.
$porAnio = @{}
foreach ($cl in $clientes) { foreach ($pr in $cl.propuestas) { if ($pr.tipoCambio -and $pr.fecha) { $a = $pr.fecha.Substring(0, 4); if (-not $porAnio.ContainsKey($a)) { $porAnio[$a] = @() }; $porAnio[$a] += [double]$pr.tipoCambio } } }
$tcAnio = @{}; $todos = @(); foreach ($a in $porAnio.Keys) { $tcAnio[$a] = Mediana $porAnio[$a]; $todos += $porAnio[$a] }
$tcGlobal = Mediana $todos; if (-not $tcGlobal) { $tcGlobal = 17.5 }
$deExcel = 0
foreach ($cl in $clientes) {
  if (-not $cl.precioMXN -and $cl.excel -and $cl.excel.montoProyectoMXN) {
    $m = [double]$cl.excel.montoProyectoMXN
    if ($cl.precioUSD) { $t = $m / [double]$cl.precioUSD; if ($t -ge 14 -and $t -le 24) { $cl.precioMXN = $m; $cl.tipoCambio = [math]::Round($t, 2); $deExcel++ } }
    else { $cl.precioMXN = $m; $deExcel++ }
  }
}
# Si el CRM trae USD y MXN que no cuadran entre si (capturas de distinta fecha o error),
# manda el USD y el MXN se recalcula con el tipo de cambio de referencia.
$corregidos = 0
foreach ($cl in $clientes) {
  if ($cl.precioUSD -and $cl.precioMXN) {
    $t = [double]$cl.precioMXN / [double]$cl.precioUSD
    if ($t -lt 13 -or $t -gt 25) { $cl.precioMXN = $null; $cl.tipoCambio = $null; $corregidos++ }
  }
}
"paridades imposibles corregidas: $corregidos"
$convertidos = 0
foreach ($cl in $clientes) {
  if (($cl.precioUSD -and $cl.precioMXN) -or (-not $cl.precioUSD -and -not $cl.precioMXN)) { continue }
  $anio = $(if ($cl.ultimaFecha -and $cl.ultimaFecha.Length -ge 4) { $cl.ultimaFecha.Substring(0, 4) } else { '' })
  $tc = $(if ($anio -and $tcAnio.ContainsKey($anio)) { $tcAnio[$anio] } else { $tcGlobal })
  if ($cl.precioUSD) { $cl.precioMXN = [math]::Round([double]$cl.precioUSD * $tc, 0) } else { $cl.precioUSD = [math]::Round([double]$cl.precioMXN / $tc, 0) }
  $cl.tipoCambio = $tc; $cl['tcEstimado'] = $true; $convertidos++
}

$out = [ordered]@{
  generado = (Get-Date).ToString('s')
  fuentes  = @{ propuestasOneDrive = $jp.propuestas.Count; excelsOneDrive = $jx.archivos.Count; registrosCRM = $jc.registros.Count }
  totales  = @{ clientes = $clientes.Count; conPropuesta = ($cruzados + $soloPropuesta); cruzadosCRM = $cruzados; soloPropuesta = $soloPropuesta; soloCRM = $sinPropuesta
                soloExcel = $soloExcel; soloCarpeta = $soloCarpeta; pendientesDescarga = @($clientes | Where-Object { $_.pendienteDescarga }).Count }
  clientes = @($clientes | Sort-Object @{e={$_.nPropuestas}; d=$true}, cliente)
}
[System.IO.File]::WriteAllText($salida, ($out | ConvertTo-Json -Depth 8 -Compress), (New-Object System.Text.UTF8Encoding $false))
"tipo de cambio por anio: " + (($tcAnio.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join '  ')
"precios MXN de la hoja de calculo: $deExcel   completados por conversion: $convertidos"
"clientes en la ficha unica : " + $clientes.Count
"  con propuesta pptx       : " + ($cruzados + $soloPropuesta) + "  (cruzados CRM $cruzados, sin CRM $soloPropuesta)"
"  solo CRM                 : $sinPropuesta"
"  solo Excel               : $soloExcel"
"  solo carpeta en linea    : $soloCarpeta"
"  pendientes de descarga   : " + $out.totales.pendientesDescarga
"tamano: " + [math]::Round((Get-Item $salida).Length / 1MB, 2) + " MB"
