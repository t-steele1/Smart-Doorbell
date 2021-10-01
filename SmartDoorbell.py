import numpy as np
import cv2
import imutils
import time
import os
import smtplib
from smtplib import SMTP
from smtplib import SMTPException
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from twilio.rest import Client

def mask_image(img):
	mask = np.zeros((img.shape[0], img.shape[1]), dtype="uint8")
	pts = np.array([ [0,600], [450,530], [700,580], [700,720], [0,720] ])
	cv2.fillConvexPoly(mask, pts, 255)
	
	masked = cv2.bitwise_and(img, img, mask=mask)
	gray = imutils.resize(masked, width=200)
	gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray,(11,11), 0)
	
	return masked, gray

n = 0

while True:
	n = n + 1
	
	print("")
	print("----Times through loop since starting:", n ,"----" )
	print("")
	
	command = 'sudo raspistill -w 1280 -h 720 -t 1000 -tl 1000 -o test%0d.jpg'
	os.system(command)
	
	print("Captured 1st & 2nd image for analysis")
	
	test1 = cv2.imread("test0.jpg")
	test2 = cv2.imread("test1.jpg")
	masked1, gray1 = mask_image(test1)
	masked2, gray2 = mask_image(test2)
	
	pixel_threshold = 50
	detector_total = np.uint64(0)
	detector = np.zeros((gray2.shape[0], gray2.shape[1]), dtype ="uint8")
	
	for i in range(0, gray2.shape[0]):
		for j in range(0, gray2.shape[1]):
			if abs(int(gray2[i,j]) - int(gray1[i,j])) > pixel_threshold:
				detector[i,j] = 255
	
	detector_total = np.uint64(np.sum(detector))
	print("detector_total = ", detector_total)
	print(" ")
	
	if detector_total > 5000:
		print("Detection alert")
		
		timestr = time.strftime("doorbell-%Y%m%d-%H%M%S")
		
		command2 = 'sudo raspivid -t 15000 -w 1280 -h 720 -fps 30 -o ' + timestr + '.h264'
		os.system(command2)
		
		print("Finsihed recording...converting to mp4")
		
		command3 = 'sudo MP4Box -fps 30 -add ' + timestr + '.h264 ' + timestr + '.mp4'
		os.system(command3)
		
		print("Finished converting file...available for viewing")
		
		#Dropbox uploader
		fullDirectory = '/home/pi/SmartDoorbell/' + timestr + '.mp4'
		
		command4 = '/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload ' + fullDirectory + ' /'
		os.system(command4)
		
		#Send email
		smtpUser = 'THROWAWAY_EMAIL@gmail.com'
		smtpPass = 'PASSWORD'

		toAdd = 'YOUR_EMAIL@EMAIL_PROVIDER.com'
		fromAdd = smtpUser
		
		f_time = datetime.now().strftime('%a %d %b @ %H:%M')
		subject = 'Smart Doorbell recording from: ' + f_time
		
		msg = MIMEMultipart()
		msg['Subject'] = subject
		msg['From'] = fromAdd
		msg['To'] = toAdd
		msg.preamble = "Detection alert @ " + f_time
		
		body = MIMEText('Detection alert @ ' + f_time)
		msg.attach(body)
		
		fp = open('test0.jpg', 'rb')
		img = MIMEImage(fp.read())
		fp.close()
		msg.attach(img)
		fp = open('test1.jpg', 'rb')
		img = MIMEImage(fp.read())
		fp.close()
		msg.attach(img)
		
		s = smtplib.SMTP('smtp.gmail.com', 587)
		s.ehlo()
		s.starttls()
		s.ehlo()
		s.login(smtpUser, smtpPass)
		s.sendmail(fromAdd, toAdd, msg.as_string())
		s.quit()
		
		print("Email delivered")
	else:
		print("No detections yet")
