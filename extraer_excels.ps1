# Extrae el contenido de los .xlsx / .xlsm de OneDrive a excels-historico.json (solo lectura).
# Respeta la posicion de las columnas para que las tablas no se desalineen.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File extraer_excels.ps1
#
# Tarda ~1 min por cada 80 archivos. Deja avance en extraer_excels.log.
Add-Type -AssemblyName System.IO.Compression.FileSystem

$raiz   = "$env:USERPROFILE\OneDrive\Comerciales e Industriales"
$salida = Join-Path $PSScriptRoot 'excels-historico.json'
$log    = Join-Path $PSScriptRoot 'extraer_excels.log'
$MAX_FILAS_HOJA = 150
$MAX_CHARS_ARCHIVO = 20000

function Log($m) { "{0}  {1}" -f (Get-Date -Format HH:mm:ss), $m | Out-File $log -Append -Encoding utf8 }
function EsperarEspacio {
  $esperas = 0
  while (((Get-Volume -DriveLetter C).SizeRemaining / 1MB) -lt 2500 -and $esperas -lt 40) {
    if ($esperas -eq 0) { Log "disco por debajo de 2.5 GB: esperando a que OneDrive libere" }
    if (-not (Get-Process OneDrive -EA SilentlyContinue)) { Start-Process "C:\Program Files\Microsoft OneDrive\OneDrive.exe" }
    Start-Sleep -Seconds 30; $esperas++
  }
}
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
function Guardar {
  $out = [ordered]@{ generado = (Get-Date).ToString('s'); origen = $raiz; total = $res.Count; fallos = $script:fallos; archivos = $res }
  [System.IO.File]::WriteAllText($salida, ($out | ConvertTo-Json -Depth 8 -Compress), (New-Object System.Text.UTF8Encoding $false))
}
function Limpiar($s) {
  $s = $s -replace '&lt;','<' -replace '&gt;','>' -replace '&quot;','"' -replace '&apos;',"'" -replace '&amp;','&'
  return [regex]::Replace($s, '&#(\d+);', { [char][int]$args[0].Groups[1].Value })
}
# "C" -> 3, "AA" -> 27
function ColIndice([string]$ref) {
  $m = [regex]::Match($ref, '^([A-Z]+)'); if (-not $m.Success) { return -1 }
  $n = 0; foreach ($ch in $m.Groups[1].Value.ToCharArray()) { $n = $n * 26 + ([int][char]$ch - 64) }; return $n
}
function LeerEntrada($z, $nombre) {
  $e = $z.Entries | Where-Object { $_.FullName -eq $nombre } | Select-Object -First 1
  if (-not $e) { return $null }
  $sr = New-Object System.IO.StreamReader($e.Open(), [System.Text.Encoding]::UTF8); $x = $sr.ReadToEnd(); $sr.Close(); return $x
}

$previos = @{}
if (Test-Path $salida) {
  try { $j = Get-Content $salida -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($p in $j.archivos) { if (-not $p.error) { $previos[$p.ruta + '|' + $p.fecha] = $p } } } catch { }
}
$archivos = Get-ChildItem $raiz -Recurse -File -Force -EA SilentlyContinue | Where-Object { $_.Extension -in '.xlsx', '.xlsm' }
Log ("archivos: " + $archivos.Count + "  (ya extraidos antes: " + $previos.Count + ")")
$res = New-Object System.Collections.ArrayList
$n = 0; $fallos = 0; $reutilizados = 0
foreach ($a in $archivos) {
  $n++
  if ($n % 200 -eq 0) { Log "$n / $($archivos.Count) (fallos: $fallos, reutilizados: $reutilizados)" }
  if ($n % 500 -eq 0) { Guardar }
  $rel = $a.FullName.Substring($raiz.Length).TrimStart('\')
  $partes = $rel -split '\\'
  $clavePrev = $rel + '|' + $a.LastWriteTime.ToString('yyyy-MM-dd')
  if ($previos.ContainsKey($clavePrev)) { attrib -P +U $a.FullName 2>$null; [void]$res.Add($previos[$clavePrev]); $reutilizados++; continue }
  $devolver = (([int]$a.Attributes -band 0x80000) -eq 0)
  EsperarEspacio
  # Mientras se lee este, OneDrive va bajando los siguientes diez en paralelo
  for ($j = $n; $j -lt [Math]::Min($n + 10, $archivos.Count); $j++) {
    $b = $archivos[$j]
    if (-not $previos.ContainsKey($b.FullName.Substring($raiz.Length).TrimStart('\') + '|' + $b.LastWriteTime.ToString('yyyy-MM-dd'))) { attrib +P -U $b.FullName 2>$null }
  }
  $reg = [ordered]@{
    cliente = $(if ($partes.Count -gt 1) { $partes[0] } else { '(raiz)' })
    ruta    = $rel
    carpeta = $(if ($partes.Count -gt 2) { ($partes[1..($partes.Count - 2)] -join ' / ') } else { '' })
    archivo = $a.Name
    fecha   = $a.LastWriteTime.ToString('yyyy-MM-dd')
  }
  try {
    if (-not (Hidratar $a.FullName 120)) { throw "OneDrive no lo descargo en 2 min" }
    $z = [System.IO.Compression.ZipFile]::OpenRead($a.FullName)
    try {
      $comp = @()
      $x = LeerEntrada $z 'xl/sharedStrings.xml'
      if ($x) { foreach ($si in [regex]::Matches($x, '<si>(.*?)</si>', 'Singleline')) { $comp += (Limpiar (([regex]::Matches($si.Groups[1].Value, '<t[^>]*>(.*?)</t>', 'Singleline') | ForEach-Object { $_.Groups[1].Value }) -join '')) } }
      $nombres = @()
      $x = LeerEntrada $z 'xl/workbook.xml'
      if ($x) { $nombres = [regex]::Matches($x, '<sheet[^>]*name="([^"]*)"') | ForEach-Object { Limpiar $_.Groups[1].Value } }
      $hojas = @(); $chars = 0; $i = 0
      $entradas = $z.Entries | Where-Object { $_.FullName -match '^xl/worksheets/sheet\d+\.xml$' } | Sort-Object { [int]([regex]::Match($_.FullName, '(\d+)').Value) }
      foreach ($sh in $entradas) {
        if ($chars -ge $MAX_CHARS_ARCHIVO) { break }
        $sr = New-Object System.IO.StreamReader($sh.Open(), [System.Text.Encoding]::UTF8); $x = $sr.ReadToEnd(); $sr.Close()
        $filas = @(); $nf = 0
        foreach ($row in [regex]::Matches($x, '<row[^>]*>(.*?)</row>', 'Singleline')) {
          if ($nf -ge $MAX_FILAS_HOJA -or $chars -ge $MAX_CHARS_ARCHIVO) { break }
          $porCol = @{}; $maxCol = 0
          foreach ($cm in [regex]::Matches($row.Groups[1].Value, '<c([^>]*)>(.*?)</c>', 'Singleline')) {
            $attrs = $cm.Groups[1].Value; $inner = $cm.Groups[2].Value
            $tm = [regex]::Match($attrs, 't="([^"]*)"'); $tipo = $(if ($tm.Success) { $tm.Groups[1].Value } else { '' })
            $v = [regex]::Match($inner, '<v>(.*?)</v>', 'Singleline'); $val = $null
            if ($tipo -eq 's' -and $v.Success) { $idx = [int]$v.Groups[1].Value; if ($idx -lt $comp.Count) { $val = $comp[$idx] } }
            elseif ($tipo -eq 'inlineStr' -or $tipo -eq 'str') {
              $it = [regex]::Match($inner, '<t[^>]*>(.*?)</t>', 'Singleline')
              if ($it.Success) { $val = Limpiar $it.Groups[1].Value } elseif ($v.Success) { $val = Limpiar $v.Groups[1].Value }
            } elseif ($v.Success) { $val = $v.Groups[1].Value }
            if ($null -ne $val -and $val -ne '') {
              $rm = [regex]::Match($attrs, 'r="([A-Z]+\d+)"')
              $ci = $(if ($rm.Success) { ColIndice $rm.Groups[1].Value } else { -1 })
              if ($ci -lt 1) { $ci = $maxCol + 1 }
              $porCol[$ci] = $val; if ($ci -gt $maxCol) { $maxCol = $ci }
            }
          }
          if ($porCol.Count) {
            $celdas = @(1..$maxCol | ForEach-Object { $(if ($porCol.ContainsKey($_)) { $porCol[$_] } else { '' }) })
            $linea = ($celdas -join ' | '); $filas += $linea; $chars += $linea.Length; $nf++
          }
        }
        if ($filas.Count) { $hojas += [ordered]@{ hoja = $(if ($i -lt $nombres.Count) { $nombres[$i] } else { "Hoja$($i+1)" }); filas = $filas } }
        $i++
      }
      $reg.hojas = $hojas; $reg.nHojas = $hojas.Count
    } finally { $z.Dispose() }
  } catch { $fallos++; $reg.error = $_.Exception.Message }
  if ($devolver) { attrib +U -P $a.FullName 2>$null }
  [void]$res.Add($reg)
}
Guardar
Log ("LISTO. " + $res.Count + " archivos, $fallos fallos, $reutilizados reutilizados (" + [math]::Round((Get-Item $salida).Length / 1MB, 1) + " MB)")
"LISTO: " + $res.Count + " archivos, $fallos fallos"
