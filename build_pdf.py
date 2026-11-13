# -*- coding: utf-8 -*-
"""把 点分治讲义.html 打印成 A4 PDF，并先检测每页是否溢出。"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "点分治讲义.html"
OUT = ROOT / "点分治讲义.pdf"
CHECK = ROOT / "_layout_check.html"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

CHECK_JS = """
<script>
window.addEventListener('load', function(){
  var out = [];
  document.querySelectorAll('.page').forEach(function(p, i){
    var pr = p.getBoundingClientRect(), maxBottom = 0, culprit = '';
    p.querySelectorAll('*').forEach(function(el){
      if (el.classList.contains('ft') || el.closest('.ft')) return;
      var r = el.getBoundingClientRect();
      var b = r.bottom - pr.top;
      if (b > maxBottom) { maxBottom = b; culprit = el.tagName + '.' + el.className; }
    });
    out.push('P' + (i+1) + '=' + Math.round(maxBottom) + 'px' +
             (maxBottom > 1050 ? ' OVERFLOW<' + culprit + '>' : ''));
  });
  document.body.setAttribute('data-check', out.join(' | '));
});
</script>
</body>"""


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)


def main():
    html = SRC.read_text(encoding="utf-8")
    CHECK.write_text(html.replace("</body>", CHECK_JS), encoding="utf-8")

    base = [str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
            "--disable-dev-shm-usage", "--allow-file-access-from-files"]
    dom = run(base + ["--virtual-time-budget=4000", "--dump-dom", CHECK.as_uri()])
    m = re.search(r'data-check="([^"]*)"', dom.stdout)
    print("LAYOUT:", m.group(1) if m else "(未读到检测结果)")
    if not m:
        print("STDERR:", dom.stderr[-800:])
    CHECK.unlink(missing_ok=True)

    pdf = run(base + ["--virtual-time-budget=6000", "--no-pdf-header-footer",
                      "--print-to-pdf=" + str(OUT), SRC.as_uri()])
    if pdf.returncode != 0:
        print("CHROME ERROR:", pdf.stderr[-1000:])
        sys.exit(1)

    data = OUT.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    boxes = re.findall(rb"/MediaBox\s*\[([^\]]+)\]", data)
    print("PDF:", OUT.name, "size=%.1f KB" % (len(data) / 1024),
          "pages=", pages, "mediabox=", boxes[0].decode() if boxes else "?")


if __name__ == "__main__":
    main()
