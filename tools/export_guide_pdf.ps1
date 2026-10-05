$docx = "D:\fileless malware\Huong_dan_cai_dat_va_thuc_hien_lab_Fileless_Malware.docx"
$pdf = "D:\fileless malware\Huong_dan_cai_dat_va_thuc_hien_lab_Fileless_Malware_preview.pdf"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($docx)
$doc.ExportAsFixedFormat($pdf, 17)
$pages = $doc.ComputeStatistics(2)
$doc.Close($false)
$word.Quit()

[System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null

Write-Output "Exported $pdf"
Write-Output "Pages $pages"
