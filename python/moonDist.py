#! /usr/bin/env python

#script that takes an optional argument for the date and target collection and calculates angular separation and elevation of each target from the moon. 

import ephem, subprocess, operator, argparse


#host & port info 
hostName="veritase.sao.arizona.edu"
portNum=""
#hostName="lucifer1.spa.umn.edu"
#portNum=33060

#dict for sorting/writing info
moonlightsources = {}
#setting up ephem observer object for veritas
veritas = ephem.Observer()
veritas.lat = '31:40.51'
veritas.lon = '-110:57.132'
veritas.elevation = 1268

#argument parser
parser = argparse.ArgumentParser(description='Takes optional arguments to specify date and source collection. If no arguments are specified, will calculate angular distances from the Moon at the current time for all moonlight sources')

parser.add_argument('--date',default=veritas.date, help='specify DATE (in UT) in the format "YYYY/MM/DD HH:MM"   don\'t forget the quotation marks')

parser.add_argument('--targets',default='moonlight_targets',help='specifies collection of targets. Allowed values for TARGETS: moonlight_targets, moonlight_bright, primary_targets, secondary_targets, blazar_filler_targets')
args = parser.parse_args()

#setting date/time to user-spefied value (or default to current date/time)
veritas.date = args.date
#letting user know the date and target collection used.
print
print "Date and time used (in UT): %s" %veritas.date
print "Calculating angular distances from the Moon for targets in %s collection..." %args.targets

#MySQL command, runs on command line through subprocess
execCMD = "select tblObserving_Collection.source_id,ra,decl,epoch from tblObserving_Sources join tblObserving_Collection ON tblObserving_Sources.source_id = tblObserving_Collection.source_id  where tblObserving_Collection.collection_id='%s'" %args.targets

sqlOut = subprocess.Popen(["mysql","-h","%s" %(hostName),"-P","%s" %(portNum),"-u", "readonly", "-D","VERITAS", "--execute=%s" %(execCMD)], stdout=subprocess.PIPE)

#stores query results
QUERY, err = sqlOut.communicate()
if QUERY == "":
  print
  print "Query result is empty. Make sure date and target collection provided are valid. Going to crash now :("

print
print "Source\t\t\tDegrees from Moon\tElevation"
print "--------------------------------------------------------------"
#loop through all objects in the bright moonlight list
#calculating and printing out angular separation from moon
for count,source in enumerate(QUERY.rstrip().split("\n")):
  #skip header in query results
  if count == 0:
    continue
  #parsing through query results
  sourceName=source.split("\t")[0]
  sourceRA=source.split("\t")[1]
  sourceDEC=source.split("\t")[2]
  sourceEpoch=source.split("\t")[3]

  #makes sure same epoch is used
  veritas.epoch = float(sourceEpoch)

  #Define ephem moon object and calculate position (ra, dec) and phase
  TheMoon = ephem.Moon(veritas)
  TheMoon.compute(veritas)
  illum = TheMoon.moon_phase*100.
  #Get angular separation of moon and target
  degFromMoon = 180./ephem.pi * ephem.separation((TheMoon.ra,TheMoon.dec),(float(sourceRA),float(sourceDEC)))

  #Define ehpem object for source, to get elevation
  sourceobj = ephem.FixedBody()
  sourceobj._ra = float(sourceRA)
  sourceobj._dec = float(sourceDEC)
  sourceobj.compute(veritas)
  
  sourceALT = sourceobj.alt*180./ephem.pi
  moonlightsources[sourceName]=[(degFromMoon,sourceALT)]

#end of for loop

sorted_sources = sorted(moonlightsources.iteritems(), key=operator.itemgetter(1), reverse=True)

#print sorted_sources

for s in sorted_sources:
  if s[1][0][1] > 20 and s[1][0][0] > 10:
    if len(s[0]) <=7:
      print "%s\t\t\t%0.3f\t\t\t%0.3f" %(s[0],s[1][0][0],s[1][0][1]) 
    elif len(s[0]) <=15: 
      print "%s\t\t%0.3f\t\t\t%0.3f" %(s[0],s[1][0][0],s[1][0][1]) 
    else:
      print "%s\t%0.3f\t\t\t%0.3f" %(s[0],s[1][0][0],s[1][0][1]) 

print "--------------------------------------------------------------"
print "The Moon is %0.2f%% illuminated" % illum
