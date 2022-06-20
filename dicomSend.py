import glob
import subprocess
import os
import signal
import sys
import time
import fileinput
import connector
import transliterate


server = '192.168.1.43 4242' # Сервер куда будем посылать
fileList = open("/root/python/files_to_copy", "r") # Файл со списком изображений

from datetime import datetime
now= datetime.now()

while True:
	lineFileList = fileList.readline()
	if not lineFileList:
		break
	filePath=lineFileList.strip()
	fileName=filePath.split('/')[-1]

	cursor = connector.cnx.cursor()
	select_query = (f"select * from DicomSend where FileName=%s")
	cursor.execute(select_query,[fileName])
	row = cursor.fetchone()

	if row == None:

		dcmToXml=subprocess.Popen("dcm2xml +M +Wb "+ filePath + " " + filePath + ".xml", shell=True)
		dcmToXml.communicate()
		fin = open(filePath + ".xml",encoding = "WINDOWS-1251")
		fout = open(filePath +".xml.mod", "wt")
		for line in fin:
			fout.write( line.replace('ISO-8859-5', 'UTF-8') )
		fin.close()
		fout.close()

		fullpathxml = filePath +'.xml.mod'

		import xml.etree.ElementTree as ET
		tree = ET.parse(fullpathxml)

		PatientName=tree.findall('data-set/element[@name="PatientName"]')[0].text
		if PatientName:
			PatientNameTrans=transliterate.transliterate(PatientName)
		else:
			PatientNameTrans="NameErr"

		tree.findall('data-set/element[@name="PatientName"]')[0].text = PatientNameTrans

		BodyPE=tree.findall('data-set/element[@name="BodyPartExamined"]')[0].text
		if BodyPE:
			BodyPETrans=transliterate.transliterate(BodyPE)
		else:
			BodyPETrans="BodyErr"

		tree.findall('data-set/element[@name="BodyPartExamined"]')[0].text = BodyPETrans

		try:
			ViewPos=tree.findall('data-set/element[@name="ViewPosition"]')[0].text
			ViewPosTrans=transliterate.transliterate(ViewPos)
		except:
			ViewPosTrans="ViewErr"

		tree.findall('data-set/element[@name="ViewPosition"]')[0].text = ViewPosTrans

		tree.write(fullpathxml)

		xmlToDcm=subprocess.Popen("xml2dcm -f "+ fullpathxml + " "+ fullpathxml +".dcm", shell=True)
		xmlToDcm.communicate()

		dcmSend=subprocess.Popen("dcmsend -nuc +ma "+server+" "+fullpathxml+".dcm", shell=True, text=True, stderr=subprocess.PIPE)
		data=dcmSend.communicate()
		for line in data:
			if line:
				line = line.strip()
		line=line.split(':')[0]
		if line=='W':
			cursor = connector.cnx.cursor()
			insert_query=(f"INSERT INTO DicomSend (id, FileName, SendDate, PatientName) values(NULL, %s, NULL, %s)")
			cursor.execute(insert_query,[fileName, PatientNameTrans])
			connector.cnx.commit()
			fullpath='/'.join(fullpathxml.split('/')[:-1])
			for xmlpath in glob.iglob(os.path.join(fullpath, '*.xml')):
				os.remove(xmlpath)
			for modpath in glob.iglob(os.path.join(fullpath, '*.mod')):
				os.remove(modpath)
			for moddcmpath in glob.iglob(os.path.join(fullpath, '*.mod.dcm')):
				os.remove(moddcmpath)
			print('Sending completed = ',now)
		else:
			print('ERROR. ORTHANC NOT ANSWER = ',now)
#	else:
#		print('RECORD IS DUPLICATED = ', now)