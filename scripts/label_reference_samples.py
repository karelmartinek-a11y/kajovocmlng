"""Ensure original presentation sources explicitly identify their sample data."""
from ssot_sources import ROOT


if __name__=='__main__':
    changed=0
    banner='<div id="reference-demo-banner" role="note" style="padding:10px 16px;background:#fff2cc;color:#634b00;font:13px Segoe UI,sans-serif">UKÁZKOVÁ DATA / SAMPLE DATA · návrh rozhraní bez spojení s provozním backendem / interface design without a live backend</div>'
    for directory in ['pages','dialogs']:
        for path in (ROOT/'03_UI_REFERENCE'/directory).glob('*.html'):
            source=path.read_text(encoding='utf-8')
            if 'data-demo="true"' in source or 'id="reference-demo-banner"' in source:
                continue
            if '<body>' not in source:
                raise ValueError('Unknown reference body framing: '+str(path))
            path.write_text(source.replace('<body>','<body>'+banner,1),encoding='utf-8',newline='\n');changed+=1
    print('Labelled sample reference sources:',changed)
