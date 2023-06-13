Add-Type -AssemblyName System.Net.Http
Add-Type -AssemblyName System.Web

$httpClient = New-Object System.Net.Http.HttpClient

Function Get-NewSessionId {
    $uri = 'http://192.168.8.1/html/home.html'

    $response = $httpClient.GetAsync($uri).Result

    $cookies = $response.Headers.GetValues("Set-Cookie") | Out-String

    $sessionId = $null

    if ($cookies -match 'SessionID=([^;]+)') {
        $sessionId = $Matches[1]
    }
	
    if (-not $sessionId) { throw "Não foi possível obter o SessionID." }

    # Decodificando o valor do sessionId
    $sessionId = [System.Web.HttpUtility]::UrlDecode($sessionId)

    return $sessionId
}

Function Get-ApiData ($url) {
    $sessionId = Get-NewSessionId

    $headers = @{
        'Cookie' = "SessionID=$sessionId"
    }

    $request = New-Object System.Net.Http.HttpRequestMessage
    $request.RequestUri = $url
    $request.Headers.Clear()
    foreach($header in $headers.GetEnumerator()){
        $request.Headers.Add($header.Key, $header.Value)
    }

    $response = $httpClient.SendAsync($request).Result
    $responseContent = $response.Content.ReadAsStringAsync().Result

<#     Write-Host "Response StatusCode: $($response.StatusCode)"   # <----- Linha adicionada para imprimir o StatusCode da resposta
    Write-Host "Response Content: $responseContent"   # <----- Linha adicionada para imprimir o conteúdo da resposta #>

    if ($response.StatusCode -ne 200) {
        throw "Ocorreu um erro HTTP: $($response.StatusCode)"
    }
    
    return [xml]$responseContent
}

function Humanize-BytesRate {
    param(
        [double]$ByteRate
    )

    $BitRate = $ByteRate * 8

    $byteUnits = "B/s", "KB/s", "MB/s", "GB/s"
    $bitUnits = "bps", "Kbps", "Mbps", "Gbps"

    $byteUnit = $bitUnit = 0

    while ($ByteRate -gt 1024 -and $byteUnit -lt $byteUnits.Length - 1) {
        $ByteRate /= 1024
        $byteUnit++
    }

    while ($BitRate -gt 1024 -and $bitUnit -lt $bitUnits.Length - 1) {
        $BitRate /= 1024
        $bitUnit++
    }

    return "{0:F2} {1} ({2:F2} {3})" -f $ByteRate, $byteUnits[$byteUnit], $BitRate, $bitUnits[$bitUnit]
}

function Humanize-Bytes {
    param(
        [double]$Size
    )

    $units = "B", "KB", "MB", "GB", "TB", "PB"
    $unit = 0

    while ($Size -gt 1024 -and $unit -lt $units.Length - 1) {
        $Size /= 1024
        $unit++
    }

    return "{0:F2} {1}" -f $Size, $units[$unit]
}

function Format-TrafficData {
    param(
        [Xml]$Data
    )

    $formattedData = @{}

    $keysToHumanize = 'CurrentUpload', 'CurrentDownload', 'TotalUpload', 'TotalDownload'
    $keysToHumanizeRate = 'CurrentUploadRate', 'CurrentDownloadRate'
    $keysToFormatTime = 'CurrentConnectTime', 'TotalConnectTime'

    foreach ($node in $Data.response.ChildNodes) {
        if ($node.Name -in $keysToHumanize) {
            $formattedData[$node.Name] = Humanize-Bytes -Size ([double]$node.'#text')
        }
        elseif ($node.Name -in $keysToHumanizeRate) {
            $formattedData[$node.Name] = Humanize-BytesRate -ByteRate ([double]$node.'#text')
        }
        elseif ($node.Name -in $keysToFormatTime) {
            $secs = [double]$node.'#text'
            $mins = [Math]::Floor($secs / 60)
            $secs %= 60
            $hours = [Math]::Floor($mins / 60)
            $mins %= 60
            $days = [Math]::Floor($hours / 24)
            $hours %= 24
            $formattedData[$node.Name] = "{0} dias, {1} horas, {2} minutos e {3} segundos" -f $days, $hours, $mins, $secs
        }
        else {
            $formattedData[$node.Name] = $node.'#text'
        }
    }

    return $formattedData
}

# Informações de URL
$url1 = "http://192.168.8.1/api/monitoring/status"
$url2 = "http://192.168.8.1/api/monitoring/traffic-statistics"

# Limpa a tela
Clear-Host

# Continua a imprimir os dados da API a cada 1 segundo
while ($true) {
    # Dados da primeira API
    $data1 = Get-ApiData $url1
    # Dados da segunda API
    $data2 = Get-ApiData $url2
    $data2Formatted = Format-TrafficData -Data $data2

    $keysToPrint = 'ConnectionStatus', 'SignalIcon', 'WanIPAddress', 'PrimaryDns', 'SecondaryDns', 'CurrentWifiUser', 'SimStatus', 'WifiStatus'

    # Para simplificar, vamos imprimir somente os dados desejados
	foreach ($node in $data1.response.ChildNodes) {
		if ($node.Name -in $keysToPrint) {
			Write-Host ($node.Name + ": " + $node.'#text')
		}
	}
    
    Write-Host "`nDados da segunda API:"
    foreach ($key in $data2Formatted.Keys) {
        Write-Host "${key}: $($data2Formatted[$key])"
    }

    # Pausa por 1 segundo
    Start-Sleep -Seconds 1

    # Limpa a tela
    Clear-Host
}
