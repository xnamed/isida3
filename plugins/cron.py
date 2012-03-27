#!/usr/bin/python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------- #
#                                                                             #
#    Plugin for iSida Jabber Bot                                              #
#    Copyright (C) 2012 diSabler <dsy@dsy.name>                               #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #
# --------------------------------------------------------------------------- #

# cron * * * * * \n command

def time_cron(type, jid, nick, text):
	ar = text.split(' ',1)[0].lower()
	try: par = text.split(' ',1)[1]
	except: par = ''
	if ar == 'show': msg = time_cron_show(jid,nick,par)
	elif ar == 'del': msg = time_cron_del(jid,nick,par)
	else: msg = time_cron_add(text,jid,nick)
	send_msg(type, jid, nick, msg)

def time_cron_show(jid,nick,ar):
	al = get_level(jid,nick)[0]
	if ar:
		if al == 9 and ar.lower().split()[0] in ['all','global','total']: room = '%'
		else: room = jid
	else: room = jid	
	c = cur_execute_fetchall('select * from cron where room ilike %s order by room, time',(room,))
	if c:
		tmp, idx = [], 1
		for t in c:
			if room=='%': msg = '%s|%s' % (t[0],disp_time(t[3]))
			else: msg = '%s. %s' % (idx,disp_time(t[3]))
			if t[4]: msg += ' [%s]' % t[4]
			msg += ' -> %s' % t[5]
			tmp.append(msg)
			idx += 1
		return L('Cron rules:\n%s') % '\n'.join(tmp)
	else: return L('There is no cron rules.')

def time_cron_add(ar,jid,nick):
	try: cron_time, cron_cmd = ar.split('\n',1)
	except: return L('Not enough parameters!')
	try:
		if cron_time[0] == '-': cron_time,repeat_time = cron_time[1:],''
		else: repeat_time = cron_time
		next_time = crontab.CronTab(cron_time).next() + time.time()
	except: return L('Error in time format!')
	lvl,rj = get_level(jid,nick)
	amm,tcmd = -1,cron_cmd.split(' ')[0]
	for tmp in comms:
		if tmp[1] == tcmd:
			amm = tmp[0]
			break
	if amm < 0: return L('Command not found: %s') % tcmd
	elif amm > lvl: return L('Not allowed launch: %s') % tcmd
	else:
		cur_execute('insert into cron values (%s,%s,%s,%s,%s,%s,%s)', (jid,getRoom(rj),nick,next_time,repeat_time,cron_cmd,lvl))
		return '%s -> %s' % (disp_time(next_time),cron_cmd)
	
def time_cron_del(jid,nick,ar):
	al = get_level(jid,nick)[0]
	if al == 9 and ar.lower() == 'all':
		cur_execute('delete from cron where room=%s',(jid,))
		return L('All cron rules removed!')
	elif not ar: return L('Need choise record number.')
	elif not ar.isdigit(): return L('Record ID is numeric.')
	else:
		c = cur_execute_fetchall('select * from cron where room ilike %s order by room, time',(jid,))
		try: rec = c[int(ar)-1]
		except: return L('Record #%s not found!') % ar
		cur_execute('delete from cron where room=%s and jid=%s and nick=%s and time=%s and repeat=%s and command=%s and level=%s',rec)
		msg = disp_time(rec[3])
		if rec[4]: msg += ' [%s]' % rec[4]
		msg += ' -> %s' % rec[5]
		return L('Removed: %s') % msg

def cron_action():
	itt = int(time.time())
	c = cur_execute_fetchall('select * from cron where %s >= time',(itt,))
	if c:
		cur_execute('delete from cron where %s >= time',(itt,))
		for t in c:
			if t[4]:
				tm = crontab.CronTab(t[4]).next() + time.time()
				m = list(t[:3]) + [tm] + list(t[4:7])
				cur_execute('insert into cron values (%s,%s,%s,%s,%s,%s,%s)', m)
			tmppos = arr_semi_find(confbase, t[0])
			if tmppos == -1:
				pprint('Can\'t execute by cron: %s in %s' % (t[5].split()[0],t[0]))
				return
			else:
				nowname = getResourse(confbase[tmppos])
				if nowname == '': nowname = Settings['nickname']
			com_parser(t[6], nowname, 'groupchat', t[0], t[2], t[5], Settings['jid'])

global execute, timer

timer = [cron_action]

execute = [(7, 'cron', time_cron, 2, L('Execute command by cron. Used unix-type time format.\ncron * * * * *\ncommand'))]