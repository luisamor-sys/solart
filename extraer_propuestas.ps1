# Extrae todo el texto de las propuestas .pptx de OneDrive a propuestas-historico.json
# y deduce los campos clave (kWp, % energia, precio USD/MXN, retorno, ahorro, tarifa...).
# Solo lectura: abre cada pptx como zip y lee unicamente los XML de diapositivas y notas.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File extraer_propuestas.ps1
#
# Tarda ~1 min por cada 150 archivos. Deja avance en extraer_propuestas.log.
#
#   -SoloRededucir : no toca OneDrive; vuelve a deducir los campos a partir del texto ya guardado
#                    (para cuando cambian las reglas de Deducir).
param([switch]$SoloRededucir)
Add-Type -AssemblyName System.IO.Compression.FileSystem

$raiz   = "$env:USERPROFILE\OneDrive\Comerciales e Industriales"
$salida = Join-Path $PSScriptRoot 'propuestas-historico.json'
$log    = Join-Path $PSScriptRoot 'extraer_propuestas.log'
$SEP    = [char]0x7C   # '|'

function Log($m) { "{0}  {1}" -f (Get-Date -Format HH:mm:ss), $m | Out-File $log -Append -Encoding utf8 }

# Casi todas las propuestas son marcadores "solo en linea": abrirlas las descarga (~95 MB cada una).
# Si el disco se queda sin margen, se espera a que OneDrive vuelva a liberar las ya leidas.
function EsperarEspacio {
  $esperas = 0
  while (((Get-Volume -DriveLetter C).SizeRemaining / 1MB) -lt 2500 -and $esperas -lt 40) {
    if ($esperas -eq 0) { Log "disco por debajo de 2.5 GB: esperando a que OneDrive libere lo ya leido" }
    if (-not (Get-Process OneDrive -EA SilentlyContinue)) { Log "OneDrive no esta corriendo: no va a liberar nada"; Start-Process "C:\Program Files\Microsoft OneDrive\OneDrive.exe" }
    Start-Sleep -Seconds 30; $esperas++
  }
}
# Abrir un marcador directamente como zip lee el archivo a medias ("directorio central danado"):
# hay que pedirle a OneDrive que lo baje (fijarlo) y esperar a que deje de ser "solo en linea".
function Hidratar($ruta, $seg) {
  $fi = Get-Item -LiteralPath $ruta -Force
  if (([int]$fi.Attributes -band 0x400000) -eq 0) { return $true }
  attrib +P -U $ruta 2>$null
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalSeconds -lt $seg) {
    Start-Sleep -Seconds 2
    $fi = Get-Item -LiteralPath $ruta -Force
    if (([int]$fi.Attributes -band 0x400000) -eq 0) { return $true }
  }
  return $false
}
# Guarda lo que va (permite reanudar si algo se interrumpe)
function Guardar {
  $out = [ordered]@{ generado = (Get-Date).ToString('s'); origen = $raiz; total = $res.Count; fallos = $script:fallos; propuestas = $res }
  [System.IO.File]::WriteAllText($salida, ($out | ConvertTo-Json -Depth 8 -Compress), (New-Object System.Text.UTF8Encoding $false))
}

function Limpiar($s) {
  $s = $s -replace '&lt;','<' -replace '&gt;','>' -replace '&quot;','"' -replace '&apos;',"'" -replace '&amp;','&'
  return [regex]::Replace($s, '&#(\d+);', { [char][int]$args[0].Groups[1].Value })
}
function TextoDeXml($xml) {
  $partes = [regex]::Matches($xml, '<a:t>(.*?)</a:t>', 'Singleline') | ForEach-Object { Limpiar $_.Groups[1].Value }
  return ($partes -join ' | ')
}
function Num($s) { if ($null -eq $s -or $s -eq '') { return $null }; $t = ($s -replace '[^\d\.]',''); if ($t -eq '' -or $t -eq '.') { return $null }; return [double]$t }
function MontoTrasEtiqueta($linea, $patron) {
  $m = [regex]::Match($linea, $patron + '[^\d\$]{0,30}\$?\s*([\d][\d,]*(?:\.\d{1,2})?)', 'IgnoreCase')
  if ($m.Success) { return Num $m.Groups[1].Value }
  return $null
}

# Campos estructurados deducidos del texto corrido de todas las diapositivas
function Deducir($texto) {
  $d = [ordered]@{}
  $lineas = $texto -split "`n"
  # kWp: el de la diapositiva "La Solucion" manda (a veces numero y unidad vienen en celdas
  # separadas: "97 | kWp"). Si no esta, el primer "N kWp" del documento.
  $m = [regex]::Match($texto, 'La Soluci.n[^\n]{0,40}?([\d][\d,\.]*)\s*(?:\|\s*)?kWp', 'IgnoreCase')
  if (-not $m.Success) { $m = [regex]::Match($texto, '([\d][\d,\.]*)\s*(?:\|\s*)?kWp', 'IgnoreCase') }
  if ($m.Success) { $d.kwp = Num $m.Groups[1].Value }
  $m = [regex]::Match($texto, '([\d][\d,\.]*)\s*kWh', 'IgnoreCase');                 if ($m.Success) { $d.kwh = Num $m.Groups[1].Value }
  $m = [regex]::Match($texto, 'RPU[:\s|]+([\d\s]{8,})', 'IgnoreCase');               if ($m.Success) { $d.rpu = ($m.Groups[1].Value).Trim() }
  $m = [regex]::Match($texto, '\b(GDMTH|GDMTO|PDBT|GDBT|DIST|DIT|APBT|APMT)\b');     if ($m.Success) { $d.tarifa = $m.Groups[1].Value }
  $m = [regex]::Match($texto, '([\d]{1,3})\s*%[^\d]{0,25}del Consumo Energ', 'IgnoreCase'); if ($m.Success) { $d.pctConsumo = [int]$m.Groups[1].Value }
  $m = [regex]::Match($texto, '([\d][\d,\.]*)\s*(?:modulos|m.dulos)', 'IgnoreCase');  if ($m.Success) { $d.modulos = Num $m.Groups[1].Value }

  # Precio: pares "$ X USD ... $ Y MXN"; manda el de la tabla de "Precio Total"
  $pares = @()
  foreach ($l in $lineas) {
    foreach ($m in [regex]::Matches($l, '\$\s*([\d][\d,]*(?:\.\d{1,2})?)\s*USD[^\d\$]{0,40}\$\s*([\d][\d,]*(?:\.\d{1,2})?)\s*MXN')) {
      $u = Num $m.Groups[1].Value; $x = Num $m.Groups[2].Value
      if ($u -and $x -and $u -ge 1000) { $pares += [pscustomobject]@{ usd = $u; mxn = $x; total = ($l -match '(?i)precio total|precio sistema fv|precio\*') } }
    }
  }
  if ($pares.Count) {
    # Un mismo documento puede traer varias propuestas (y repetir el precio con recargo en la
    # diapositiva de financiamiento). El kWp se toma de la PRIMERA propuesta, asi que el precio
    # tambien: el primer par en orden de documento, y entre los de "precio total" si los hay.
    # Como salvaguarda, si con el kWp ese precio da un costo por watt increible (fuera de
    # 0.3-2.0 USD/W) y otro par si lo da, se prefiere el creible.
    $cand = @($pares | Where-Object { $_.total }); if (-not $cand.Count) { $cand = @($pares) }
    $best = $cand[0]
    if ($d.Contains('kwp') -and $d.kwp -ge 5) {
      $plaus = @($cand | Where-Object { $upw = $_.usd / ($d.kwp * 1000); $upw -ge 0.3 -and $upw -le 2.0 })
      if ($plaus.Count) { $best = $plaus[0] }
    }
    $d.precioUSD = $best.usd; $d.precioMXN = $best.mxn; $d.tipoCambio = [math]::Round($best.mxn / $best.usd, 2)
    if ($pares.Count -gt 1) { $d.nOpcionesPrecio = @($pares | Select-Object -ExpandProperty usd -Unique).Count }
  }
  foreach ($l in $lineas) {
    if (-not $d.Contains('ahorroAnual'))    { $v = MontoTrasEtiqueta $l 'Ahorro Anual[^:]{0,30}:'; if ($v -and $v -ge 1000) { $d.ahorroAnual = $v } }
    if (-not $d.Contains('pagoPromedio'))   { $v = MontoTrasEtiqueta $l 'Pago Promedio\s*:';       if ($v -and $v -ge 100)  { $d.pagoPromedio = $v } }
    if (-not $d.Contains('pagoMasAlto'))    { $v = MontoTrasEtiqueta $l 'Pago m.s alto\s*:';       if ($v -and $v -ge 100)  { $d.pagoMasAlto = $v } }
    if (-not $d.Contains('utilidadFiscal')) { $v = MontoTrasEtiqueta $l 'Utilidad Fiscal\s*:';     if ($v -and $v -ge 1000) { $d.utilidadFiscal = $v } }
    $m = [regex]::Match($l, '(?i)retorno de inversi.n(\s*con beneficio fiscal)?[^\d]{0,40}([\d]+(?:\.\d+)?)\s*a.os')
    if ($m.Success) {
      $v = [double]$m.Groups[2].Value
      if ($v -gt 0 -and $v -le 30) {
        if ($m.Groups[1].Success) { if (-not $d.Contains('retornoAniosConBF')) { $d.retornoAniosConBF = $v } }
        elseif (-not $d.Contains('retornoAnios')) { $d.retornoAnios = $v }
      }
    }
  }
  # Portada (diapositiva 1 o 2): ubicacion "Ciudad, Estado" y fecha "Mes, 2024"
  $portada = $lineas | Where-Object { $_ -match '^\[[12]\]' } | Select-Object -First 1
  if ($portada) {
    $celdas = $portada.Split($SEP) | ForEach-Object { $_.Trim() }
    $ub = $celdas | Where-Object { $_ -match ',' -and $_ -notmatch '(?i)RPU|fotovoltaic|interconect' -and $_.Length -lt 70 -and $_ -notmatch '^\d' -and $_ -notmatch '(?i)^(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b' } | Select-Object -First 1
    if ($ub) { $d.ubicacion = $ub.TrimEnd('.') }
    $fp = $celdas | Where-Object { $_ -match '(?i)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)[,\s]+20\d\d' } | Select-Object -First 1
    if ($fp) { $d.fechaPropuesta = $fp.TrimEnd('.') }
  }
  # Situacion actual (sin la linea de agenda)
  $sit = @(); foreach ($l in $lineas) { if ($l -match '(?i)Situaci.n Actual' -and $l -notmatch '(?i)Agenda') { $sit += ($l -replace '^\[\d+\]\s*','') } }
  if ($sit.Count) { $t = [regex]::Replace(($sit -join ' '), '\s{2,}', ' '); $d.situacion = $t.Substring(0, [Math]::Min(700, $t.Length)) }
  # Contactos, si los hubiera (casi nunca: viven en el CRM)
  $mails = [regex]::Matches($texto, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}') | ForEach-Object { $_.Value.ToLower() } | Sort-Object -Unique
  if ($mails) { $d.emails = @($mails) }
  $tels = [regex]::Matches($texto, '(?<![\d\-\.])(?:\+?52[\s\-]?)?(?:\(?\d{2,3}\)?[\s\-]){1,2}\d{3,4}[\s\-]?\d{4}(?![\d\-])') | ForEach-Object { $_.Value.Trim() } | Sort-Object -Unique
  if ($tels) { $d.telefonos = @($tels | Select-Object -First 5) }
  return $d
}

if ($SoloRededucir) {
  $j = Get-Content $salida -Raw -Encoding UTF8 | ConvertFrom-Json
  $n = 0
  foreach ($p in $j.propuestas) {
    if ($p.texto) { $p.datos = Deducir $p.texto; $n++ }
  }
  $j.generado = (Get-Date).ToString('s')
  [System.IO.File]::WriteAllText($salida, ($j | ConvertTo-Json -Depth 8 -Compress), (New-Object System.Text.UTF8Encoding $false))
  Log "REDEDUCIDO: $n propuestas desde el texto guardado"
  "REDEDUCIDO: $n propuestas"
  exit
}

# Lo ya extraido en una corrida anterior (misma ruta y fecha, sin error) no se vuelve a leer
$previos = @{}
if (Test-Path $salida) {
  try { $j = Get-Content $salida -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($p in $j.propuestas) { if (-not $p.error -and $p.texto) { $previos[$p.ruta + '|' + $p.fecha] = $p } } } catch { }
}
$archivos = Get-ChildItem $raiz -Recurse -File -Filter *.pptx -Force -ErrorAction SilentlyContinue
Log ("archivos a procesar: " + $archivos.Count + "  (ya extraidos antes: " + $previos.Count + ")")
$res = New-Object System.Collections.ArrayList
$n = 0; $fallos = 0; $reutilizados = 0
foreach ($a in $archivos) {
  $n++
  if ($n % 100 -eq 0) { Log ("$n / " + $archivos.Count + "  (fallos: $fallos, reutilizados: $reutilizados)") }
  if ($n % 200 -eq 0) { Guardar }
  $rel = $a.FullName.Substring($raiz.Length).TrimStart('\')
  $partes = $rel -split '\\'
  $clavePrev = $rel + '|' + $a.LastWriteTime.ToString('yyyy-MM-dd')
  if ($previos.ContainsKey($clavePrev)) { attrib -P +U $a.FullName 2>$null; [void]$res.Add($previos[$clavePrev]); $reutilizados++; continue }
  # Si era "solo en linea", leerlo lo descarga: al terminar se devuelve a la nube
  $devolver = (([int]$a.Attributes -band 0x80000) -eq 0)
  EsperarEspacio
  # Mientras se lee este, OneDrive va bajando los siguientes seis en paralelo
  for ($j = $n; $j -lt [Math]::Min($n + 6, $archivos.Count); $j++) {
    $b = $archivos[$j]
    if (-not $previos.ContainsKey($b.FullName.Substring($raiz.Length).TrimStart('\') + '|' + $b.LastWriteTime.ToString('yyyy-MM-dd'))) { attrib +P -U $b.FullName 2>$null }
  }
  $reg = [ordered]@{
    cliente = $(if ($partes.Count -gt 1) { $partes[0] } else { '(raiz)' })
    ruta    = $rel
    carpeta = $(if ($partes.Count -gt 2) { ($partes[1..($partes.Count - 2)] -join ' / ') } else { '' })
    archivo = $a.Name
    fecha   = $a.LastWriteTime.ToString('yyyy-MM-dd')
    mb      = [math]::Round($a.Length / 1MB, 1)
  }
  try {
    if (-not (Hidratar $a.FullName 240)) { throw "OneDrive no lo descargo en 4 min" }
    $z = [System.IO.Compression.ZipFile]::OpenRead($a.FullName)
    try {
      $slides = $z.Entries | Where-Object { $_.FullName -match '^ppt/slides/slide(\d+)\.xml$' } | Sort-Object { [int]([regex]::Match($_.FullName, '(\d+)').Value) }
      $sb = New-Object System.Text.StringBuilder; $nDiap = 0
      foreach ($e in $slides) {
        $nDiap++
        $sr = New-Object System.IO.StreamReader($e.Open(), [System.Text.Encoding]::UTF8); $xml = $sr.ReadToEnd(); $sr.Close()
        $t = TextoDeXml $xml; if ($t) { [void]$sb.Append("[$nDiap] $t`n") }
      }
      $notas = New-Object System.Text.StringBuilder
      foreach ($e in ($z.Entries | Where-Object { $_.FullName -match '^ppt/notesSlides/notesSlide\d+\.xml$' })) {
        $sr = New-Object System.IO.StreamReader($e.Open(), [System.Text.Encoding]::UTF8); $xml = $sr.ReadToEnd(); $sr.Close()
        $t = TextoDeXml $xml; if ($t) { [void]$notas.Append($t + "`n") }
      }
      $reg.diapositivas = $nDiap
      $reg.texto = $sb.ToString().Trim()
      if ($notas.Length) { $reg.notas = $notas.ToString().Trim() }
      $reg.datos = Deducir $reg.texto
    } finally { $z.Dispose() }
  } catch { $fallos++; $reg.error = $_.Exception.Message; Log ("FALLO: $rel -> " + $_.Exception.Message) }
  if ($devolver) { attrib +U -P $a.FullName 2>$null }
  [void]$res.Add($reg)
}
Guardar
Log ("LISTO. " + $res.Count + " propuestas, $fallos fallos, $reutilizados reutilizados -> $salida  (" + [math]::Round((Get-Item $salida).Length / 1MB, 1) + " MB)")
"LISTO: " + $res.Count + " propuestas, $fallos fallos"
