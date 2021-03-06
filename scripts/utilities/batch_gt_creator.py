#!/usr/bin/python2.7
import argparse
import rospkg
import numpy as np
import cv2
from os import listdir

# Default Parameters
frameCheckInterval = 50;
multiUsers = False;
videosDir = '/videos/'
gtDir = '/gt/'

rospack = rospkg.RosPack()
packagePath = rospack.get_path('social_robot')

# Argument Parser
ap = argparse.ArgumentParser()
#ap.add_argument("-i","--image", required=True, help="Path to the image")
ap.add_argument("-s", "--frame-check-interval", required=False, help="Interval of frames to check for updates")
ap.add_argument("-m", "--multi-user", required=False, help="allow for multi-users")
args = vars(ap.parse_args())

videosDir = packagePath + '/validation/' + videosDir
gtDir = packagePath + '/validation/' + gtDir

if args['frame_check_interval'] is not None:
  frameCheckInterval = int(args['frame_check_interval'])

if args['multi_user'] is not None:
  multiUsers = True

videoList = listdir(videosDir)
videoList = [file.split('.')[0] for file in videoList]

gtList = listdir(gtDir)
gtList = [file.split('.')[0] for file in gtList]

fileList = [file for file in videoList if file not in gtList]

print fileList

# Global Variables
refPt = []
cropping = False

def click_and_crop(event, x, y, flags, param):
  global refPt, cropping

  # If the left mouse button is clicked, record the starting
  # (x,y) coordinates and indicate that cropping is being
  # performed

  if event == cv2.EVENT_LBUTTONDOWN:
    refPt = [(x,y)]
    cropping = True

  # check to see if the left mouse button was released
  elif event == cv2.EVENT_LBUTTONUP:
    # record the ending (x,y) coordinates and indicate that 
    # cropping operation is finished
    refPt.append((x,y))
    cropping = False

    # draw a rectangle around the region of interest
    cv2.rectangle(image, refPt[0], refPt[1], (0,255,0), 2)
    cv2.imshow("image", image)

# Sort points to the given format
def sortPoints(pts):
  [left,top] = np.amin(pts, axis=0)
  [right,bottom] = np.amax(pts, axis=0)

  return [(left,top),(right,bottom)]

# Get euclidean Distance
def euclideanDistance(pts):
  x_sq = (pts[0][0] - pts[1][0])**2
  y_sq = (pts[0][1] - pts[1][1])**2

  return np.sqrt(x_sq + y_sq)

# Print results to file
def printToFile(f,numOfUsers,framenum, names, pts):
  f.write(str(framenum))
  if numOfUsers == 0:
    f.write(',Environment,0,0,0,0\n')
    return
  for i in range(numOfUsers):
    f.write(','+names[i]+','+str(pts[i][0][0])+','+str(pts[i][0][1])+','+str(pts[i][1][0])+','+str(pts[i][1][1]))
  f.write('\n')

ctr = 0
for file in fileList:
  ctr += 1
  print '\nprogress: ', round(float(ctr) / float(len(fileList)),2)
  print ' ' + file

  numTargets = -1
  targetName = ''
  name = file.split('_')[0]

  if name == "Combined":
    continue
     
  if multiUsers:
    while numTargets == -1:
      try:
        numTargets = int(raw_input('How many people are in this file? '))
      except Exception as e:
        print "Invalid number of targets!"
  else:
    numTargets = 1

  f = open(gtDir + file + '.csv', 'w')

  f.write('VideoName,' + file + '\n')
  
  if multiUsers:
    f.write('NumberOfTargets,' + str(numTargets) + '\n\n')

  name = ''
  if numTargets < 2:
    name = file.split('_')[0]
    f.write('Name,' + name + '\n')
    f.write('Position,' + file.split('_')[1] + '\n')
    f.write('Orientation,' + file.split("_")[2] + '\n')
    if file.split('_')[3] != '':
      f.write('Distance,' + file.split("_")[3][0] + '.' + file.split("_")[3][1:] + '\n\n')
    else:
      f.write('\n')
    targetName = file.split('_')[0]

  random = False
  if name == "Mixed":
    random = True
    targetName = "person"

  if random == False:
    f.write('i')
    for i in range(numTargets):
      f.write(',name,left,top,right,bottom')
    f.write('\n')

  cap = cv2.VideoCapture(videosDir + file + '.avi')

  cv2.namedWindow('image')
  cv2.setMouseCallback('image', click_and_crop)
  framenum = 0

  previousFrameRef = [0]*numTargets
  currentFrameRef = []
  previousNames = []
  currentNames = []

  first_run = True
  frameCheckIntervalIndx = 0

  while cap.isOpened():
    ret, image = cap.read()
    if image is None:
      break

    if name == "Environment":
      printToFile(f,0,framenum,name,[0,0,0,0])
      framenum+=1
      continue

    if random:
      cv2.imshow('image',image)
      cv2.waitKey(100)

      numTargets = -1
      while numTargets == -1:
        try:
          numTargets = int(raw_input('How many people are in this file? '))
        except Exception as e:
          print "Invalid number of targets!"

      if numTargets > 1:
        multiUsers = True

      f.write('i')
      if numTargets == 0:
        f.write(',name,left,top,right,bottom')

      for i in range(numTargets):
        f.write(',name,left,top,right,bottom')
      f.write('\n')
      random = False

    clone = image.copy()

    refPt = []
    name = ''

    if not first_run:
      currentFrameRef = previousFrameRef

    if frameCheckIntervalIndx == frameCheckInterval:
      if currentFrameRef == previousFrameRef:
        while True:
          for i in range(len(currentFrameRef)):
            cv2.rectangle(image, currentFrameRef[i][0], currentFrameRef[i][1], (255,0,0), 2)
            cv2.putText(image, currentNames[i], (currentFrameRef[i][0][0],currentFrameRef[i][0][1]-10), 1, 1.2, (255,0,0))
          cv2.imshow("image", image)
          key = cv2.waitKey(1) & 0xFF

          if key == ord("c"):
            break
          
          elif key == ord("r"):
            currentFrameRef = []
            currentNames = []
            image = clone.copy()
            break

          elif key == ord("s"):
            currentFrameRef = []
            image = clone.copy()
            break

      frameCheckIntervalIndx = 0

    while len(currentFrameRef) < numTargets:
      #image = clone.copy()
      while True:
        # Keep looping until the 'q' key is pressed
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF

        # If the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
          image = clone.copy()

        # If the 'c' key is pressed, break from the loop
        elif key == ord('c'):
          break

      # If there are two reference points, then crop the region of interest
      # from the image, and display it
      if len(refPt) == 2:
        roi = []
        refPt = sortPoints(refPt)
        
        if euclideanDistance(refPt) < 10: 
          continue
        roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
        
        currentFrameRef.append(refPt)
        if len(currentNames) != numTargets:
          if multiUsers:
            #name = raw_input('Name: ')
            name = targetName + "_" + str(len(currentNames))
          else:
            name = targetName
          currentNames.append(name)

        cv2.putText(roi, name, (0,15), 1, 1.0, (0,255,0))
        cv2.imshow("ROI_" + str(len(currentFrameRef)),roi)
        cv2.waitKey(1)
        
    print framenum, currentFrameRef, currentNames
    printToFile (f, numTargets, framenum, currentNames, currentFrameRef)
    framenum+=1
    previousFrameRef = currentFrameRef
    previousNames = currentNames
    first_run = False
    frameCheckIntervalIndx += 1

  multiUsers = False

  cv2.destroyAllWindows()
  cv2.waitKey(1)
  f.close()
  cap.release()