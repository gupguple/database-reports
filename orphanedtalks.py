#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, MZMcBride

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wikipedia
import MySQLdb
import re
import datetime
import time

sleep_time = 0

report_template = u'''
Orphaned talk pages; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
|-
%s
|}
'''

site = wikipedia.getSite()

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* orphanedtalks.py SLOW_OK */
SELECT
  p1.page_namespace,
  ns_name,
  p1.page_title
FROM page AS p1
JOIN toolserver.namespace
ON p1.page_namespace = ns_id
AND dbname = 'enwiki_p'
WHERE p1.page_title NOT LIKE "%/%"
AND CASE WHEN p1.page_namespace = 1
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 0
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 5
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 4
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 11
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 10
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 13
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 12
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 15
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 14
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 17
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 16
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 101
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 100
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace IN (0,2,3,4,6,7,8,9,10,12,14,16,18,100,102,104)
  THEN 1 != 1
  ELSE 1 END;
''')

i = 1
output = []
for row in cursor.fetchall():
    talkpage = wikipedia.Page(site, '%s:%s' % (row[1], unicode(row[2], 'utf-8')))
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'%s' % unicode(row[2], 'utf-8')
    if page_namespace == 6 or page_namespace == 14:
        page_title = '[[:%s:%s]]' % (ns_name, page_title)
    elif ns_name:
        page_title = '[[%s:%s]]' % (ns_name, page_title)
    else:
        page_title = '[[%s]]' % (page_title)
    
    if re.search(r'\\', row[2], re.I|re.U) or re.search(r'(archive|^Image:|^Image_talk:|^File:|^File_talk:|^Category:|^User:|^User_talk:|^Template:)', row[2], re.I|re.U):
        pass

    elif talkpage.exists() and "G8-exempt" not in talkpage.templates() and "Go away" not in talkpage.templates():
        lastedit = datetime.datetime.strptime(talkpage.editTime(), '%Y%m%d%H%M%S')
        if datetime.datetime.utcnow() - lastedit > datetime.timedelta(days=7):
            try:
                talkpage.delete('[[WP:CSD#G8|CSD G8]]', False, False)
                time.sleep(sleep_time)
                continue
            except wikipedia.BadTitle:
                print 'Skipped [[en:%s]]: had unknown issues' % talkpage.title()
                continue
    table_row = u'''| %d
| %s
|-''' % (i, page_title)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikipedia.Page(site, 'Wikipedia:Database reports/Orphaned talk pages')
report.put(report_template % (current_of, '\n'.join(output)), 'updated page', True, False)
cursor.close()
conn.close()

wikipedia.stopme()