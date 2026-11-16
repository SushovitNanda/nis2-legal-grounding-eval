# Open the report in Word, print the page each section starts on, and export a PDF next to it.
#
#   powershell -ExecutionPolicy Bypass -File scripts\check_report.ps1
#
# The limit is 8 pages before "References". Needs Microsoft Word on this machine.
param(
    [string]$Docx = (Join-Path $PSScriptRoot "..\Report\NIS2-compliance-advice-report.docx"),
    [string]$Pdf = ""
)
$Docx = (Resolve-Path $Docx).Path
if (-not $Pdf) { $Pdf = [System.IO.Path]::ChangeExtension($Docx, ".pdf") }
$w = New-Object -ComObject Word.Application
$w.Visible = $false
try {
    $d = $w.Documents.Open($Docx, $false, $true)
    $d.Repaginate()
    "total pages: " + $d.ComputeStatistics(2)
    $refPage = 0
    foreach ($h in @("1. Introduction", "2. Related Work", "3. Methods", "4. Results", "5. Discussion and Limitations",
                     "6. Conclusion", "Code and Data", "Author Contributions", "References", "Appendix", "LLM Usage Statement")) {
        $r = $d.Content; $f = $r.Find; $f.ClearFormatting(); $f.MatchCase = $true
        $found = $false
        while ($f.Execute($h)) { if ($r.Paragraphs(1).Range.Text.Trim() -eq $h) { $found = $true; break } }
        if ($found) {
            "{0,-32} page {1}" -f $h, $r.Information(3)
            if ($h -eq "References") { $refPage = $r.Information(3) }
        } else { "{0,-32} not found" -f $h }
    }
    $end = $d.Content; $f = $end.Find
    if ($f.Execute("reviewed the report.")) {
        $p = $end.Information(3)
        "main text ends on page $p, line " + $end.Information(10)
        if ($p -le 8) { "OK: the main text fits in 8 pages." } else { "!! OVER: the main text runs to page $p. Shorten scripts\report_text.py and build again." }
    }
    $d.ExportAsFixedFormat($Pdf, 17)
    "PDF written: $Pdf"
    $d.Close($false)
} finally { $w.Quit() }
