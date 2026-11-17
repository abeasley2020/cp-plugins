"""SCORM 1.2 packaging: one SCO per lesson, shared assets as one resource.

The package is a plain zip with imsmanifest.xml at the root. Each lesson page
finds the LMS API, sets incomplete on load and completed when the learner
reaches the end marker (assets/cp-lesson.js). No score is reported: lessons
carry ungraded practice only. Standard library only.
"""

import os
import zipfile
from xml.sax.saxutils import escape, quoteattr


def manifest(identifier, title, lessons, shared_files):
    """lessons: [(lesson_id, title, href)]; shared_files: relative paths."""
    items, resources = [], []
    for lid, ltitle, href in lessons:
        rid = "res-" + lid
        items.append(f'      <item identifier="item-{escape(lid)}" identifierref="{escape(rid)}" isvisible="true">\n'
                     f"        <title>{escape(ltitle)}</title>\n      </item>")
        resources.append(f'    <resource identifier="{escape(rid)}" type="webcontent" adlcp:scormtype="sco" href={quoteattr(href)}>\n'
                         f"      <file href={quoteattr(href)}/>\n"
                         f'      <dependency identifierref="shared"/>\n    </resource>')
    shared = "\n".join(f"      <file href={quoteattr(f)}/>" for f in sorted(shared_files))
    resources.append(f'    <resource identifier="shared" type="webcontent" adlcp:scormtype="asset">\n{shared}\n    </resource>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier={quoteattr(identifier)} version="1.0"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org-1">
    <organization identifier="org-1">
      <title>{escape(title)}</title>
{chr(10).join(items)}
    </organization>
  </organizations>
  <resources>
{chr(10).join(resources)}
  </resources>
</manifest>
"""


def build_zip(site_dir, zip_path, identifier, title, lessons):
    """Zip a rendered site folder as SCORM 1.2. Every file that is not a lesson
    page is listed as a shared asset."""
    lesson_hrefs = {href for _, _, href in lessons}
    shared = []
    for root, _, files in os.walk(site_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), site_dir).replace(os.sep, "/")
            if rel not in lesson_hrefs and rel != "imsmanifest.xml":
                shared.append(rel)
    xml = manifest(identifier, title, lessons, shared)
    os.makedirs(os.path.dirname(os.path.abspath(zip_path)), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("imsmanifest.xml", xml)
        for root, _, files in os.walk(site_dir):
            for f in sorted(files):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, site_dir).replace(os.sep, "/")
                if rel == "imsmanifest.xml":
                    continue
                z.write(full, rel)
    return zip_path
