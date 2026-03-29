$ErrorActionPreference = 'Stop'

$packageName    = 'inspecta-agent'
$toolsDir       = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url64          = 'https://github.com/mufthakherul/device-inspector/releases/download/v0.1.0/inspecta-0.1.0-windows.zip'
$checksum64     = 'REPLACE_WITH_SHA256'
$extractDir     = Join-Path $toolsDir 'inspecta-0.1.0-windows'

$packageArgs = @{
  packageName    = $packageName
  unzipLocation  = $toolsDir
  fileType       = 'zip'
  url64bit       = $url64
  checksum64     = $checksum64
  checksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

$exePath = Join-Path $extractDir 'inspecta.exe'
Install-BinFile -Name 'inspecta' -Path $exePath
