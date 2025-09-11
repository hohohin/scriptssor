@echo off
echo Creating PNG icons for Chrome extension...

:: Create a simple PowerShell script to generate icons
powershell -Command ^
    "$sizes = @(16, 32, 48, 128); "^
    "foreach ($size in $sizes) { "^
    "    $bitmap = New-Object System.Drawing.Bitmap($size, $size); "^
    "    $graphics = [System.Drawing.Graphics]::FromImage($bitmap); "^
    "    $graphics.SmoothingMode = 'AntiAlias'; "^
    "    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush("^
    "        (New-Object System.Drawing.Rectangle(0, 0, $size, $size)), "^
    "        [System.Drawing.Color]::FromArgb(59, 130, 246), "^
    "        [System.Drawing.Color]::FromArgb(139, 92, 246), "^
    "        45"^
    "    ); "^
    "    $graphics.FillRectangle($brush, 0, 0, $size, $size); "^
    "    $font = New-Object System.Drawing.Font('Arial', ($size * 0.6), [System.Drawing.FontStyle]::Bold); "^
    "    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White); "^
    "    $format = New-Object System.Drawing.StringFormat; "^
    "    $format.Alignment = [System.Drawing.StringAlignment]::Center; "^
    "    $format.LineAlignment = [System.Drawing.StringAlignment]::Center; "^
    "    $graphics.DrawString('S', $font, $textBrush, ($size/2), ($size/2), $format); "^
    "    $outputPath = 'browser-extension-store\icons\icon' + $size + '.png'; "^
    "    $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png); "^
    "    $bitmap.Dispose(); "^
    "    $graphics.Dispose(); "^
    "    Write-Host 'Created: ' $outputPath; "^
    "}"

echo PNG icons created successfully!
pause